#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging
from os.path import abspath

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.http import protocol_type

"""
该函数同时支持config配置变更触发和周期触发。
收到配置变更或周期触发事件时，查询当前事件中的VPC是否开启了流日志，如果开启视为合规，未开启视为不合规。
判断当前触发类型如果是周期触发，则开启删除模式，config会自动清理非本周期内评估的记录
"""
logger = logging.getLogger()
# 合规类型
COMPLIANCE_TYPE_COMPLIANT = 'COMPLIANT'
COMPLIANCE_TYPE_NON_COMPLIANT = 'NON_COMPLIANT'
COMPLIANCE_TYPE_NOT_APPLICABLE = 'NOT_APPLICABLE'
# 资源配置推送类型
CONFIGURATION_TYPE_COMMON = 'COMMON'
CONFIGURATION_TYPE_OVERSIZE = 'OVERSIZE'
CONFIGURATION_TYPE_NONE = 'NONE'

# Config api endpoint, International sites use ap-southeast-1 and config.ap-southeast-1.aliyuncs.com
CONFIG_SERVICE_REGION = 'cn-shanghai'
CONFIG_SERVICE_ENDPOINT = 'config.cn-shanghai.aliyuncs.com'

AK = '******'
SK = '******'


# main function
# event schema https://help.aliyun.com/document_detail/127405.html
def handler(event, context):
    evt = validate_event(event)
    if not evt:
        return None

    rule_parameters = evt.get('ruleParameters')
    result_token = evt.get('resultToken')
    ordering_timestamp = evt.get('orderingTimestamp')
    invoking_event = evt.get('invokingEvent')
    configuration_item = invoking_event.get('configurationItem')
    account_id = configuration_item.get('accountId')
    resource_id = configuration_item.get('resourceId')
    resource_type = configuration_item.get('resourceType')
    region_id = configuration_item.get('regionId')

    configuration_type = invoking_event.get('configurationType')
    if configuration_type and configuration_type == CONFIGURATION_TYPE_OVERSIZE:
        resource_result = get_discovered_resource(context, resource_id, resource_type, region_id)
        resource_json = json.loads(resource_result)
        configuration_item["configuration"] = resource_json["DiscoveredResourceDetail"]["Configuration"]

    compliance_type, annotation = evaluate_configuration_item(context, rule_parameters, configuration_item)
    evaluations = [
        {
            'accountId': account_id,
            'complianceResourceId': resource_id,
            'complianceResourceType': resource_type,
            'complianceRegionId': region_id,
            'orderingTimestamp': ordering_timestamp,
            'complianceType': compliance_type,
            'annotation': annotation
        }
    ]

    message_type = invoking_event.get('messageType')
    put_evaluations(context, result_token, evaluations, message_type)
    return evaluations


# 实现资源评估逻辑
def evaluate_configuration_item(context, rule_parameters, configuration_item):
    vpc_region_id = configuration_item["regionId"]
    vpc_id = json.loads(configuration_item['configuration'])["VpcId"]
    vpc_logs_count = query_vpc_logs(context, vpc_region_id, vpc_id)

    compliance_type = COMPLIANCE_TYPE_COMPLIANT
    annotation = None
    if not vpc_logs_count or vpc_logs_count <= 0:
        compliance_type = COMPLIANCE_TYPE_NON_COMPLIANT
        annotation = json.dumps({'configuration': 'Not enable flowLogs', 'desiredValue': 'Enable flowLogs'})
    return compliance_type, annotation


def query_vpc_endpoint(context, region_id):
    client = AcsClient(
        AK,
        SK,
        'region_id',
    )

    vpc_center_endpoint = "vpc.aliyuncs.com"
    request = CommonRequest()
    request.set_domain('vpc.aliyuncs.com')
    request.set_version('2016-04-28')
    request.set_action_name('DescribeRegions')
    request.set_method('GET')

    response = client.do_action_with_exception(request)
    res = str(response, encoding='utf-8')
    json_res = json.loads(res)
    for region_info in json_res["Regions"]["Region"]:
        if region_id == region_info["RegionId"]:
            return region_info["RegionEndpoint"]
    return vpc_center_endpoint


def query_vpc_logs(context, region_id, vpc_id):
    client = AcsClient(AK, SK, region_id)

    vpc_endpoint = query_vpc_endpoint(context, region_id)
    request = CommonRequest()
    request.set_protocol_type(protocol_type.HTTPS)
    request.set_domain(vpc_endpoint)
    request.set_version('2016-04-28')
    request.set_action_name('DescribeFlowLogs')
    request.set_method('GET')
    request.add_query_param('RegionId', region_id)
    request.add_query_param('ResourceType', 'VPC')
    request.add_query_param('ResourceId', vpc_id)
    request.add_query_param('Status', 'Active')

    response = client.do_action_with_exception(request)
    res = str(response, encoding='utf-8')
    json_res = json.loads(res)
    if "TotalCount" in json_res and json_res["TotalCount"] > 0:
        return json_res["TotalCount"] > 0
    return None


def validate_event(event):
    if not event:
        logger.error('Event is empty.')
    evt = parse_json(event)
    logger.info('Loading event: %s .' % evt)

    if 'resultToken' not in evt:
        logger.error('ResultToken is empty.')
        return None
    if 'ruleParameters' not in evt:
        logger.error('RuleParameters is empty.')
        return None
    if 'invokingEvent' not in evt:
        logger.error('InvokingEvent is empty.')
        return None
    return evt


def parse_json(content):
    try:
        return json.loads(content)
    except Exception as e:
        logger.error('Parse content:{} to json error:{}.'.format(content, e))
        return None


def put_evaluations(context, result_token, evaluations, message_type):
    client = AcsClient(AK, SK, CONFIG_SERVICE_REGION)

    request = CommonRequest()
    request.set_domain(CONFIG_SERVICE_ENDPOINT)
    request.set_version('2019-01-08')
    request.set_action_name('PutEvaluations')
    request.add_body_params('ResultToken', result_token)
    request.add_body_params('Evaluations', evaluations)
    if message_type and message_type == 'ScheduledNotification':
        request.add_body_params('DeleteMode', True)
    request.set_method('POST')

    try:
        response = client.do_action_with_exception(request)
        logger.info('PutEvaluations with request: {}, response: {}.'.format(request, response))
    except Exception as e:
        logger.error('PutEvaluations error: %s' % e)


def get_discovered_resource(context, resource_id, resource_type, region_id):
    client = AcsClient(AK, SK, CONFIG_SERVICE_REGION)

    request = CommonRequest()
    request.set_domain(CONFIG_SERVICE_ENDPOINT)
    request.set_version('2020-09-07')
    request.set_action_name('GetDiscoveredResource')
    request.add_query_param('ResourceId', resource_id)
    request.add_query_param('ResourceType', resource_type)
    request.add_query_param('Region', region_id)
    request.set_method('GET')

    try:
        response = client.do_action_with_exception(request)
        resource_result = str(response, encoding='utf-8')
        return resource_result
    except Exception as e:
        logger.error('GetDiscoveredResource error: %s' % e)