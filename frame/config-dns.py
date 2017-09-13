# -*- coding:utf-8 -*-

# -- app config --
APP_PORT = 60000
DEBUG = True

# 阿里云url，api秘钥
ALI_BASE_URL = "https://alidns.aliyuncs.com/"
ACCESS_KEY_ID = "LTAIyXNeN09WczI2"
ACCESS_KEY_SECRET = "QCUtIurIEuxtQzQp4rVOOyJjUaWu2l"

# smarteye 回调秘钥
SMARTEYE_CALLBACK_SECRET = 'vLE6GdisgCzxT8iUEEP6uwiwFfKrQy8f'

# -- sms setting --
SMS_KEY = "f878aa1798ff809dcba58dfbbbf0c7a7"
SMS_HOST = "https://www.anchnet.com"
SMS_URL = "/crm/api/smsSend.html"
SMS_TYPE = "SmartEye"

# 基础数据配置信息
DNS_DATA_LIST = {
    1: {
        'dns_name': 'anchnet.com.cn',
        'RR': 'www',
        'Type': 'A',
        'TTL': 1,
        'mobiles': '15000016416;15692109791',
        'master_group': [
            {'record_name': '119.23.117.122', 'server_name': '119.23.117.122'}
        ],
        'backup_group': [
            {'record_name': '101.132.89.197', 'server_name': '101.132.89.197'},
            {'record_name': '43.254.148.142', 'server_name': '43.254.148.142'}
        ]
    }
}
