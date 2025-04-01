export function convertToUpperCase(str: string): string {
    return str.toUpperCase();
}

const resourceTypeMap: Map<string, string> = new Map();
resourceTypeMap.set("ALIYUN::ECS::SecurityGroup", "ACS::ECS::SecurityGroup");
resourceTypeMap.set("ALIYUN::ECS::Instance", "ACS::ECS::Instance");
resourceTypeMap.set("ALIYUN::SLS::LogStore", "ACS::SLS::LogStore");
resourceTypeMap.set("ALIYUN::OSS::Bucket", "ACS::OSS::Bucket");

export function getResourceType(resourceType: string): string {
    return resourceTypeMap.get(resourceType) || resourceType;
}

export function getProactiveRules(resourceType: string): Array<string> {
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


