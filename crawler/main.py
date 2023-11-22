import hashlib
import json
import os
import redis
import subprocess

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI()


# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=int(os.getenv("REDIS_DB", 0)),
)


class CrawlInput(BaseModel):
    url: str
    path: str
    max_depth: int = 1


# class CrawlOutput(BaseModel):
#     data: List[Dict[str, List[str]]]
#     error: str = None


@app.post("/crawl")  # , response_model=CrawlOutput)
async def crawl(inp: CrawlInput):
    url, path, max_depth = inp.url, inp.path, inp.max_depth
    # Create a unique key based on URL and path
    unique_key = hashlib.sha256(f"{url}{path}{max_depth}".encode()).hexdigest()

    # Check if the data is in cache
    if (cached_data := redis_client.get(unique_key)) is not None:
        return {"data": json.loads(cached_data)}

    # Call the Scrapy spider using subprocess
    process = subprocess.Popen(
        [
            "python3",
            "-m",
            "scrapy",
            "runspider",
            "custom_spider.py",
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
        redis_client.set(unique_key, json.dumps(data))
        return {"data": data}
    except Exception as e:
        with open("output.json") as f:
            data = f.read()
        return {"data": data, "error": str(e)}
