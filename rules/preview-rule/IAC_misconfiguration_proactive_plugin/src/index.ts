import * as step from '@flow-step/step-toolkit'
import process from 'process'
import { convertToUpperCase, getProactiveRules, getResourceType } from './util'
import { getParams } from './params'
import ROS20190910, * as $ROS20190910 from '@alicloud/ros20190910';
import OpenApi, * as $OpenApi from '@alicloud/openapi-client';
import Util, * as $Util from '@alicloud/tea-util';
import fs from 'fs/promises';
import path from 'path';
import { PreviewStackResponseBodyStackResources } from '@alicloud/ros20190910';
import Config20200907, * as $Config20200907 from '@alicloud/config20200907';
import { time } from 'console';


async function runStep(): Promise<void> {
    const params = getParams()
    step.info(`PIPELINE_ID=${params.pipelineID}`)
    step.info(`PIPELINE_NAME=${params.pipelineName}`)
    step.info(`BUILD_NUMBER=${params.buildNumber}`)
    step.info(`WORK_SPACE=${params.workSpace}`)
    step.info(`PROJECT_DIR=${params.projectDir}`)
    step.info(`BUILD_JOB_ID=${params.buildJobID}`)

    step.info(`Init cloudconfig proactive...`)
    // console.log('process.env', process.env);

    const stackPath = process.env["StackPath"] as string
    step.info(`stackPath=${stackPath}`)

    const regionId = process.env["RegionId"] as string
    step.info(`regionId=${regionId}`)

    const enableEvaluate = process.env["EnableEvaluate"] as string
    step.info(`enableEvaluate=${enableEvaluate}`)

    const ak = process.env["AccessKey"] as string
    const sk = process.env["AccessSecret"] as string

    const sourceCode = await getCodeFileContent(stackPath)
    console.log(`sourceCode=${sourceCode}`)

    let apiConfig = newClientConfig(ak, sk);
    const stackRespone = await getPreviewStack(apiConfig, sourceCode);
    step.info(`stackProperties response=${stackRespone}`)

    for (const resource of stackRespone) {
        const resourceJson = JSON.stringify(resource)
        step.info(`one begin scan resourceJson =${resourceJson}`)

        let resourceTypeSpec = resource.acsResourceType || ''
        step.info(`one resourceTypeSpec =${resourceTypeSpec}`)

        if (resourceTypeSpec === '') {
            resourceTypeSpec = getResourceType(resource.resourceType || '');
            step.info(`one resourceTypeSpec by ros type =${resourceTypeSpec}`)
        }

        const proactiveRules = getProactiveRules(resourceTypeSpec)
        step.info(`one proactiveRules =${proactiveRules}`)

        const resourceProperties = resource.properties || ''
        const resourcePropertiesJson = JSON.stringify(resourceProperties);
        step.info(`one resourceProperties =${resourcePropertiesJson}`)

        const result = await evaluateOneResourcePreRules(apiConfig, resourceTypeSpec, proactiveRules, resourcePropertiesJson)
        step.info(`one evaluatePreRules =${JSON.stringify(result)}`)
        result.body?.resourceEvaluations?.forEach(element => {
            step.info(`one evaluatePreRules element =${JSON.stringify(element)}`)
            
            let rules = element.rules || []
            rules.forEach(rule => {
                let identifier = rule.identifier
                let complianceType = rule.complianceType
                let annotation = rule.annotation
                if(complianceType === 'NON_COMPLIANT') {
                    step.error(`evaluatePreRules noncompliant; reason:" ${identifier},${JSON.stringify(annotation)} `);
                    return ;
                }
            })

        });
    }
}

/**
 * 跟进文件名称解析iac文件内容，识别ros的资源stack
 * @param fileName 
 * @returns 
 */
async function getCodeFileContent(fileName: string): Promise<string> {
    const filePath = path.join(process.env['PROJECT_DIR'] as string, fileName);
    return fs.readFile(filePath, 'utf-8');
}

/**
 * https://next.api.aliyun.com/api/ROS/2019-09-10/PreviewStack
 * 获取priviewstack，通过templateBody，解析config识别的预检属性
 * @param ak 
 * @param sk 
 * @param templateBody 
 * @returns 
 */

function newClientConfig(ak:string, sk:string): $OpenApi.Config{
    let config = new $OpenApi.Config({
        accessKeyId: ak,
        accessKeySecret: sk,
    });
    return config;
}
async function getPreviewStack(config: $OpenApi.Config, templateBody: string): Promise<PreviewStackResponseBodyStackResources[]> {
    config.endpoint = `ros.aliyuncs.com`;

    let client = new ROS20190910(config);
    let previewStackRequest = new $ROS20190910.PreviewStackRequest({
        regionId: "cn-shanghai",
        templateBody: templateBody,
        stackName: "tmp",
    });
    let runtime = new $Util.RuntimeOptions({});
    try {
        const statckResponse = await client.previewStackWithOptions(previewStackRequest, runtime);
        step.info(`PreviewStackResponse result=${statckResponse}`)
        return statckResponse.body?.stack?.resources || [];
    } catch (error) {
        step.info(`stackProperties error=${error}`)
        return [];
    }
}

/**
 * https://next.api.aliyun.com/api/Config/2020-09-07/EvaluatePreConfigRules
 * @param ak 
 * @param sk 
 * @param resourceType 
 * @param resourceRules 
 * @param resourceProperties 
 * @returns 
 */
async function evaluateOneResourcePreRules(config: $OpenApi.Config, resourceType: string, resourceRules: Array<string>, resourceProperties: string):Promise<$Config20200907.EvaluatePreConfigRulesResponse> {
    config.endpoint = `config.cn-shanghai.aliyuncs.com`;
    let client = new Config20200907(config);

    let rules = new Array<$Config20200907.EvaluatePreConfigRulesRequestResourceEvaluateItemsRules>();
    for (const rule of resourceRules) {
        let one = new $Config20200907.EvaluatePreConfigRulesRequestResourceEvaluateItemsRules({
            identifier: rule,
        });
        rules.push(one);
    }

    let resourceEvaluateItems0 = new $Config20200907.EvaluatePreConfigRulesRequestResourceEvaluateItems({
        resourceLogicalId: "",
        resourceType: resourceType,
        rules: rules,
        resourceProperties: resourceProperties
    });

    let evaluatePreConfigRulesRequest = new $Config20200907.EvaluatePreConfigRulesRequest({
        resourceTypeFormat: "ros",
        resourceEvaluateItems: [
            resourceEvaluateItems0
        ],
    });
    let runtime = new $Util.RuntimeOptions({});
    let result = await client.evaluatePreConfigRulesWithOptions(evaluatePreConfigRulesRequest, runtime);
    step.info(`evaluatePreRules result=${JSON.stringify(result)}`)
    return result;
}

runStep()
    .then(function () {
        step.success('run step successfully!')
    })
    .catch(function (err: Error) {
        step.error(err.message)
        process.exit(-1)
    })
