provider "alicloud" {
  region     = "cn-shanghai"
  access_key = "xxx"
  secret_key = "xxx"
  assume_role {
    role_arn = "acs:ram::107315933626xxx:role/config_test"
    session_name       = "config_test"
  }
}
variable "rule_required_tags_input_parameters" {
  type        = map
  description = ""
  default = {
      "tag1Key":"env",
      "tag1Value": "prod",
      "tag2Key": "owner",  
      "tag2Value": "Tomc"
  }
}

variable "rule_required_tags_resource_types_scope" {
  type        = list
  description = ""
  default =[
    "ACS::RDS::DBInstance",
    "ACS::ECS::SecurityGroup"
  ]
}

resource "alicloud_config_rule" "tf_requried_tags_managed_rule" {
  description                = "关联的资源类型下实体资源均已有指定标签，存在没有指定标签的资源则视为“不合规”。"
  source_owner               = "ALIYUN"
  source_identifier          = "required-tags"
  risk_level                 = 1
  config_rule_trigger_types  = "ConfigurationItemChangeNotification"
  resource_types_scope = var.rule_required_tags_resource_types_scope
  rule_name = "tf-auto-rule-by-required-tags"
  input_parameters = var.rule_required_tags_input_parameters
}


variable "remediation_required_tags_input_parameters_all" {
  type        = any
  default = {
    "properties": [
      {
        "name": "regionId",
        "type": "String",
        "value": "{regionId}",
        "allowedValues": [ ],
        "description": "[Required]地域ID。"
      },
      {
        "name": "tags",
        "type": "Json",
        "value": "{\"env\":\"prod\",\"owner\":\"Tomc\"}",
        "allowedValues": [ ],
        "description": "[Required]资源标签（例：{\"k1\":\"v1\",\"k2\":\"v2\"}）。"
      },
      {
        "name": "resourceType",
        "type": "String",
        "value": "{resourceType}",
        "allowedValues": [ ],
        "description": "[Required]资源类型。"
      },
      {
        "name": "resourceIds",
        "type": "List",
        "value": "{resourceId}",
        "allowedValues": [ ],
        "description": "[Required]资源ID。"
      }
    ]
  }
}

resource "alicloud_config_remediation" "tf_requried_tags_remediation" {
  config_rule_id          = alicloud_config_rule.tf_requried_tags_managed_rule.config_rule_id
  remediation_template_id = "ACS-TAG-TagResources"
  remediation_source_type = "ALIYUN"
  invoke_type             = "AUTO_EXECUTION"
  params                  =  jsonencode(var.remediation_required_tags_input_parameters_all)
  remediation_type        = "OOS"
}
