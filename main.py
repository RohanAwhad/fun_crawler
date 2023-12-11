import crawler.new_crawler

import hashlib
import json
import os
import redis
import urllib.parse as urlparse

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union

app = FastAPI()

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


class CrawlOutput(BaseModel):
    data: Union[List[Optional[str]], str]
    error: Optional[str] = None


@app.post("/crawl", response_model=CrawlOutput)
async def crawl(inp: CrawlInput):
    url = inp.url.strip()
    # Create a unique key based on URL and path
    unique_key = hashlib.sha256(url.encode()).hexdigest()

    try:
        # Check if the data is in cache
        if redis_client is not None:
            if (cached_data := redis_client.get(unique_key)) is not None:
                return {"data": json.loads(cached_data)}
    except Exception as e:
        print("Error fetching data from cache")
        print(e)


    # Read the results from the file
    try:
        all_links = await new_crawler.main(url)
        if len(all_links) == 0:
            return HTTPException(status_code=500, detail="No links found")
        # Cache the data
        try:
            if redis_client is not None:
                redis_client.set(unique_key, json.dumps(all_links))
        except Exception as e:
            print("Error caching data")
            print(e)

        return {"data": all_links, "error": None}
    except Exception as e:
        return {"data": [], "error": str(e)}
