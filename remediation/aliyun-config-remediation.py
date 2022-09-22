#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import logging
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.StopInstanceRequest import StopInstanceRequest

logger = logging.getLogger()


def handler(event, context):
    get_resources_non_compliant(event)


def get_resources_non_compliant(event):
    resources = parse_json(event)
    for resource in resources:
        remediation_ecs_instance_no_public_ip(resource)


def parse_json(content):
    """
    Parse string to json object
    :param content: json string content
    :return: Json object
    """
    try:
        return json.loads(content)
    except Exception as e:
        logger.error('Parse content:{} to json error:{}.'.format(content, e))
        return None


def remediation_ecs_instance_no_public_ip(resource, context):
    logger.info(resource)
    region_id = resource['regionId']
    account_id = resource['accountId']
    resource_id = resource['resourceId']
    resource_type = resource['resourceType']
    config_rule_id = resource['configRuleId']
    if resource_type == 'ACS::ECS::Instance' and config_rule_id == 'cr-xxxxx':
        print(region_id, account_id, resource_id, resource_type, config_rule_id)
        stop_ecs_instance(context, region_id, resource_id)


def stop_ecs_instance(context, resource_region_id, resource_id):
    logger.info("Notice：begin stop instance {}{}".format(resource_region_id, resource_id))

    creds = context.credentials
    client = AcsClient(creds.access_key_id, creds.access_key_secret, region_id=resource_region_id)

    request = StopInstanceRequest()
    request.set_accept_format('json')
    request.set_InstanceId(resource_id)
    request.set_StoppedMode("KeepCharging")
    request.add_query_param('SecurityToken', creds.security_token)

    response = client.do_action_with_exception(request)
    logger.info(response)
