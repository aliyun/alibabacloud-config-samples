#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import json
import logging

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.http import protocol_type

"""
该函数周期触发方式为周期执行。
收到周期性触发事件后，查询需要评估的ACK集群列表，遍历集群信息获取集群的节点列表，再遍历节点列表逐个判断是否安装云监控插件，如果节点都已安装云监控插件则视该集群为合规，否则视为不合规。
周期性评估回写评估结果时开启删除无效评估模式，config会自动将本周期产生的评估之外的评估结果进行删除
"""
logger = logging.getLogger()
# 合规类型
COMPLIANCE_TYPE_COMPLIANT = 'COMPLIANT'
COMPLIANCE_TYPE_NON_COMPLIANT = 'NON_COMPLIANT'
COMPLIANCE_TYPE_NOT_APPLICABLE = 'NOT_APPLICABLE'

# Config api endpoint, International sites use ap-southeast-1 and config.ap-southeast-1.aliyuncs.com
CONFIG_SERVICE_REGION = 'cn-shanghai'
CONFIG_SERVICE_ENDPOINT = 'config.cn-shanghai.aliyuncs.com'
AK = '******'
SK = '******'


# 入口方法
def handler(event, context):
    evt = validate_event(event)
    if not evt:
        return None

    result_token = evt.get('resultToken')
    ordering_timestamp = evt.get('orderingTimestamp')
    invoking_event = evt.get('invokingEvent')
    account_id = invoking_event.get('accountId')
    # regionId = invoking_event.get('configurationItem')['regionId']
    client = AcsClient(AK, SK, CONFIG_SERVICE_REGION)
    evaluations = []
    # ResourceType supported by the config
    resource_type = "ACS::ACK::Cluster"
    # 查询集群列表并逐个校验集群检查情况
    page_number = 1
    page_size = 50
    cluster_total = 0
    while page_number == 1 or (cluster_total > page_size * page_number):
        cluster_page_json = query_cluster_page(client, page_size, page_number)
        if "clusters" in cluster_page_json and cluster_page_json["clusters"]:
            for cluster in cluster_page_json["clusters"]:
                logger.info(cluster["cluster_id"])
                compliant_result = query_nodes_evaluation(client, cluster["cluster_id"])
                if compliant_result:
                    evaluation = {
                        'accountId': account_id,
                        'complianceResourceId': cluster["cluster_id"],
                        'complianceResourceType': resource_type,
                        'orderingTimestamp': ordering_timestamp,
                        'complianceType': COMPLIANCE_TYPE_COMPLIANT,
                        'annotation': json.dumps({}),
                        'complianceRegionId': cluster["region_id"]
                    }
                    evaluations.append(evaluation)
                else:
                    evaluation = {
                        'accountId': account_id,
                        'complianceResourceId': cluster["cluster_id"],
                        'complianceResourceType': resource_type,
                        'orderingTimestamp': ordering_timestamp,
                        'complianceType': COMPLIANCE_TYPE_NON_COMPLIANT,
                        'annotation': json.dumps(
                            {'configuration': 'Not all nodes installed monitor agent.',
                             'desiredValue': 'All nodes installed monitor agent.'}),
                        'complianceRegionId': cluster["region_id"]
                    }
                    evaluations.append(evaluation)
        else:
            break

        page_number = page_number + 1
        if "page_info" in cluster_page_json and cluster_page_json["page_info"] and "total_count" \
                in cluster_page_json["page_info"] and cluster_page_json["page_info"]["total_count"]:
            cluster_total = cluster_page_json["page_info"]["total_count"]

    put_evaluations(context, result_token, evaluations)
    return evaluations


def query_cluster_page(clt, page_size, page_number):
    request = CommonRequest(
        'cs.aliyuncs.com',
        '2015-12-15',
        uri_pattern='/api/v1/clusters'
    )
    request.add_query_param('page_size', page_size)
    request.add_query_param('page_number', page_number)
    response = clt.do_action_with_exception(request)
    res = str(response, encoding='utf-8')
    json_res = json.loads(res)
    return json_res


