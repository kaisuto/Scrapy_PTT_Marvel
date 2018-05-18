# -*- coding: utf-8 -*-

import pprint
import json
import logging
import os.path
import urllib
import arrow
import scrapy
from functools import wraps
from scrapy.http import Request
from ptt_marvel.items import Article


DIR_PATH, _ = os.path.split(__file__)
DIR_PATH, _ = os.path.split(DIR_PATH)
LOGGER = logging.getLogger("MarvelSpider")


class MarvelSpider(scrapy.Spider):
    name = 'marvel'
    allowed_domains = ['www.ptt.cc']
    start_urls = ['https://www.ptt.cc/bbs/marvel/index.html']
    data_path = os.path.join(DIR_PATH, 'marvel.dat')
    articles = []
    data = None
    now_date = None
    last_date = None
    period_days = 7

    def start_requests(self):
        # load last date from file

        self.now_date = arrow.now()
        with open(self.data_path, 'a+') as fp:
            try:
                fp.seek(0)
                self.data = json.load(fp)
                self.data['last_date'] = arrow.get(self.data['last_date'])
            except:
                LOGGER.warning("Load Last Date Failed.")
                last_date = self.now_date.shift(days=-self.period_days)
                self.data = {
                    'last_date': last_date
                }
            self.last_date = self.data['last_date']
        return [Request(url, dont_filter=True) for url in self.start_urls]
    
    def closed(self, reason):
        with open(self.data_path, 'w+') as fp:
                self.data['last_date'] = str(self.now_date)
                json.dump(self.data, fp)
        return

    def fileter_articles(self, articles):
        """Filter articles on page by date and score
        """
        now_date = arrow.now()
        year = now_date.year
        for article in articles:
            score = article.xpath('.//div[@class="nrec"]/span/text()')
            try:
                score = int(score)
            except ValueError:
                if score == "推":
                    score = 100
                elif score.startswith("X"):
                    score = -100
                else:
                    raise

            date = article.xpath('.//div[@class="date"]/text()')[0].extract()
            date = date[0].strip()
            date = arrow.get('{}/{}'.format(year, date), 'YYYY/M/D')
        return

    def get_preview_article(self, response, element):
        article = Article()
        url = element.xpath('.//div[@class="title"]/a/@href')[0].extract()
        article['url'] = response.urljoin(url)
        article['title'] = element.xpath('.//div[@class="title"]/a/text()')[0].extract()
        article['author'] = element.xpath('.//div[@class="author"]/text()')[0].extract()
        date_mmdd = element.xpath('.//div[@class="date"]/text()')[0].extract()
        article['date'] = arrow.get(date_mmdd, 'M/DD').replace(year=self.now_date.year)

        try:
            score = element.xpath('.//div[@class="nrec"]/span/text()')[0].extract()
            score = int(score)
        except IndexError:
            score = 0
        except ValueError:
            if score == "爆":
                score = 100
            elif score.startswith("X"):
                score = -100
            else:
                raise
        article['score'] = score
        return article

    def parse_retry(func, max_retry_times=3):
        parse_retry_times = {}

        @wraps(func)
        def retry_func(self, response):
            try:
                yield from func(self, response)
            except:
                retry_times = parse_retry_times.get(response.url, 0)
                if retry_times < max_retry_times:
                    LOGGER.debug("Retry <GET %s>", response.url)
                    parse_retry_times[response.url] = retry_times + 1
                    yield response.request.copy().replace(dont_filter=True)
                else:
                    raise
        return retry_func

    def parse(self, response):
        """Parsing Marvel board pages
        """
        # Check page type (Page or Article)
        url_path = urllib.parse.urlsplit(response.url).path
        _, last_section = os.path.split(url_path)
        if last_section.startswith("index"):
            yield from self.parse_page(response)
        else:
            yield from self.parse_article(response)
        return

    @parse_retry
    def parse_page(self, response):
        over_date = False
        # Article requests
        articles = response.xpath('//div[contains(@class, "r-list-container")]//div[@class="r-list-sep"]/preceding-sibling::div[@class="r-ent"]')
        if not articles:
            # "r-list-sep" only show on first page
            articles = response.css("div.r-list-container > .r-ent")

        for article in articles:
            # Skip deleted aritcles
            if "本文已被刪除" in article.extract():
                continue
            try:
                article = self.get_preview_article(response, article)
            except Exception as e:
                LOGGER.warning(article.extract())
                LOGGER.warning("Article parsing failed.[%s]", str(e))
            else:
                if article['date'] > self.last_date:
                    meta_data = {'article': article}
                    request = Request(article['url'],
                                      self.parse_article,
                                      meta=meta_data)
                    yield request
                else:
                    over_date = True

        if over_date:
            return

        # Pages requests
        next_page = response.xpath('//div[@id="action-bar-container"]//a[@class="btn wide"][contains(text(), "上頁")]/@href').extract()
        if next_page:
            url = response.urljoin(next_page[0])
            yield Request(url, self.parse)
        yield

    @parse_retry
    def parse_article(self, response):
        article = response.meta['article']
        date_str_xpath = ('//div[@class="article-metaline"]'
                          '//span[@class="article-meta-tag"][contains(text(), "時間")]'
                          '/following-sibling::span[@class="article-meta-value"]/text()')
        date_str = response.xpath(date_str_xpath)[0].extract()
        # date_string normalize
        date_str = ' '.join(date_str.split())
        article['date'] = arrow.get(date_str, 'ddd MMM D HH:mm:ss YYYY')
        article['content'] = response.xpath('//div[@id="main-content"]/text()')[0].extract()
        LOGGER.debug('detail parsing: %s', article['title'])
        yield article
