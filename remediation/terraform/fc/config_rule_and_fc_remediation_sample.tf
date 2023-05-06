variable "access_key" {
	default = "xxx"
}
variable "secret_key" {
	default = "xxx"
}

terraform {
  required_providers {
    alicloud = {
      source  = "hashicorp/alicloud"
      version = ">= 1.204.0"
    }
  }
}

provider "alicloud" {
	region     = "cn-shanghai"
	access_key = "${var.access_key}"
	secret_key = "${var.secret_key}"
    # security_token = "${var.security_token}"
}

data "alicloud_account" "current" {
}

variable "function_name" {
  default = "aliyun-config-remediation-kms-tags"
}

resource "alicloud_fc_service" "fc_service" {
  name        = var.function_name
}

resource "alicloud_fc_function" "function" {
  service     = alicloud_fc_service.fc_service.name
  name        = var.function_name
  description = "tf"
  filename  = "sample.zip"
  memory_size = "512"
  runtime = "python3.9"
  handler     = "index.handler"
  environment_variables = {
                    "ALIBABA_CLOUD_ACCESS_KEY_ID": "${var.access_key}"
                    "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "${var.secret_key}"
                    # "ALIBABA_CLOUD_SECURITY_TOKEN":"${var.security_token}"
  }
}

variable "rule_required_tags_input_parameters" {
  type        = map
  description = ""
  default = {
      "tag1Key":"app_id",
      "tag1Value": "200345",
      "tag2Key": "app_name",
      "tag2Value": "name",
      "tag3Key": "env",
      "tag3Value": "dev",
      "tag4Key": "owner_div",
      "tag4Value": "054",
      "tag5Key": "owner_dept",
      "tag5Value": "0645"
  }
}

variable "rule_required_tags_resource_types_scope" {
  type        = list
  description = ""
  default =[
    "ACS::KMS::Key",
    "ACS::KMS::Secret",
  ]
}

resource "alicloud_config_rule" "tf_requried_tags_managed_rule" {
  description                = "tf-fc-rule-by-required-tags"
  source_owner               = "ALIYUN"
  source_identifier          = "required-tags"
  risk_level                 = 1
  config_rule_trigger_types  = "ConfigurationItemChangeNotification"
  resource_types_scope = var.rule_required_tags_resource_types_scope
  rule_name = "tf-fc-rule-by-required-tags"
  input_parameters = var.rule_required_tags_input_parameters
}

resource "alicloud_config_remediation" "tf_requried_tags_remediation" {
  config_rule_id          = alicloud_config_rule.tf_requried_tags_managed_rule.config_rule_id
  remediation_template_id = "acs:fc:cn-shanghai:${data.alicloud_account.current.id}:services/${alicloud_fc_service.fc_service.name}.LATEST/functions/${alicloud_fc_function.function.name}"
  remediation_source_type = "CUSTOM"
  invoke_type             = "AUTO_EXECUTION"
  params                  =  "{}"
  remediation_type        = "FC"
}
