# spiders/custom_spider.py
import scrapy

class CustomSpider(scrapy.Spider):
    name = 'custom_spider'

    def __init__(self, start_url, path, **kwargs):
        self.start_urls = [start_url]
        self.path = path
        super().__init__(**kwargs)

    def parse(self, response):
        # get response url
        curr_link = response.url
        filter_link = True
        if curr_link.endswith('/'):
            if (curr_link[:-1]).endswith(self.path):
                filter_link = False
        else:
            if curr_link.endswith(self.path):
                filter_link = False

        # Get the current depth (default to 0 if not set)
        current_depth = response.meta.get('depth', 0)

        links = response.css('a::attr(href)').getall()
        if filter_link:
            filtered_links = [link for link in links if link.startswith(self.path)]
        else:
            filtered_links = [link for link in links 
                              if not (link.startswith('/') or
                                      link.startswith('http') or
                                      link.startswith('https') or
                                      link.startswith('mailto') or
                                      link.startswith('tel') or
                                      link.startswith('javascript') or
                                      link.startswith('data') or
                                      link.startswith('ftp') or
                                      link.startswith('file') or
                                      link.startswith('#'))]
        yield {'url': response.url, 'links': filtered_links}

        # Follow links only if depth is less than 2
        if current_depth < 2:
            for link in filtered_links:
                yield response.follow(link, self.parse, meta={'depth': current_depth + 1})
