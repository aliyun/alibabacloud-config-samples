## How to deploy customer remediation by terraform

### 1.create function sample.zip
```
cd remediation/terraform/fc
sh zip-sample.sh fc_function_for_kms_tag.py

```
### 2. terraform create resource
```
terraform init
terraform plan
terraform apply
```

### 3. goto fc console debug your code

https://fcnext.console.aliyun.com/cn-shanghai/services/aliyun-config-remediation-kms-tags/function-detail/aliyun-config-remediation-kms-tags/LATEST?tab=code