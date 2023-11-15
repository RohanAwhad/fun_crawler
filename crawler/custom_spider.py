# spiders/custom_spider.py
import scrapy

class CustomSpider(scrapy.Spider):
    name = 'custom_spider'

    def __init__(self, start_url, path, **kwargs):
        self.start_urls = [start_url]
        self.path = path
        super().__init__(**kwargs)

    def parse(self, response):
        links = response.css('a::attr(href)').getall()
        filtered_links = [link for link in links if link.startswith(self.path)]
        yield {'url': response.url, 'links': filtered_links}
