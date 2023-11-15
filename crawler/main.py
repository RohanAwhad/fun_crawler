# main.py
from fastapi import FastAPI
import subprocess
import json

app = FastAPI()

@app.get("/crawl")
async def crawl(url: str, path: str):
    # Call the Scrapy spider using subprocess
    process = subprocess.Popen(
        ['python3', '-m', 'scrapy', 'runspider', 'custom_spider.py', '-a', f'start_url={url}', '-a', f'path={path}', '-O', 'output.json'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        if stderr: return {"error": stderr.decode()}
        else: return {"error": stdout.decode()}

    # Read the results from the file
    try:
        with open('output.json') as f: data = json.load(f)
        return data
    except Exception as e:
        with open('output.json') as f: data = f.read()
        return {"data": data, "error": str(e)}
