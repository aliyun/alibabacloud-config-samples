> # Aliyun Config Python Samples

- This repo provides samples for config customer feature, it will help you to deploy rules and remediation more quickly.
-

## Prerequisite

* Enable [Aliyun Config](https://help.aliyun.com/document_detail/213747.html) and finished resource monitor.
* Prepare the AK&SK with AliyunConfigFullAccess.
* Install Python SDK .

## Features

see more [managed rules](https://help.aliyun.com/document_detail/127404.html)

<table>
    <thead>
      <tr>
         <th>Topic</th>
         <th>Sample</th>
        </tr>
    </thead>
    <tbody>
        <tr>
         <td>customer-api-sample</td>
          <td>apis/open_api_sign.py</td>
        </tr>
        <tr>
            <td>customer-rule-sample</td>
            <td>rules/ack_cluster_node_monitor_enabled.py</td>
        </tr>
        <tr>
            <td>customer-remediation-sample</td>
            <td>remediation/aliyun-config-remediation.py</td>
        </tr>
    </tbody>
</table>

## Run and Deploy

### call apis by http client

```
python apis/open_api_sign.py
```

### debug fc function and deploy

debug the handler

```
python rules/vpc_flow_logs_enabled.py
```
