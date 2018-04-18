#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import time
from plurk_oauth import PlurkAPI

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('plurk_api')


class Plurk(object):
    _max_len = 360
    _post_period = 10

    def __init__(self, api_keys_path, max_retry=5):
        self.max_retry = max_retry
        self.plurk = PlurkAPI.fromfile(api_keys_path)

    def __del__(self):
        del self.plurk

    def _retry(func):
        # MAX_RETRY = 5
        def wrap_request(self, *args, **kwargs):
            retry_count = self.max_retry
            while retry_count:
                r = func(self, *args, **kwargs)
                if r is not None:
                    return r
                retry_count -= 1
                time.sleep(self._post_period)

            err = self.plurk.error()
            err_msg = '[ERR][{0}][{1} {2}] {3}'.format(
                func.__name__, err['reason'],
                err['code'], err['content'])
            logger.debug(err_msg)
            return err_msg
            # raise Exception(err_msg)
        return wrap_request

    def check_status(self):
        self.plurk.callAPI('/APP/Users/me')
        err = self.plurk.error()
        err_msg = '[ERR][{0}][{1} {2}] {3}'.format(
            'check_status', err['reason'],
            err['code'], err['content'])
        if err['code'] == 503:
            logger.debug(err_msg)
            return False
        return True

    @_retry
    def get_clique_ids(self, clique_name):
        logger.debug('get clique: {0}'.format(clique_name))
        # add self uid
        ids = [3344763]
        clique_data = self.plurk.callAPI('/APP/Cliques/getClique',
                                         {'clique_name': clique_name})
        for user_data in clique_data:
            ids.append(user_data['id'])
        return ids

    @_retry
    def post_new(self, content, limited_to=None, options=None):
        if limited_to is None:
            limited_to = []
        if options is None:
        	options = {}

        if not content:
            return {}

        qualifier = 'says'
        plurk_data = {'content': content,
                      'qualifier': qualifier}
        plurk_data.update(options)
        if limited_to:
            plurk_data['limited_to'] = str(limited_to)

        return self.plurk.callAPI('/APP/Timeline/plurkAdd', plurk_data)

    @_retry
    def post_resp(self, plurk_id, content):
        if not content:
            return {}

        qualifier = 'says'
        plurk_data = {'plurk_id': plurk_id,
                      'content': content,
                      'qualifier': qualifier}

        return self.plurk.callAPI('/APP/Responses/responseAdd', plurk_data)

    def _get_one_post(self, items=None):
    	for content in items:
    		yield content
    	"""
        if items is None:
            yield ''
        post_content = ''
        post_len = 0
        for i, item in enumerate(items, 1):
            content = item
            content_len = len(content)
            if content_len > self._max_len:
                logger.warning('content %d length %d > max_len %d',
                               i, content_len, self._max_len)
                content = content[:self._max_len]
                content_len = len(content)

            if (post_len + content_len + 1) > self._max_len:
                # logger.debug('%d %s', i, post_content)
                yield post_content
                post_content = content
                post_len = content_len
            else:
                if post_content:
                    post_content = '{}\n{}'.format(post_content, content)
                else:
                    post_content = content
                post_len = len(post_content)
        if post_content:
            # logger.debug('end %d %s', i, post_content)
            yield post_content
        """

    def post_item(self, items, limited_to=None, options=None):
        """post_item
        Args:
            items: string contents list
            limited_to: the user or group id of plurk
        """
        if limited_to is None:
            limited_to = []
        if options is None:
        	options = {}
        post_content = ''
        post_len = 0
        plurk_id = -1
        is_first_post = True

        for post_content in self._get_one_post(items):
            if is_first_post:
                # logger.debug(post_content)
                # logger.debug(limited_to)
                r = self.post_new(post_content, limited_to, options)
                plurk_id = int(r['plurk_id'])
                is_first_post = False
            else:
                # logger.debug(post_content)
                r = self.post_resp(plurk_id, post_content)
                pass
            logger.debug('## Post length: {} ##'.format(len(post_content)))
        return plurk_id


if __name__ == '__main__':
    api_keys_path = '/home/kaisuto/pixiv_plurk_bot/plurk_api.keys'

    plurk = Plurk(api_keys_path)
    status = plurk.check_status()
    if status:
        ids = plurk.get_clique_ids('gentle')
        print(ids)
        limited_to = [3344763]    # add self

        plurk.post_new('test post content', limited_to, {'porn': 1})
        exit()

        s = '[R-18][Pixiv TOP][Rank 1][笹岡ぐんぐ/メロン様委託中！] 委託販売開始しました！（新刊）' \
            'http://www.pixiv.net/member_illust.php?mode=medium&' \
            'illust_id=52271653&ref=rn-b-1-title-3&uarea=male_r18 ' \
            'http://i.imgur.com/vCehEQs.jpg'
        print(len(s))
        items = [s] * 3
        items.append('143243222243333324')
        plurk.post_item(items, limited_to)
    del plurk
