# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import json
import time

from alibabacloud_config20200907.client import Client as Config20200907Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_config20200907 import models as config_20200907_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

AccessKey = 'xxx'
AccessSecret = 'xxx'


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
            access_key_id: str,
            access_key_secret: str,
    ) -> Config20200907Client:
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        # 访问的域名
        config.endpoint = f'config.cn-hangzhou.aliyuncs.com'
        return Config20200907Client(config)

    @staticmethod
    def create_config_rule(
            input_parameters
    ) -> str:

        client = Sample.create_client(AccessKey, AccessSecret)
        create_config_rule_request = config_20200907_models.CreateConfigRuleRequest(
            config_rule_name='delta-required-tags-by-sdk-v2',
            description='最多可定义6组标签，资源需同时具有指定的所有标签，视为“合规”。标签输入大小写敏感，每组最多只能输入一个值。',
            resource_types_scope=[
                # 'ACS::ECS::Disk',
                'ACS::ECS::Instance',
                'ACS::OSS::Bucket'
            ],
            input_parameters=input_parameters,
            config_rule_trigger_types='ConfigurationItemChangeNotification',
            risk_level=1,
            source_owner='ALIYUN',
            source_identifier='required-tags'
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            response = client.create_config_rule_with_options(create_config_rule_request, runtime)
            print("finish create_config_rule rule_id:" + response.body.config_rule_id)
            return response.body.config_rule_id

        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)

    @staticmethod
    def create_remediation(
            config_rule_id,
            remediation_tags
    ) -> None:
        # 工程代码泄露可能会导致AccessKey泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        client = Sample.create_client(AccessKey, AccessSecret)
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
                    "value": json.dumps(remediation_tags),
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
        create_remediation_request = config_20200907_models.CreateRemediationRequest(
            config_rule_id=config_rule_id,
            remediation_type='OOS',
            remediation_template_id='ACS-TAG-TagResources',
            invoke_type='MANUAL_EXECUTION',
            source_type='ALIYUN',
            params=json.dumps(params)
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            response = client.create_remediation_with_options(create_remediation_request, runtime)
            print("finish create_remediation remediation_id:" + response.body.remediation_id)
        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)

    @staticmethod
    def start_remediation(
            config_rule_id
    ) -> None:
        client = Sample.create_client(AccessKey, AccessSecret)
        start_remediation_request = config_20200907_models.StartRemediationRequest(
            config_rule_id=config_rule_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            client.start_remediation_with_options(start_remediation_request, runtime)
            print("finish start_remediation config_rule_id:" + config_rule_id)

        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)

    @staticmethod
    def get_resource_compliance_by_config_rule(
            config_rule_id
    ) -> None:
        client = Sample.create_client(AccessKey, AccessSecret)
        get_resource_compliance_by_config_rule_request = config_20200907_models.GetResourceComplianceByConfigRuleRequest(
            compliance_type='NON_COMPLIANT',
            config_rule_id=config_rule_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            response = client.get_resource_compliance_by_config_rule_with_options(
                get_resource_compliance_by_config_rule_request, runtime)
            for res in response.body.compliance_result.compliances:
                if res.compliance_type == 'NON_COMPLIANT':
                    return res.count
            return 0
        except Exception as error:
            # 如有需要，请打印 error
            UtilClient.assert_as_string(error.message)


if __name__ == '__main__':
    input_parameters = {
        "tag1Key": "a_sys_app_id",
        "tag1Value": "200345",
        "tag2Key": "a_sys_app_name",
        "tag2Value": "name",
        "tag3Key": "a_sys_env",
        "tag3Value": "dev",
        "tag4Key": "a_sys_owner_div",
        "tag4Value": "054",
        "tag5Key": "a_sys_owner_dept",
        "tag5Value": "0645",
        "tag6Key": "",
        "tag6Value": ""
    }
    config_rule_id = Sample.create_config_rule(input_parameters)

    # remediation_tags = {
    #     "a_sys_app_id":"200345",
    #     "a_sys_app_name": "name",
    #     "a_sys_env": "dev",
    #     "a_sys_owner_div": "054",
    #     "a_sys_owner_dept": "0645",
    # }
    # Sample.create_remediation(config_rule_id, remediation_tags)
    # 
    # ## wait for 60s, after finish evaluate then start remediation execution and monitor
    # time.sleep(60)
    # print("start remediation configRuleId:" + config_rule_id)
    # Sample.start_remediation(config_rule_id)
    # time.sleep(60)
    # ## 等异步评估任务完成再探查合规记录count
    # non_compliance_cnt = Sample.get_resource_compliance_by_config_rule(config_rule_id)

    print("finish remediation configRuleId:" + config_rule_id)
