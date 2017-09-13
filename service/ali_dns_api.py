# -*- coding:utf-8 -*-
import base64
import hashlib
import hmac
import time
import urllib
import uuid

from flask import json

from frame.requestHelper import RequestHelper
from frame.logHelper import LogHelper
from frame.config import ALI_BASE_URL, ACCESS_KEY_ID, ACCESS_KEY_SECRET

logger = LogHelper().logger


def do_ali_api(action, params):
    url = ALI_BASE_URL
    params['Action'] = action
    params['Timestamp'] = get_utc_now()
    params['Format'] = 'json'
    params['Version'] = '2015-01-09'
    params['AccessKeyId'] = ACCESS_KEY_ID
    params['SignatureMethod'] = 'HMAC-SHA1'
    params['SignatureVersion'] = '1.0'
    params['SignatureNonce'] = str(uuid.uuid1())

    params = sorted(params.items(), key=lambda d: d[0])
    print json.dumps(params)

    str_collect = '&'
    url += '?'
    for param in params:
        str_collect += '&' + urllib.quote(str(param[0])) + '=' + urllib.quote(str(param[1]))
        url += '&' + str(param[0]) + '=' + str(param[1])
        str_collect = str_collect.replace('&&', '')
        url = url.replace('?&', '?')

    str_collect = 'GET&%2F&' + urllib.quote(str_collect)
    signStr = base64.b64encode(hmac.new(ACCESS_KEY_SECRET + '&', str_collect, digestmod=hashlib.sha1).digest())
    Signature = urllib.quote(signStr)

    url += '&Signature=' + Signature
    r = RequestHelper.do_get(url)
    print json.dumps(r)
    return r


def get_utc_now():
    timestamp_now = time.time()
    timestamp_utc = timestamp_now - 8 * 60 * 60
    utc_time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime(timestamp_utc))
    return utc_time_str


def chang_dns_status_by_record_id(record_id, status):
    result = do_ali_api('SetDomainRecordStatus',
                        {'RecordId': record_id, 'Status': status})
    if 'RecordId' in result and 'Status' in result:
        if result.get('RecordId') == record_id and result.get('Status') == status:
            return True
    logger.warn('SetDomainRecordStatus failed , response : ' + json.dumps(result))
    return False


def delete_dns_by_record_id(record_id):
    result = do_ali_api('DeleteDomainRecord',
                        {'RecordId': record_id})
    if 'RecordId' in result:
        return True
    logger.warn('DeleteDomainRecord failed , response : ' + json.dumps(result))
    return False


def add_dns(domain_name, rr, record_ip, type, ttl):
    result = do_ali_api('AddDomainRecord',
                        {'DomainName': domain_name, 'RR': rr, 'Type': type, 'TTL': ttl, 'Value': record_ip})
    if 'RecordId' in result:
        return result['RecordId']
    logger.warn('AddDomainRecord failed , response : ' + json.dumps(result))
    return None


def get_domain_desc(domain_name, rr):
    result = do_ali_api('DescribeDomainRecords',
                        {'DomainName': domain_name, 'RRKeyWord': rr})
    if 'DomainRecords' in result and "Record" in result.get('DomainRecords'):
        domain_record_list = result.get('DomainRecords').get('Record')
        result_dict = {}
        for each_item in domain_record_list:
            if each_item.get('RR') == rr:
                result_dict[each_item.get('Value')] = each_item.get('RecordId')
        return result_dict
    logger.warn('DescribeDomainRecords failed , response : ' + json.dumps(result))
    return None
