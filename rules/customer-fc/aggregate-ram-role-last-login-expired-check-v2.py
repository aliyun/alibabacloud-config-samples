#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging
import time

from aliyunsdksts.request.v20150401.AssumeRoleRequest import AssumeRoleRequest

from aliyunsdkcore.auth.credentials import StsTokenCredential
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from alibabacloud_sls20201230.client import Client as Sls20201230Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_sls20201230 import models as sls_20201230_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


"""
该函数基于config配置变更触发。
"""
logger = logging.getLogger()
# 合规类型
COMPLIANCE_TYPE_COMPLIANT = 'COMPLIANT'
COMPLIANCE_TYPE_NON_COMPLIANT = 'NON_COMPLIANT'
COMPLIANCE_TYPE_NOT_APPLICABLE = 'NOT_APPLICABLE'
COMPLIANCE_TYPE_IGNORED = 'IGNORED'
# 资源配置推送类型
CONFIGURATION_TYPE_COMMON = 'COMMON'
CONFIGURATION_TYPE_OVERSIZE = 'OVERSIZE'
CONFIGURATION_TYPE_NONE = 'NONE'

# Config api endpoint, International sites use ap-southeast-1 and config.ap-southeast-1.aliyuncs.com
CONFIG_SERVICE_REGION = 'cn-shanghai'
CONFIG_SERVICE_ENDPOINT = 'config.cn-shanghai.aliyuncs.com'

ACTIONTRAIL_SERVICE_REGION='cn-hangzhou'

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
    resource_name = configuration_item.get('resourceName')
    resource_type = configuration_item.get('resourceType')
    region_id = configuration_item.get('regionId')

    if filter_configuration_item(configuration_item):
        logger.info('filter hit resource {} {}.'.format(resource_id, resource_name))
        compliance_type = COMPLIANCE_TYPE_IGNORED
        annotation = "filter ignored."
    else:
        logger.info('evaluate resource {} {}.'.format(resource_id, resource_name))
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

    put_evaluations(context, result_token, evaluations)
    return evaluations

def filter_configuration_item(item):
    filter_exclude_resources = ["332629018877xxxxxx", "332629018878xxxxxx"]
    resource_id = item.get('resourceId')
    if resource_id in filter_exclude_resources:
        return True

    resource_name = item.get('resourceName')
    return resource_name.startswith("Aliyun")

# 实现资源评估逻辑
def evaluate_configuration_item(context, rule_parameters, configuration_item):
    compliance_type = COMPLIANCE_TYPE_NON_COMPLIANT
    annotation = None

    full_configuration = configuration_item['configuration']
    configuration = parse_json(full_configuration)
    resource_id = configuration_item["resourceId"]
    sls_project, sls_logstore = actiontrail_get_default_trail(context)

    ## 只查看第一页是否有数据
    cnt = sls_get_logs_cnt(context, sls_project, sls_logstore, resource_id)
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
    creds = context.credentials
    credentials = StsTokenCredential(creds.access_key_id, creds.access_key_secret, creds.security_token)
    client = AcsClient(region_id=CONFIG_SERVICE_REGION, credential=credentials)
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
def actiontrail_get_default_trail(context):
    creds = context.credentials
    credentials = StsTokenCredential(creds.access_key_id, creds.access_key_secret, creds.security_token)
    client = AcsClient(region_id=CONFIG_SERVICE_REGION, credential=credentials)
    logger.info("init at client ok.")

    try:
        request = CommonRequest()
        request.set_accept_format('json')
        domain = 'actiontrail.' + ACTIONTRAIL_SERVICE_REGION + '.aliyuncs.com'
        request.set_domain(domain)
        logger.info('actiontrail_get_default_trail domain: {}.'.format(domain))

        request.set_method('POST')
        request.set_protocol_type('https')
        request.set_version('2020-07-06')
        request.set_action_name('DescribeTrails')
        request.add_query_param('IncludeOrganizationTrail', True)
        response = client.do_action_with_exception(request)
        logger.info('actiontrail_get_default_trail response : {}.'.format(response))
        resource_result = str(response, encoding='utf-8')
        for trail_detail in json.loads(resource_result)['TrailList']:
            logger.info('actiontrail_get_default_trail loop trail : {}.'.format(trail_detail))

            sls_project = str.split(trail_detail['SlsProjectArn'], '/')[1]
            sls_logstore = 'actiontrail_' + str.split(trail_detail['TrailArn'], '/')[1]
            is_organization_trail = trail_detail['IsOrganizationTrail']

            ## 多账号
            if is_organization_trail:
                return sls_project, sls_logstore

    except Exception as e:
        logger.error('DescribeTrails error: %s' % e)


def sls_get_logs_cnt(context, project, logstore, resource_id):
    token = assume_role_and_get_token(context)
    config = open_api_models.Config(token['Credentials']['AccessKeyId'], token['Credentials']['AccessKeySecret'],
                                    token['Credentials']['SecurityToken'])
    config.endpoint = f'cn-hangzhou.log.aliyuncs.com'
    client = Sls20201230Client(config)

    x_days = 90

    to_timestamp = int(round(time.time()))
    from_timestamp = to_timestamp - x_days * 24 * 60 * 60
    get_logs_request = sls_20201230_models.GetLogsRequest(
        from_=from_timestamp,
        to=to_timestamp,
        query='event.userIdentity.principalId: ' + resource_id  # event.userIdentity.principalId: 389051450072705987
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

def assume_role_and_get_token(context):
    creds = context.credentials
    logger.info('assume_role_and_get_token begin : {}.'.format(creds))
    credentials = StsTokenCredential(creds.access_key_id, creds.access_key_secret, creds.security_token)
    client = AcsClient(credential=credentials)

    request = AssumeRoleRequest()
    request.set_accept_format('json')

    request.set_RoleArn('acs:ram::1783661826xxxxxx:role/actiontraildeliveryrole')
    request.set_RoleSessionName("ActionTrailDeliveryRole")
    response = client.do_action_with_exception(request)
    logger.info('assume_role_and_get_token response : {}.'.format(response))

    print(str(response, encoding='utf-8'))
    token = json.loads(response)
    logger.info('assume_role_and_get_token: {}, assume role: {}.'.format(context.credentials, token))
    return token
