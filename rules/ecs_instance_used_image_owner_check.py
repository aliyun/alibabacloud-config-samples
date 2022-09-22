#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

"""
该函数基于config配置变更触发。
收到ECS实例的资源变更事件后查询实例所使用镜像的详细信息，检测镜像的来源，如果镜像是阿里云提供的公共镜像视为合规，否则视为不合规
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
def evaluate_configuration_item(context, rule_parameters, configuration_item):
    instance_region_id = configuration_item["RegionId"]
    instance_image_id = configuration_item["ImageId"]
    image_owner = query_image_owner(context, instance_region_id, instance_image_id)

    compliance_type = COMPLIANCE_TYPE_COMPLIANT
    annotation = None
    desired_owner = 'system'
    if not image_owner or image_owner != desired_owner:
        compliance_type = COMPLIANCE_TYPE_NON_COMPLIANT
        annotation = json.dumps({'configuration': image_owner, 'desiredValue': desired_owner, 'operator': 'Equals'})
    return compliance_type, annotation


def query_ecs_endpoint(context, region_id):
    client = AcsClient(AK, SK, region_id)

    ecs_center_endpoint = "ecs.aliyuncs.com"
    request = CommonRequest()
    request.set_domain('ecs.aliyuncs.com')
    request.set_version('2014-05-26')
    request.set_action_name('DescribeRegions')
    request.set_method('GET')

    response = client.do_action_with_exception(request)
    res = str(response, encoding='utf-8')
    json_res = json.loads(res)
    for region_info in json_res["Regions"]["Region"]:
        if region_id == region_info["RegionId"]:
            return region_info["RegionEndpoint"]
    return ecs_center_endpoint


def query_image_owner(context, region_id, image_id):
    client = AcsClient(AK, SK, region_id)

    ecs_endpoint = query_ecs_endpoint(context, region_id)
    request = CommonRequest()
    request.set_domain(ecs_endpoint)
    request.set_version('2014-05-26')
    request.set_action_name('DescribeImages')
    request.add_query_param('RegionId', region_id)
    request.add_query_param('ImageId', image_id)
    request.add_query_param('ShowExpired', True)
    request.set_method('GET')

    response = client.do_action_with_exception(request)
    res = str(response, encoding='utf-8')
    json_res = json.loads(res)
    if "Images" in json_res and json_res["Images"] and "Image" in json_res["Images"] and json_res["Images"]["Image"]:
        image_info = json_res["Images"]["Image"][0]
        return image_info["ImageOwnerAlias"]
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
