# -*- coding: utf-8 -*-

import json
import logging
import os

from alibabacloud_tea_openapi.client import Client as OpenApiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_openapi_util.client import Client as OpenApiUtilClient


sts_access_key_id = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID')
sts_access_key_secret = os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
sts_security_token = os.environ.get('ALIBABA_CLOUD_SECURITY_TOKEN')

logger = logging.getLogger()

DESIRED_TAG = '[{"TagKey":"app_id","TagValue":"200345"},{"TagKey":"app_name","TagValue":"name"},{"TagKey":"env","TagValue":"dev"},{"TagKey":"owner_div","TagValue":"054"},{"TagKey":"owner_dept","TagValue":"0645"}]'

def handler(event, context):

  evt = json.loads(event)

  for resource in evt:
    account_id = resource.get('accountId')
    resource_id = resource.get('resourceId')
    resource_type = resource.get('resourceType')
    region_id = resource.get('regionId')
    try:
      tag_resources(context, resource_id, resource_type, region_id)
    except:
      continue


def tag_resources(context, resource_id, resource_type, region_id):
    config = open_api_models.Config(
            access_key_id = sts_access_key_id,
            access_key_secret = sts_access_key_secret,
            security_token = sts_security_token
    )
    logger.info(f'check {region_id}')
    config.endpoint = f'kms.{region_id}.aliyuncs.com'
    client = OpenApiClient(config)

    params = open_api_models.Params(
        action='TagResource',
        version='2016-01-20',
        protocol='HTTPS',
        method='POST',
        auth_type='AK',
        style='RPC',
        pathname=f'/',
        req_body_type='json',
        body_type='json'
    )
    resource_type_params = 'KeyId' if resource_type == 'ACS::KMS::Key' else 'SecretName'
    queries = {resource_type_params: resource_id,
               'Tags': DESIRED_TAG}
    # runtime options
    runtime = util_models.RuntimeOptions()
    request = open_api_models.OpenApiRequest(
        query=OpenApiUtilClient.query(queries)
    )
    try:
        response = client.call_api(params, request, runtime)
        logger.info('tag_resources with request: {}, response: {}.'.format(request, response))
    except Exception as e:
          logger.error('tag_resources error: %s' % e)


# def tag_resources(context, resource_id, resource_type, region_id):
#     config = open_api_models.Config(
#             access_key_id = sts_access_key_id,
#             access_key_secret = sts_access_key_secret,
#             security_token = sts_security_token
#     )
#     logger.info(f'check {region_id}')
#     config.endpoint = f'kms.{region_id}.aliyuncs.com'
#     client = OpenApiClient(config)

#     params = open_api_models.Params(
#         action='UntagResource',
#         version='2016-01-20',
#         protocol='HTTPS',
#         method='POST',
#         auth_type='AK',
#         style='RPC',
#         pathname=f'/',
#         req_body_type='json',
#         body_type='json'
#     )
#     resource_type_params = 'KeyId' if resource_type == 'ACS::KMS::Key' else 'SecretName'
#     UNTAG_KEYS ='["a_sys_app_id","a_sys_app_id1","a_sys_app_name","a_sys_env","a_sys_owner_div","a_sys_owner_dept"]'
#     queries = {resource_type_params: resource_id,
#                'TagKeys': UNTAG_KEYS}
#     # runtime options
#     runtime = util_models.RuntimeOptions()
#     request = open_api_models.OpenApiRequest(
#         query=OpenApiUtilClient.query(queries)
#     )
#     try:
#         response = client.call_api(params, request, runtime)
#         logger.info('tag_resources with request: {}, response: {}.'.format(request, response))
#     except Exception as e:
#           logger.error('tag_resources error: %s' % e)
