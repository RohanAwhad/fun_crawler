# Fun Crawler

## Description

This is a crawler service for fun. It can crawl the web pages and extract the links based on the given url and path.
It can also follow the links and crawl the web pages recursively.

## How to run

### Using Docker
```
docker-compose up --build
```

### Using Python

**Note**: Redis client is required. If redis is not running on `http://localhost:6379`, then `REDIS_HOST` and `REDIS_PORT` environment variable should be set.
```
pip install -r crawler/requirements.txt
uvicorn crawler.main:app
```