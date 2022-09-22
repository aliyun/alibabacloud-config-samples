#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

"""
该函数基于config配置变更触发。
收到安全组的资源变更事件后检测当前资源的入方向规则配置：授权来源是否包含参数中指定的IP段，包含视为合规、不包含视为不合规、云产品或虚商所使用的的安全组视为不适用
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

AK = '********'
SK = '********'


# 入口方法
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

    compliance_type, annotation = evaluate_configuration_item(
        rule_parameters, configuration_item)
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

    put_evaluations(context, result_token, evaluations)
    return evaluations


# 实现资源评估逻辑
def evaluate_configuration_item(rule_parameters, configuration_item):
    # 示例中要检测的cidr参数名为checkCidr，实际应用中可以自行设定名称
    param_cidr = rule_parameters["checkCidr"]
    compliance_type = COMPLIANCE_TYPE_NON_COMPLIANT
    annotation = None

    full_configuration = configuration_item['configuration']
    configuration = parse_json(full_configuration)
    service_managed = configuration["ServiceManaged"]
    if service_managed:
        compliance_type = COMPLIANCE_TYPE_NOT_APPLICABLE
        return compliance_type, annotation

    permission_list = configuration["Permissions"]
    for permission in permission_list:
        policy = permission["Policy"]
        direction = permission["Direction"]
        source_cidr_ip = permission["SourceCidrIp"]
        if policy == "Accept" and direction == "ingress" and source_cidr_ip == param_cidr:
            compliance_type = COMPLIANCE_TYPE_COMPLIANT
            return compliance_type, annotation

    annotation = json.dumps({'configuration': '', 'desiredValue': param_cidr, 'operator': 'Equals'})
    return compliance_type, annotation


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


def put_evaluations(context, result_token, evaluations):
    client = AcsClient(AK, SK, CONFIG_SERVICE_REGION)

    request = CommonRequest()
    request.set_domain(CONFIG_SERVICE_ENDPOINT)
    request.set_version('2019-01-08')
    request.set_action_name('PutEvaluations')
    request.add_body_params('ResultToken', result_token)
    request.add_body_params('Evaluations', evaluations)
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
