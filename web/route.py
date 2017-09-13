# -*- coding:utf-8 -*-
import threading
import urllib
import hmac
import hashlib

from flask import json

from web import app
from frame.logHelper import LogHelper
from flask import request
from service.dispatcher import Dispatcher
from frame.config import DNS_DATA_LIST, SMARTEYE_CALLBACK_SECRET

logger = LogHelper().logger

dispatcher_map = {}


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/callback/dns', methods=['POST'])
def dns_api_callback():
    # 接收callback消息
    logger.info("---- receiving DNS callback data ----")
    try:
        request_params = request.form.to_dict()
        logger.info("receive data : " + json.dumps(request_params))
        # 发起线程处理数据
        t = threading.Thread(target=receive_data, args=("dns", request_params,))
        t.start()
        logger.info("---- receive data finished ----")
    except:
        logger.error("dns_api_callback ERROR!")
    return "0"


@app.route('/callback/ddos', methods=['POST'])
def ddos_api_callback():
    # 接收callback消息
    logger.info("---- receiving DDOS callback data ----")
    try:
        request_params = request.form.to_dict()
        logger.info("receive data : " + json.dumps(request_params))
        # 发起线程处理数据
        t = threading.Thread(target=receive_data, args=("ddos", request_params,))
        t.start()
        logger.info("---- receive data finished ----")
    except:
        logger.error("dns_api_callback ERROR!")
    return "0"


def receive_data(receive_type, callback_data):
    logger.info("---- enter receive_data ----")
    # 验证回调数据是否合法
    if not check_data_validate(callback_data):
        print "验证数据不合法！"
        logger.error("check_data_validate fail!")
        return
    # 根据server_id查询所在的dns组
    server_id = ''
    try:
        server_id = json.loads(callback_data.get('event_data')).get('monitor_name')
    except:
        logger.error("get server_id error!")
        pass
    if len(server_id) == 0:
        logger.error("get server_id fail!")
        return
    dns_id, group_type, record_name = find_dns_id_by_server_id(server_id)
    logger.info("data found :" + str(dns_id) + "|" + group_type + "|" + record_name)
    # 发起调度器处理逻辑
    if dns_id is not None:
        # 每个dns组只初始化一个调度器
        if dns_id not in dispatcher_map:
            dispatcher = Dispatcher(dns_id, receive_type)
            dispatcher_map[dns_id] = dispatcher
        else:
            dispatcher = dispatcher_map[dns_id]
        if receive_type == "dns":
            logger.info("**** Start DNS handler ****")
            dispatcher.callback_dns_handler(callback_data, group_type, record_name)
        elif receive_type == "ddos":
            logger.info("**** Start DDOS handler ****")
            dispatcher.callback_ddos_handler(callback_data, group_type, record_name)
        else:
            logger.info("**** Undefined receive type , no handler matches up ****")


def check_data_validate(callback_data):
    try:
        sign = callback_data.pop('sign')
        print "sign : ", sign
        params = sorted(callback_data.items(), key=lambda d: d[0])
        sign_str = '&'
        for param in params:
            sign_str += '&' + urllib.quote(str(param[0])) + '=' + urllib.quote(str(param[1]))
        sign_str = sign_str.replace('&&', '')
        sign_str = sign_str.replace('/', '%2F')
        print "sign_str before encrypt : " + sign_str
        sign_str1 = hmac.new(SMARTEYE_CALLBACK_SECRET, sign_str, digestmod=hashlib.sha1).hexdigest()
        print "sign_str after encrypt : " + sign_str1
        if sign == sign_str1:
            return True
    except:
        pass
    return False


def find_dns_id_by_server_id(server_id):
    for dns_id, dns_items in DNS_DATA_LIST.items():
        master_group = dns_items.get('master_group')
        for each_item in master_group:
            if each_item.get('server_name') == server_id:
                return dns_id, 'master', each_item.get('record_name')
        backup_group = dns_items.get('backup_group')
        for each_item in backup_group:
            if each_item.get('server_name') == server_id:
                return dns_id, 'backup', each_item.get('record_name')
    return None
