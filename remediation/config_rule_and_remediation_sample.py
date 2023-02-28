#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkconfig.request.v20200907.GetResourceComplianceByConfigRuleRequest import \
    GetResourceComplianceByConfigRuleRequest
from aliyunsdkcore.request import CommonRequest

"""
this script for configRule required-tags and remediation non_compliance resources。
"""

CONFIG_SERVICE_ENDPOINT = 'config.cn-shanghai.aliyuncs.com'

## aliyun config CreateConfigRule --region cn-shanghai --ConfigRuleName '存在所有指定标签' --Description '最多可定义6组标签，资源需同时具有指定的所有标签，视为“合规”。标签输入大小写敏感，每组最多只能输入一个值。' --ResourceTypesScope 'ACS::ECS::Disk,ACS::ECS::Instance' --InputParameters '{"tag6Value":"","tag6Key":"","tag5Value":"","tag5Key":"","tag4Value":"","tag4Key":"","tag3Value":"","tag3Key":"","tag2Value":"","tag2Key":"","tag1Value":"test","tag1Key":"env"}' --ConfigRuleTriggerTypes ConfigurationItemChangeNotification --RiskLevel 1 --SourceOwner ALIYUN --SourceIdentifier 'required-tags' --version 2020-09-07 --force
def create_config_rule(ak, sk, tag_key, tag_value):
    credentials = AccessKeyCredential(ak, sk)
    # use STS Token
    # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
    client = AcsClient(region_id='cn-shanghai', credential=credentials)
    request = CommonRequest()
    request.set_domain(CONFIG_SERVICE_ENDPOINT)
    request.set_version('2020-09-07')
    request.set_action_name('CreateConfigRule')
    request.set_method('POST')

    request.add_body_params("ConfigRuleName", "存在所有指定标签By SDK")
    request.add_body_params("Description", "最多可定义6组标签，资源需同时具有指定的所有标签，视为“合规”。标签输入大小写敏感，每组最多只能输入一个值。")
    request.add_body_params("ResourceTypesScope", "ACS::ECS::Disk")

    tags_tuples = {
        "tag1Value": tag_key,
        "tag1Key": tag_value,
        "tag6Value": "",
        "tag6Key": "",
        "tag5Value": "",
        "tag5Key": "",
        "tag4Value": "",
        "tag4Key": "",
        "tag3Value": "",
        "tag3Key": "",
        "tag2Value": "",
        "tag2Key": ""
    }
    request.add_body_params("InputParameters", tags_tuples)
    request.add_body_params("ConfigRuleTriggerTypes", 'ConfigurationItemChangeNotification')
    request.add_body_params("RiskLevel", 1)
    request.add_body_params("SourceOwner", 'ALIYUN')
    request.add_body_params("SourceIdentifier", 'required-tags')

    response = client.do_action_with_exception(request)
    resource_result = str(response, encoding='utf-8')
    json_res = json.loads(resource_result)
    return json_res['ConfigRuleId']

def create_rule_remediation(ak, sk, config_rule_id, tag_key, tag_value):
    credentials = AccessKeyCredential(ak, sk)
    # use STS Token
    # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
    client = AcsClient(region_id='cn-shanghai', credential=credentials)

    request = CommonRequest()
    request.set_domain(CONFIG_SERVICE_ENDPOINT)
    request.set_version('2020-09-07')
    request.set_action_name('CreateRemediation')
    request.set_method('POST')

    request.add_body_params("ConfigRuleId", config_rule_id)
    request.add_body_params("RemediationType", 'OOS')
    request.add_body_params("RemediationTemplateId", 'ACS-TAG-TagResources')
    request.add_body_params("InvokeType", 'MANUAL_EXECUTION')
    request.add_body_params("SourceType", 'ALIYUN')

    tags = {
        tag_key: tag_value
    }
    params = {
        "properties": [
            {
                "name": "regionId",
                "type": "STRING",
                "value": "{regionId}",
                "allowedValues": [],
                "description": "[Required]地域ID。"
            },
            {
                "name": "tags",
                "type": "OBJECT",
                "value": json.dumps(tags),
                "allowedValues": [],
                "description": "[Required]资源标签（例：{\"k1\":\"v1\",\"k2\":\"v2\"}）。"
            },
            {
                "name": "resourceType",
                "type": "STRING",
                "value": "{resourceType}",
                "allowedValues": [],
                "description": "[Required]资源类型。"
            },
            {
                "name": "resourceIds",
                "type": "ARRAY",
                "value": "[\"{resourceId}\"]",
                "allowedValues": [],
                "description": "[Required]资源ID。"
            }
        ]
    }
    request.add_body_params("Params", json.dumps(params))
    response = client.do_action_with_exception(request)
    resource_result = str(response, encoding='utf-8')
    json_res = json.loads(resource_result)
    return json_res['RemediationId']

def start_remediation(ak, sk, config_rule_id):
    credentials = AccessKeyCredential(ak, sk)
    # use STS Token
    # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
    client = AcsClient(region_id='cn-shanghai', credential=credentials)

    request = CommonRequest()
    request.set_domain(CONFIG_SERVICE_ENDPOINT)
    request.set_version('2020-09-07')
    request.set_action_name('StartRemediation')
    request.set_method('POST')

    request.add_body_params("ConfigRuleId", config_rule_id)

    response = client.do_action_with_exception(request)
    print(str(response, encoding='utf-8'))


def get_resource_compliance_by_config_rule(ak, sk, config_rule_id):
    credentials = AccessKeyCredential(ak, sk)
    # use STS Token
    # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
    client = AcsClient(region_id='cn-shanghai', credential=credentials)

    # request = CommonRequest()
    # request.set_domain(CONFIG_SERVICE_ENDPOINT)
    # request.set_version('2020-09-07')
    # request.set_action_name('GetResourceComplianceByConfigRule')
    # request.set_method('POST')
    #
    # request.add_body_params("ConfigRuleId", config_rule_id)
    # request.add_body_params("ComplianceType", 'NON_COMPLIANT')

    request = GetResourceComplianceByConfigRuleRequest()
    request.set_accept_format('json')

    request.set_ComplianceType("NON_COMPLIANT")
    request.set_ConfigRuleId(config_rule_id)


    response = client.do_action_with_exception(request)
    # {
    #     "ComplianceResult": {
    #         "TotalCount": 5184,
    #         "Compliances": [
    #             {
    #                 "ComplianceType": "NON_COMPLIANT",
    #                 "Count": 5184
    #             }
    #         ]
    #     },
    #     "RequestId": "D501D416-B64C-55E2-8B37-62E267317086"
    # }
    resource_result = str(response, encoding='utf-8')
    json_res = json.loads(resource_result)
    for compliance in json_res['ComplianceResult']['Compliances']:
        if compliance['ComplianceType'] == 'NON_COMPLIANT':
            return compliance['Count']
    return 0


if __name__ == '__main__':
    AccessKey = 'xxx'
    AccessSecret = 'xxx'

    ## settings
    tag_key = 'env'
    tag_value = 'test'
    config_rule_id = create_config_rule(AccessKey, AccessSecret, tag_key, tag_value)
    create_rule_remediation(AccessKey, AccessSecret, config_rule_id, tag_key, tag_value)

    ## remediation execution and monitor
    print("start remediation configRuleId" + config_rule_id)
    start_remediation(AccessKey, AccessSecret, config_rule_id)
    non_compliance_cnt = get_resource_compliance_by_config_rule(AccessKey, AccessSecret,config_rule_id)

    print("finish remediation configRuleId" + config_rule_id)
