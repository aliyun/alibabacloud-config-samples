#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import uuid
import datetime
import hmac
import base64
from urllib.parse import quote
import hashlib
import requests
import ssl
import warnings


warnings.filterwarnings("ignore")
ssl._create_default_https_context = ssl._create_unverified_context()


def params_info(access_key, api_version):
    public_param = {
        "Format": "JSON",
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "Version": api_version,
        "AccessKeyId": access_key
    }
    return public_param


def sign(public_params, http_method, accesskey_secret):
    public_param = public_params
    format_time = '%Y-%m-%dT%H:%M:%SZ'
    utctime = datetime.datetime.utcnow().strftime(format_time)
    signature_nonce = str(uuid.uuid1())
    public_param['SignatureNonce'] = signature_nonce
    public_param['Timestamp'] = utctime
    sort_all_params = list()
    for key, value in public_param.items():
        all_params = key + '=' + str(value)
        sort_all_params.append(all_params)
    sort_all_params.sort()
    for i in range(len(sort_all_params)):
        if 'NextToken' in sort_all_params[i]:
            continue
        sort_all_params[i] = quote(sort_all_params[i], '=')
        # tmp = sort_all_params[i]
        if sort_all_params[i].find('+'):
            sort_all_params[i].replace('+', '%20')
        elif sort_all_params[i].find('*'):
            sort_all_params[i].replace('*', '%2A')
        elif sort_all_params[i].find('%7E'):
            sort_all_params[i].replace('%7E', '~')

    # print(sort_all_params)
    str_to_sign = ''
    for i in range(len(sort_all_params)):
        str_to_sign = str_to_sign + sort_all_params[i] + '&'
    str_to_sign = http_method + '&%2F&' + quote(str_to_sign[:-1])
    # print(str_to_sign)
    key = accesskey_secret + '&'
    signature = hmac.new(key.encode('utf-8'), str_to_sign.encode('utf-8'), digestmod=hashlib.sha1)
    signature = base64.b64encode(signature.digest()).decode()
    # print(signature)
    # 解决签名中包含有'+'的特殊情况
    signature = list(signature)
    for i in range(len(signature)):
        if signature[i] == '+':
            signature[i] = '%2B'
    new_signature = ''.join(signature)
    public_param['Signature'] = new_signature

    return public_param


def request_url(public_param, domain):
    draft_url = ''
    for k, v in public_param.items():
        draft_url += f'&{k}={v}'
    draft_url = draft_url[1:]
    url = domain + draft_url

    return url


def post_request(latest_url):
    response = requests.post(latest_url, verify=False)
    response_json = response.json()
    return response_json


def get_request(latest_url):
    response = requests.get(latest_url, verify=False)
    response_json = response.json()
    return response_json


if __name__ == '__main__':
    AK = 'this is ak'
    SK = 'this is sk'
    config_api_version = '2019-01-08'
    config_api_domain = 'https://config.cn-shanghai.aliyuncs.com/?'
    params = params_info(AK, config_api_version)
    params.update({
        'Action': 'ListConfigRules'
    })
    # sign
    sig_params = sign(params, 'GET', SK)

    # get url
    url = request_url(sig_params, config_api_domain)

    # call
    res = get_request(url)
    print(res)