import hashlib
import json
import os
import redis
import subprocess
import urllib.parse as urlparse

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Union

app = FastAPI()

# get cwd
spider_dir = os.getcwd()
if not spider_dir.endswith("crawler"):
    spider_dir = os.path.join(spider_dir, "crawler")
SPIDER_FILE = os.path.join(spider_dir, "custom_spider.py")
if not os.path.exists(SPIDER_FILE):
    raise Exception("Spider file not found")


# Initialize Redis client
redis_client = None
try:
    url = os.getenv("REDISCLOUD_URL", None)
    if url is not None:
        url = urlparse.urlparse(url)
        redis_client = redis.Redis(
            host=url.hostname, port=url.port, password=url.password
        )
    else:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=os.getenv("REDIS_PORT", 6379),
            db=int(os.getenv("REDIS_DB", 0)),
        )
except Exception as e:
    print("Error connecting to Redis")
    print(e)


class CrawlInput(BaseModel):
    url: str
    path: str
    max_depth: int = 1


class CrawlOutput(BaseModel):
    data: Union[List[Optional[str]], str]
    error: Optional[str] = None


@app.post("/crawl", response_model=CrawlOutput)
async def crawl(inp: CrawlInput):
    url, path, max_depth = inp.url, inp.path, inp.max_depth
    # Create a unique key based on URL and path
    unique_key = hashlib.sha256(f"{url}{path}{max_depth}".encode()).hexdigest()

    try:
        # Check if the data is in cache
        if redis_client is not None:
            if (cached_data := redis_client.get(unique_key)) is not None:
                return {"data": json.loads(cached_data)}
    except Exception as e:
        print("Error fetching data from cache")
        print(e)

    # Call the Scrapy spider using subprocess
    print("calling spider")
    process = subprocess.Popen(
        [
            "python3",
            "-m",
            "scrapy",
            "runspider",
            SPIDER_FILE,
            "-a",
            f"start_url={url}",
            "-a",
            f"path={path}",
            "-a",
            f"max_depth={max_depth}",
            "-O",
            "output.json",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        if stderr:
            err = stderr.decode()
        else:
            err = stdout.decode()
        raise HTTPException(status_code=500, detail=err)

    # Read the results from the file
    try:
        with open("output.json") as f:
            data = json.load(f)

        # transform the data
        all_links = set()
        for item in data:
            url = item["url"]
            links = item["links"]
            domain = "/".join(url.split("/")[:3])

            # Remove the query params from the link
            links = [link.split("?")[0] for link in links]
            links = [link for link in links if link]

            # form the absolute links
            for link in links:
                if link.startswith("/"):
                    final_link = domain + link
                    all_links.add(final_link)
                # check if link starts with alphabets
                elif link[0].isalpha():
                    final_link = url + "/" + link
                    all_links.add(final_link)

        if len(all_links) == 0:
            return HTTPException(status_code=500, detail="No links found")

        # Cache the data
        try:
            if redis_client is not None:
                redis_client.set(unique_key, json.dumps(all_links))
        except Exception as e:
            print("Error caching data")
            print(e)

        return {"data": list(all_links), "error": None}
    except Exception as e:
        with open("output.json") as f:
            data = f.read()
        return {"data": data, "error": str(e)}
