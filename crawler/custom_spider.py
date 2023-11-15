# spiders/custom_spider.py
import scrapy

class CustomSpider(scrapy.Spider):
    name = 'custom_spider'

    def __init__(self, start_url, path, **kwargs):
        self.start_urls = [start_url]
        self.path = path
        super().__init__(**kwargs)

    def parse(self, response):
        # Get the current depth (default to 0 if not set)
        current_depth = response.meta.get('depth', 0)

        links = response.css('a::attr(href)').getall()
        filtered_links = [link for link in links if link.startswith(self.path)]
        yield {'url': response.url, 'links': filtered_links}

        # Follow links only if depth is less than 2
        if current_depth < 2:
            for link in filtered_links:
                yield response.follow(link, self.parse, meta={'depth': current_depth + 1})
