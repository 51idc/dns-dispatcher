# -*- coding:utf-8 -*-
from flask import json
from frame.config import DNS_DATA_LIST
from service import ali_dns_api, sms_sender

logger = ali_dns_api.logger


class Dispatcher(object):
    def __init__(self, dns_id, receive_type):
        self.dns_id = dns_id
        data_list = DNS_DATA_LIST.get(dns_id)
        self.dns_name = data_list.get('dns_name')
        self.rr = data_list.get('RR')
        self.dns_type = data_list.get('Type')
        self.ttl = data_list.get('TTL')
        self.mobiles = data_list.get('mobiles')
        self.master_group = data_list.get('master_group')
        self.backup_group = data_list.get('backup_group')
        describe_dict = ali_dns_api.get_domain_desc(self.dns_name, self.rr)
        # 将所有监控项初始状态置为0(正常)
        # 将备用监控的使用状态置为0(未启用)
        for each_item in self.master_group:
            each_item['status'] = 0
            if receive_type == "ddos":
                each_item['used'] = 1
            each_item['record_id'] = describe_dict.get(each_item.get('record_name'))
        for each_item in self.backup_group:
            each_item['status'] = 0
            each_item['used'] = 0
        logger.info('Dispatcher init ......')
        logger.info('Master group : ' + json.dumps(self.master_group))
        logger.info('Backup group : ' + json.dumps(self.backup_group))
        logger.info('Dispatcher init finished.')

    def callback_dns_handler(self, callback_data, group_type, record_name):
        current_status = 0 if json.loads(callback_data.get('event_data')).get('status') == 'OK' else 1
        if group_type == 'master':
            # 如果master组全部故障，则无需操作
            # 如果master组未全部故障，则更新当前状态
            if not self.check_master_group_collapse():
                current_master_item = self.get_item_in_group_by_record_name(self.master_group, record_name)
                current_master_item['status'] = current_status
                # 再次判断master组是否全部故障，若是，则进行切换操作
                if self.check_master_group_collapse():
                    enable_point = ''
                    disable_point = ''
                    # 添加首个正常且未使用过的备用节点
                    for each_item in self.backup_group:
                        if each_item.get('status') == 0 and each_item.get('used') == 0:
                            record_id_add = ali_dns_api.add_dns(self.dns_name, self.rr, each_item.get('record_name'),
                                                                self.dns_type,
                                                                self.ttl)
                            if record_id_add:
                                each_item['used'] = 1
                                each_item['record_id'] = record_id_add
                                logger.info(
                                    'Enable backup DNS ' + each_item.get(
                                        'record_id') + ' . Current backup_group : ' + json.dumps(
                                        self.backup_group))
                                enable_point += '[' + each_item.get('record_name') + ']'
                            break
                    else:
                        logger.info(
                            'No useful backup DNS left . Current backup_group : ' + json.dumps(self.backup_group))
                    # 关闭所有主节点
                    for each_item in self.master_group:
                        if ali_dns_api.delete_dns_by_record_id(each_item.get('record_id')):
                            logger.info('Delete master DNS ' + each_item.get('record_id') + ' .')
                            disable_point += '[' + each_item.get('record_name') + ']'
                    logger.info('Current master_group : ' + json.dumps(self.master_group))
                    if len(enable_point) > 0 and len(disable_point) > 0:
                        send_content = '尊敬的用户您好，监控检测到您的主节点' + disable_point + '出现故障，目前已经为您切换到备用节点' + enable_point + '，请您知晓！'
                        logger.info('Sending sms to ' + self.mobiles)
                        sms_sender.send(self.mobiles, send_content)
                        logger.info('Sending sms finished.')

        else:
            # 判断当前备用节点状态，如果与历史状态相同，则不作操作
            current_backup_item = self.get_item_in_group_by_record_name(self.backup_group, record_name)
            if current_status != current_backup_item.get('status'):
                # 判断master是否全部故障，若否，则仅更新备节点状态不切换
                if not self.check_master_group_collapse():
                    current_backup_item['status'] = current_status
                    logger.info('Status update . Current backup_group : ' + json.dumps(self.backup_group))
                else:
                    # 若当前备用节点正在使用，且当前状态为故障，则进行切换
                    # 否则，仅更新状态
                    if current_status == 1 and current_backup_item.get('used') == 1:
                        enable_point = ''
                        disable_point = ''
                        current_backup_item['status'] = 1
                        # 查询优先级最高且未使用过的正常节点
                        for each_item in self.backup_group:
                            # 开启节点
                            if each_item.get('status') == 0 and each_item.get('used') == 0:
                                record_id_add = ali_dns_api.add_dns(self.dns_name, self.rr,
                                                                    each_item.get('record_name'),
                                                                    self.dns_type,
                                                                    self.ttl)
                                if record_id_add:
                                    each_item['used'] = 1
                                    each_item['record_id'] = record_id_add
                                    logger.info('Enable backup DNS ' + each_item.get('record_id'))
                                    enable_point += '[' + each_item.get('record_name') + ']'
                                break
                        else:
                            logger.info(
                                'No useful backup DNS left . Current backup_group : ' + json.dumps(self.backup_group))
                        # 关闭当前备用节点
                        if ali_dns_api.delete_dns_by_record_id(current_backup_item.get('record_id')):
                            logger.info('Delete backup DNS ' + current_backup_item.get('record_id'))
                            disable_point += '[' + current_backup_item.get('record_name') + ']'
                        logger.info('Current backup_group : ' + json.dumps(self.backup_group))
                        if len(enable_point) > 0 and len(disable_point) > 0:
                            send_content = '尊敬的用户您好，监控检测到您的备用节点' + disable_point + '出现故障，目前已经为您切换到备用节点' + enable_point + '，请您知晓！'
                            logger.info('Sending sms to ' + self.mobiles)
                            sms_sender.send(self.mobiles, send_content)
                            logger.info('Sending sms finished.')
                    else:
                        # 若当前节点已经使用过，则不更新（废弃）
                        if current_backup_item.get('used') != 1:
                            current_backup_item['status'] = current_status
                            logger.info('Status update . Current backup_group : ' + json.dumps(self.backup_group))

    def callback_ddos_handler(self, callback_data, group_type, record_name):
        # 每个组的节点只取第一个，写多个的情况下后面的无效
        # 收到备用节点的任何告警信息都无需处理
        # 收到主节点告警时，执行
        master_item = self.master_group[0]
        backup_item = self.backup_group[0]
        if group_type == "master" and record_name == master_item.get('record_name'):
            current_status = 0 if json.loads(callback_data.get('event_data')).get('status') == 'OK' else 1
            # 如果当前主节点使用中，且收到故障告警，则切至备用节点
            # 如果当前主节点未使用，且收到恢复告警，则切回主节点
            # 其余情况不处理
            if current_status == 1 and master_item.get('used') == 1:
                enable_point = ''
                disable_point = ''
                # 关闭主节点
                if ali_dns_api.delete_dns_by_record_id(master_item.get('record_id')):
                    master_item['used'] = 0
                    logger.info('Delete master DNS ' + master_item.get('record_id'))
                    disable_point += '[' + master_item.get('record_name') + ']'
                # 开启备用节点
                record_id_add = ali_dns_api.add_dns(self.dns_name, self.rr,
                                                    backup_item.get('record_name'),
                                                    backup_item.get('Type'),
                                                    self.ttl)
                if record_id_add:
                    backup_item['used'] = 1
                    backup_item['record_id'] = record_id_add
                    logger.info('Enable backup DNS ' + backup_item.get('record_id'))
                    enable_point += '[' + backup_item.get('record_name') + ']'
                if len(enable_point) > 0 and len(disable_point) > 0:
                    send_content = '尊敬的用户您好，监控检测到您的节点' + disable_point + '出现故障，目前已经为您切换到高防节点' + enable_point + '，请您知晓！'
                    logger.info('Sending sms to ' + self.mobiles)
                    sms_sender.send(self.mobiles, send_content)
                    logger.info('Sending sms finished.')
            elif current_status == 0 and master_item.get('used') == 0:
                enable_point = ''
                disable_point = ''
                # 关闭备用节点
                if ali_dns_api.delete_dns_by_record_id(backup_item.get('record_id')):
                    backup_item['used'] = 0
                    logger.info('Delete backup DNS ' + backup_item.get('record_id'))
                    disable_point += '[' + backup_item.get('record_name') + ']'
                # 开启主节点
                record_id_add = ali_dns_api.add_dns(self.dns_name, self.rr,
                                                    master_item.get('record_name'),
                                                    master_item.get('Type'),
                                                    self.ttl)
                if record_id_add:
                    master_item['used'] = 1
                    master_item['record_id'] = record_id_add
                    logger.info('Enable master DNS ' + master_item.get('record_id'))
                    enable_point += '[' + master_item.get('record_name') + ']'
                if len(enable_point) > 0 and len(disable_point) > 0:
                    send_content = '尊敬的用户您好，监控检测到您的节点' + enable_point + '恢复正常，目前已经为您切回主节点，请您知晓！'
                    logger.info('Sending sms to ' + self.mobiles)
                    sms_sender.send(self.mobiles, send_content)
                    logger.info('Sending sms finished.')

    def check_master_group_collapse(self):
        for each_item in self.master_group:
            if each_item.get('status') == 0:
                return False
        else:
            return True

    @staticmethod
    def get_item_in_group_by_record_id(group, record_id):
        for each in group:
            if each.get('record_id') == record_id:
                return each
        else:
            return None

    @staticmethod
    def get_item_in_group_by_record_id(group, record_id):
        for each in group:
            if each.get('record_id') == record_id:
                return each
        else:
            return None

    @staticmethod
    def get_item_in_group_by_record_name(group, record_name):
        for each in group:
            if each.get('record_name') == record_name:
                return each
        else:
            return None
