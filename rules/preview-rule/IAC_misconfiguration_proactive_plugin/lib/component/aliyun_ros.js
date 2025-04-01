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
Object.defineProperty(exports, "__esModule", { value: true });
// This file is auto-generated, don't edit it
// 依赖的模块可通过下载工程中的模块依赖文件或右上角的获取 SDK 依赖信息查看
const ros20190910_1 = __importStar(require("@alicloud/ros20190910")), $ROS20190910 = ros20190910_1;
const $OpenApi = __importStar(require("@alicloud/openapi-client"));
const $Util = __importStar(require("@alicloud/tea-util"));
class ROSClient {
    /**
     * @remarks
     * 使用AK&SK初始化账号Client
     * @returns Client
     *
     * @throws Exception
     */
    static createClient(ak, sk) {
        let config = new $OpenApi.Config({
            accessKeyId: ak,
            accessKeySecret: sk,
        });
        // Endpoint 请参考 https://api.aliyun.com/product/ROS
        config.endpoint = `ros.aliyuncs.com`;
        return new ros20190910_1.default(config);
    }
    static getPreviewStack(ak, sk, stackPath) {
        let client = ROSClient.createClient(ak, sk);
        let previewStackRequest = new $ROS20190910.PreviewStackRequest({
            regionId: "cn-shanghai",
            templateBody: stackPath,
            stackName: "tmp",
        });
        let runtime = new $Util.RuntimeOptions({});
        try {
            // 复制代码运行请自行打印 API 的返回值
            client.previewStackWithOptions(previewStackRequest, runtime);
            return "ok";
        }
        catch (error) {
            return "error";
            console.log(error);
        }
    }
}
exports.default = ROSClient;
//# sourceMappingURL=aliyun_ros.js.map