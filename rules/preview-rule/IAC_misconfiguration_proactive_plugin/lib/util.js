"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getProactiveRules = exports.getResourceType = exports.convertToUpperCase = void 0;
function convertToUpperCase(str) {
    return str.toUpperCase();
}
exports.convertToUpperCase = convertToUpperCase;
const resourceTypeMap = new Map();
resourceTypeMap.set("ALIYUN::ECS::SecurityGroup", "ACS::ECS::SecurityGroup");
resourceTypeMap.set("ALIYUN::ECS::Instance", "ACS::ECS::Instance");
resourceTypeMap.set("ALIYUN::SLS::LogStore", "ACS::SLS::LogStore");
resourceTypeMap.set("ALIYUN::OSS::Bucket", "ACS::OSS::Bucket");
function getResourceType(resourceType) {
    return resourceTypeMap.get(resourceType) || resourceType;
}
exports.getResourceType = getResourceType;
function getProactiveRules(resourceType) {
    switch (resourceType) {
        case "ALIYUN::ECS::Instance":
            return [
                "ecs-instance-os-name-check"
            ];
        case "ACS::OSS::Bucket":
            return [
                "oss-bucket-logging-enabled",
                "oss-bucket-server-side-encryption-enabled",
                "oss-bucket-public-write-prohibited",
            ];
        default:
            return [];
    }
}
exports.getProactiveRules = getProactiveRules;
//# sourceMappingURL=util.js.map