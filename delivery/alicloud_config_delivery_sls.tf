terraform {
  required_providers {
    alicloud = {
      source  = "hashicorp/alicloud"
      version = ">= 1.204.0"
    }
  }
}

variable "access_key" {
	default = "this is ak"
}
variable "secret_key" {
	default = "this is sk"
}
variable "region_id" {
  # The Cloud Config region support cn-shanghai(cn) and ap-southeast-1(intl).
  default="ap-southeast-1"
}

provider "alicloud" {
	region     = "${var.region_id}"
	access_key = "${var.access_key}"
	secret_key = "${var.secret_key}"
}

resource "alicloud_log_project" "this" {
  name        = "tf-config-log-project"
  description = "created by terraform"

}

resource "alicloud_log_store" "this" {
  name    = "tf-config-log-store"
  project = alicloud_log_project.this.name
}

data "alicloud_account" "this" {}

resource "alicloud_config_delivery" "delivery_intl_sls" {
  configuration_item_change_notification = true
  non_compliant_notification             = true
  delivery_channel_name                  = "config_devliery_sls"
  delivery_channel_target_arn            = "acs:log:${var.region_id}:${data.alicloud_account.this.id}:project/${alicloud_log_project.this.name}/logstore/${alicloud_log_store.this.name}"
  delivery_channel_type                  = "SLS"
  description                            = "config devliery sls"
}
