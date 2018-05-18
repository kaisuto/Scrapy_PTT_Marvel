# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


import pprint
import os.path
from scrapy.exceptions import DropItem
from ptt_marvel.plurk_api import Plurk


DIR_PATH, _ = os.path.split(__file__)


class ArticlePipeline(object):
    def open_spider(self, spider):
        # post to plurk
        plurk_key_path = os.path.join(DIR_PATH, 'plurk_api.keys')

        self.plurk = Plurk(plurk_key_path)
        self.plurk_post_items = []
        return
    
    def close_spider(self, spider):
        options = {
            'porn': 1,
            'replurkable': 0,
        }
        # limited_to = [3344763]
        status = self.plurk.check_status()
        if status and self.plurk_post_items:
            self.plurk_post_items.insert(0, '[Marvel]')
            self.plurk.post_item(self.plurk_post_items,
                                 options=options)
        del self.plurk
        return

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
            self.plurk_post_items.append(str(item))
            return item

        # Check scraped
        if spider.last_date >= item_date:
            raise DropItem("Scraped Article")

        if item['score'] < 0:
            raise DropItem("Low Score of Article")
        
        self.plurk_post_items.append(str(item))

        return item
