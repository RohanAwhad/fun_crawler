# spiders/custom_spider.py
import scrapy

class CustomSpider(scrapy.Spider):
    name = 'custom_spider'

    def __init__(self, start_url, **kwargs):
        self.start_urls = [start_url]
        super().__init__(**kwargs)

    def parse(self, response):
        links = response.css('a::attr(href)').getall()
        yield {'url': response.url, 'links': links}