# 查询集群节点列表，并校验是否全部安装云监控插件且状态为运行中
def query_nodes_evaluation(clt, cluster_id):
    compliance_result = True
    page_number = 1
    page_size = 50
    cluster_total = 0
    while page_number == 1 or (cluster_total > page_size * page_number):
        request = CommonRequest(
            'cs.aliyuncs.com',
            '2015-12-15',
            uri_pattern='/clusters/' + cluster_id + '/nodes'
        )
        request.set_protocol_type(protocol_type.HTTPS)
        request.add_query_param('pageSize', page_size)
        request.add_query_param('pageNumber', page_number)
        response = clt.do_action_with_exception(request)
        res = str(response, encoding='utf-8')
        json_res = json.loads(res)

        instance_id_set = set()
        if "nodes" in json_res and json_res["nodes"]:
            for node in json_res["nodes"]:
                instance_id_set.add(node["instance_id"])
            compliance_result = query_instances_monitor_status(clt, instance_id_set)
            if not compliance_result:
                return compliance_result
        else:
            break

        page_number = page_number + 1
        if "page" in json_res and json_res["page"] and "total_count" in json_res["page"] and \
                json_res["page"]["total_count"]:
            cluster_total = json_res["page"]["total_count"]
    return compliance_result


# 批量查询实例列表云监控插件状态是否全为运行中
def query_instances_monitor_status(clt, instance_id_set):
    compliance_result = True
    instance_id_str = ",".join(instance_id_set)
    request = CommonRequest()
    request.set_protocol_type(protocol_type.HTTPS)
    request.set_domain('metrics.aliyuncs.com')
    request.set_version('2019-01-01')
    request.set_action_name('DescribeMonitoringAgentStatuses')
    request.set_method('GET')
    request.add_query_param('InstanceIds', instance_id_str)
    response = clt.do_action_with_exception(request)
    res = str(response, encoding='utf-8')
    json_res = json.loads(res)
    if "NodeStatusList" in json_res and json_res["NodeStatusList"] and "NodeStatus" in json_res["NodeStatusList"] and \
            json_res["NodeStatusList"]["NodeStatus"]:
        if len(json_res["NodeStatusList"]["NodeStatus"]) != len(instance_id_set):
            logger.warn('Query monitor list len not equal input: {}'.format(instance_id_str))
            compliance_result = False
        else:
            for status in json_res["NodeStatusList"]["NodeStatus"]:
                if status["Status"] != "running":
                    compliance_result = False
                    break
    else:
        compliance_result = False
    return compliance_result


def validate_event(event):
    if not event:
        logger.error('Event is empty.')
    evt = parse_json(event)
    logger.info('Loading event: %s .' % evt)

    if 'resultToken' not in evt:
        logger.error('ResultToken is empty.')
        return None
    if 'ruleParameters' not in evt:
        logger.error('RuleParameters is empty.')
        return None
    if 'invokingEvent' not in evt:
        logger.error('InvokingEvent is empty.')
        return None
    return evt


def parse_json(content):
    try:
        return json.loads(content)
    except Exception as e:
        logger.error('Parse content:{} to json error:{}.'.format(content, e))
        return None


def put_evaluations(context, result_token, evaluations):
    client = AcsClient(AK, SK, CONFIG_SERVICE_REGION)

    request = CommonRequest()
    request.set_domain(CONFIG_SERVICE_ENDPOINT)
    request.set_version('2019-01-08')
    request.set_action_name('PutEvaluations')
    request.add_body_params('ResultToken', result_token)
    request.add_body_params('Evaluations', evaluations)
    # 开启删除模式，config会自动删除非本周期内评估的记录
    request.add_body_params('DeleteMode', True)
    request.set_method('POST')

    try:
        response = client.do_action_with_exception(request)
        logger.info('PutEvaluations with request: {}, response: {}.'.format(request, response))
    except Exception as e:
        logger.error('PutEvaluations error: %s' % e)

