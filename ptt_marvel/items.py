# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Article(scrapy.Item):
    """Article info show on independent article page
    """
    url = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    score = scrapy.Field()
    content = scrapy.Field()

    def __repr__(self):
        """only print out attr1 after exiting the Pipeline"""
        return repr({'title': self['title']})
    
    def __str__(self):
        return self['url']
