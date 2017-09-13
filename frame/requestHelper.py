# -*- coding:utf-8 -*-
import requests
import json
from frame.logHelper import LogHelper

headers = {'content-type': 'application/x-www-form-urlencoded;charset=UTF-8'}
timeout = 30

logger = LogHelper().logger


class RequestHelper(object):
    @classmethod
    def do_get(cls, url, is_https=True):
        try:
            r = requests.get(url=url, headers=headers, timeout=timeout, verify=is_https)
            # if r.status_code != requests.codes.ok:
            #     r.raise_for_status()
        except Exception, ex:
            logger.error('do get error!')
            return []
        return json.loads(r.content)

    @classmethod
    def do_post(cls, url, data, is_https=True):
        try:
            r = requests.post(url=url, data=data, headers=headers, timeout=timeout, verify=is_https)
            if r.status_code != '200':
                return []
        except Exception, ex:
            logger.error('do post error!')
            return []
        return json.loads(r.content)

    @classmethod
    def do_delete(cls, url, data, is_https=True):
        try:
            r = requests.delete(url=url, data=data, headers=headers, timeout=timeout, verify=is_https)
        except Exception, ex:
            logger.error('do delete error!')
            return []
        return json.loads(r.content)

    @classmethod
    def do_post_json(cls, url, data, header, is_https=True):
        try:
            r = requests.post(url=url, json=data, headers=header, timeout=timeout, verify=is_https)
        except Exception, ex:
            logger.error('do post_json error!')
            return []
        # print "response content : " + r.content
        return json.loads(r.content)
