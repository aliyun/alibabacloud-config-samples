import ROS20190910 from '@alicloud/ros20190910';
export default class ROSClient {
    /**
     * @remarks
     * 使用AK&SK初始化账号Client
     * @returns Client
     *
     * @throws Exception
     */
    static createClient(ak: string, sk: string): ROS20190910;
    static getPreviewStack(ak: string, sk: string, stackPath: string): string;
}
