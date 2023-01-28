#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging
import time
from datetime import datetime

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from alibabacloud_sls20201230.client import Client as Sls20201230Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_sls20201230 import models as sls_20201230_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

"""
该函数基于config配置变更触发。
多账号场景下，通过actiontrail获取角色是否有审计日志，并作为合规判断的逻辑依据，有日志合规，没有不合规。
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

    compliance_type, annotation = evaluate_configuration_item(rule_parameters, configuration_item)
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
    compliance_type = COMPLIANCE_TYPE_NON_COMPLIANT
    annotation = None

    full_configuration = configuration_item['configuration']
    configuration = parse_json(full_configuration)
    resource_id = configuration_item["resourceId"]
    sls_region_id, sls_project, sls_logstore = actiontrail_get_default_trail(resource_id)

    ## 只查看第一页是否有数据
    cnt = sls_get_logs_cnt(sls_region_id, sls_project, sls_logstore, resource_id)
    if cnt and cnt > 0:
        compliance_type = COMPLIANCE_TYPE_COMPLIANT
        annotation = json.dumps({'configuration': '', 'desiredValue': '', 'operator': ''})

    else:
        annotation = json.dumps({'configuration': 'RAM Role have no activity within X (90) days', 'desiredValue': '', 'operator': ''})

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


## 需要设置配置审计跟踪并设置为模版跟踪，使用sls的高级搜索能力
def actiontrail_get_default_trail(role_name):
    client = AcsClient(AK, SK, 'cn-hangzhou')

    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('actiontrail.cn-hangzhou.aliyuncs.com')
    request.set_method('POST')
    request.set_protocol_type('https')  # https | http
    request.set_version('2020-07-06')
    request.set_action_name('GetDefaultTrail')

    try:
        response = client.do_action_with_exception(request)
        resource_result = str(response, encoding='utf-8')
        json_res = json.loads(resource_result)

        actiontrail_name_list = json_res['Name']

        if actiontrail_name_list:
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('actiontrail.cn-hangzhou.aliyuncs.com')
            request.set_method('POST')
            request.set_protocol_type('https')  # https | http
            request.set_version('2020-07-06')
            request.set_action_name('DescribeTrails')
            request.add_query_param('NameList', actiontrail_name_list)
            response = client.do_action_with_exception(request)
            resource_result = str(response, encoding='utf-8')
            trail_detail = json.loads(resource_result)['TrailList'][0]
            sls_project_arn = trail_detail['SlsProjectArn']
            region_id = str.split(sls_project_arn, ':')[2]
            sls_project = str.split(sls_project_arn, '/')[1]
            sls_logstore = 'actiontrail_' + str.split(trail_detail['TrailArn'], '/')[1]
            is_organization_trail = trail_detail['IsOrganizationTrail']
            ## 开启高级搜索，且为多账号
            if is_organization_trail:
                return region_id, sls_project, sls_logstore

    except Exception as e:
        logger.error('DescribeTrails error: %s' % e)


def sls_get_logs_cnt(region_id, project, logstore, resource_id):
    config = open_api_models.Config(access_key_id=AK, access_key_secret=SK)
    config.endpoint = region_id + '.log.aliyuncs.com'
    client = Sls20201230Client(config)

    x_days = 90

    to_timestamp = int(round(time.time()))
    from_timestamp = to_timestamp - x_days * 24 * 60 * 60
    get_logs_request = sls_20201230_models.GetLogsRequest(
        from_=from_timestamp,
        to=to_timestamp,
        query='event.userIdentity.principalId: ' + resource_id  # event.userIdentity.principalId: 389051450072xxxxxx
    )
    try:
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = client.get_logs_with_options(project, logstore,
                                                    get_logs_request, headers, runtime)
            events_cnt = len(response.body)
            return events_cnt

        except Exception as error:
            UtilClient.assert_as_string(error.message)

    except Exception as e:
        logger.error('GetLogsRequest error: %s' % e)
