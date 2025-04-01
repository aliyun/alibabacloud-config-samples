"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const step = __importStar(require("@flow-step/step-toolkit"));
const process_1 = __importDefault(require("process"));
const util_1 = require("./util");
const params_1 = require("./params");
const ros20190910_1 = __importStar(require("@alicloud/ros20190910")), $ROS20190910 = ros20190910_1;
const $OpenApi = __importStar(require("@alicloud/openapi-client"));
const $Util = __importStar(require("@alicloud/tea-util"));
const promises_1 = __importDefault(require("fs/promises"));
const path_1 = __importDefault(require("path"));
const config20200907_1 = __importStar(require("@alicloud/config20200907")), $Config20200907 = config20200907_1;
function runStep() {
    var _a, _b;
    return __awaiter(this, void 0, void 0, function* () {
        const params = (0, params_1.getParams)();
        step.info(`PIPELINE_ID=${params.pipelineID}`);
        step.info(`PIPELINE_NAME=${params.pipelineName}`);
        step.info(`BUILD_NUMBER=${params.buildNumber}`);
        step.info(`WORK_SPACE=${params.workSpace}`);
        step.info(`PROJECT_DIR=${params.projectDir}`);
        step.info(`BUILD_JOB_ID=${params.buildJobID}`);
        step.info(`Init cloudconfig proactive...`);
        // console.log('process.env', process.env);
        const stackPath = process_1.default.env["StackPath"];
        step.info(`stackPath=${stackPath}`);
        const regionId = process_1.default.env["RegionId"];
        step.info(`regionId=${regionId}`);
        const enableEvaluate = process_1.default.env["EnableEvaluate"];
        step.info(`enableEvaluate=${enableEvaluate}`);
        const ak = process_1.default.env["AccessKey"];
        const sk = process_1.default.env["AccessSecret"];
        const sourceCode = yield getCodeFileContent(stackPath);
        console.log(`sourceCode=${sourceCode}`);
        let apiConfig = newClientConfig(ak, sk);
        const stackRespone = yield getPreviewStack(apiConfig, sourceCode);
        step.info(`stackProperties response=${stackRespone}`);
        for (const resource of stackRespone) {
            const resourceJson = JSON.stringify(resource);
            step.info(`one begin scan resourceJson =${resourceJson}`);
            let resourceTypeSpec = resource.acsResourceType || '';
            step.info(`one resourceTypeSpec =${resourceTypeSpec}`);
            if (resourceTypeSpec === '') {
                resourceTypeSpec = (0, util_1.getResourceType)(resource.resourceType || '');
                step.info(`one resourceTypeSpec by ros type =${resourceTypeSpec}`);
            }
            const proactiveRules = (0, util_1.getProactiveRules)(resourceTypeSpec);
            step.info(`one proactiveRules =${proactiveRules}`);
            const resourceProperties = resource.properties || '';
            const resourcePropertiesJson = JSON.stringify(resourceProperties);
            step.info(`one resourceProperties =${resourcePropertiesJson}`);
            const result = yield evaluateOneResourcePreRules(apiConfig, resourceTypeSpec, proactiveRules, resourcePropertiesJson);
            step.info(`one evaluatePreRules =${JSON.stringify(result)}`);
            (_b = (_a = result.body) === null || _a === void 0 ? void 0 : _a.resourceEvaluations) === null || _b === void 0 ? void 0 : _b.forEach(element => {
                step.info(`one evaluatePreRules element =${JSON.stringify(element)}`);
                let rules = element.rules || [];
                rules.forEach(rule => {
                    let identifier = rule.identifier;
                    let complianceType = rule.complianceType;
                    let annotation = rule.annotation;
                    if (complianceType === 'NON_COMPLIANT') {
                        step.error(`evaluatePreRules noncompliant; reason:" ${identifier},${JSON.stringify(annotation)} `);
                        return;
                    }
                });
            });
        }
    });
}
/**
 * 跟进文件名称解析iac文件内容，识别ros的资源stack
 * @param fileName
 * @returns
 */
function getCodeFileContent(fileName) {
    return __awaiter(this, void 0, void 0, function* () {
        const filePath = path_1.default.join(process_1.default.env['PROJECT_DIR'], fileName);
        return promises_1.default.readFile(filePath, 'utf-8');
    });
}
/**
 * https://next.api.aliyun.com/api/ROS/2019-09-10/PreviewStack
 * 获取priviewstack，通过templateBody，解析config识别的预检属性
 * @param ak
 * @param sk
 * @param templateBody
 * @returns
 */
function newClientConfig(ak, sk) {
    let config = new $OpenApi.Config({
        accessKeyId: ak,
        accessKeySecret: sk,
    });
    return config;
}
function getPreviewStack(config, templateBody) {
    var _a, _b;
    return __awaiter(this, void 0, void 0, function* () {
        config.endpoint = `ros.aliyuncs.com`;
        let client = new ros20190910_1.default(config);
        let previewStackRequest = new $ROS20190910.PreviewStackRequest({
            regionId: "cn-shanghai",
            templateBody: templateBody,
            stackName: "tmp",
        });
        let runtime = new $Util.RuntimeOptions({});
        try {
            const statckResponse = yield client.previewStackWithOptions(previewStackRequest, runtime);
            step.info(`PreviewStackResponse result=${statckResponse}`);
            return ((_b = (_a = statckResponse.body) === null || _a === void 0 ? void 0 : _a.stack) === null || _b === void 0 ? void 0 : _b.resources) || [];
        }
        catch (error) {
            step.info(`stackProperties error=${error}`);
            return [];
        }
    });
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
function evaluateOneResourcePreRules(config, resourceType, resourceRules, resourceProperties) {
    return __awaiter(this, void 0, void 0, function* () {
        config.endpoint = `config.cn-shanghai.aliyuncs.com`;
        let client = new config20200907_1.default(config);
        let rules = new Array();
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
        let result = yield client.evaluatePreConfigRulesWithOptions(evaluatePreConfigRulesRequest, runtime);
        step.info(`evaluatePreRules result=${JSON.stringify(result)}`);
        return result;
    });
}
runStep()
    .then(function () {
    step.success('run step successfully!');
})
    .catch(function (err) {
    step.error(err.message);
    process_1.default.exit(-1);
});
//# sourceMappingURL=index.js.map