"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getParams = exports.IParams = void 0;
const process_1 = __importDefault(require("process"));
class IParams {
}
exports.IParams = IParams;
function getParams() {
    let params = new IParams();
    params.pipelineID = Number(process_1.default.env.PIPELINE_ID);
    params.pipelineName = process_1.default.env.PIPELINE_NAME;
    params.buildNumber = Number(process_1.default.env.BUILD_NUMBER);
    params.workSpace = process_1.default.env.WORK_SPACE;
    params.projectDir = process_1.default.env.PROJECT_DIR;
    params.buildJobID = Number(process_1.default.env.BUILD_JOB_ID);
    return params;
}
exports.getParams = getParams;
//# sourceMappingURL=params.js.map