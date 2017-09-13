# -*- coding:utf-8 -*-
import httplib, urllib, json, sys

import requests

from frame.config import SMS_HOST, SMS_URL, SMS_KEY, SMS_TYPE
from frame.logHelper import LogHelper

logger = LogHelper().logger


def send(mobiles, content):
    mobile_list = mobiles.split(';')
    for each_mobile in mobile_list:
        send_short_message(each_mobile, content)


def send_short_message(mobile, content):
    reload(sys)
    sys.setdefaultencoding('utf-8')
    try:
        params = urllib.urlencode(
            {'key': SMS_KEY, 'mobile': mobile, 'sms_contect': content})
        headers = {"Content-type": "application/x-www-form-urlencoded"}

        logger.info("send sms data:" + json.dumps(
            {'key': SMS_KEY, 'mobile': mobile, 'sms_contect': content}))
        result = requests.post(SMS_HOST + SMS_URL, data=params, timeout=30, headers=headers)
        # r_json = json.loads(r.content)
        # httpClient = httplib.HTTPConnection(SMS_HOST, 80, timeout=30)
        # httpClient.request("POST", SMS_URL, params, headers)
        #
        # response = httpClient.getresponse()
        # result = response.read()
        resp = json.loads(result.content)
        # print response.status
        # print response.reason
        # print response.read()
        # print response.getheaders()  # 获取头信息
        if resp["status"] != 1:
            logger.error("短信发送失败，原因:" + urllib.unquote(resp["message"]))
        else:
            print "send sms success!"
    except Exception, ex:
        logger.exception("短信发送出错，错误信息:" + str(ex))
