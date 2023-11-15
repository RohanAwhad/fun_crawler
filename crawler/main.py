# main.py
from fastapi import FastAPI, HTTPException
import subprocess
import json
import redis
import hashlib
import os

app = FastAPI()

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'), 
    port=os.getenv('REDIS_PORT', 6379), 
    db=int(os.getenv('REDIS_DB', 0))
)

@app.get("/crawl")
async def crawl(url: str, path: str):
    # Create a unique key based on URL and path
    unique_key = hashlib.sha256(f'{url}{path}'.encode()).hexdigest()

    # Check if the data is in cache
    if (cached_data := redis_client.get(unique_key)) is not None:
        return json.loads(cached_data)


    # Call the Scrapy spider using subprocess
    process = subprocess.Popen(
        ['python3', '-m', 'scrapy', 'runspider', 'custom_spider.py', '-a', f'start_url={url}', '-a', f'path={path}', '-O', 'output.json'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        if stderr: err = stderr.decode()
        else: err = stdout.decode()
        raise HTTPException(status_code=500, detail=err)


    # Read the results from the file
    try:
        with open('output.json') as f: data = json.load(f)
        redis_client.set(unique_key, json.dumps(data))
        return data
    except Exception as e:
        with open('output.json') as f: data = f.read()
        return {"data": data, "error": str(e)}
