# main.py
from fastapi import FastAPI
import subprocess
import json

app = FastAPI()

@app.get("/crawl")
async def crawl(url: str):
    # Call the Scrapy spider using subprocess
    process = subprocess.Popen(
        ['scrapy', 'crawl', 'custom_spider', '-a', f'start_url={url}', '-o', 'output.json'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        return {"error": stderr.decode()}

    # Read the results from the file
    with open('output.json') as f:
        data = json.load(f)

    return data
