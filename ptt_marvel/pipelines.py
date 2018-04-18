# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from scrapy.exceptions import DropItem


class ArticlePipeline(object):
    def process_item(self, item, spider):
        black_keywords = [
            "創作",
            "找文",
            "公告",
        ]

        white_keywords = [
            "日本怪談",
        ]

        # Translate arrow object in item to string for json serialization.
        # And remain arrow object for date comparison.
        item_date = item['date']
        item['date'] = str(item['date'])

        # Check black keywords
        if any(keyword in item['title'] for keyword in black_keywords):
            raise DropItem("Article matchs black keywords")

        # Check white keywords
        if any(keyword in item['title'] for keyword in white_keywords):
            return item

        # Check scraped
        if spider.last_date >= item_date:
            raise DropItem("Scraped Article")

        if item['score'] < 10:
            raise DropItem("Low Score of Article")

        return item
