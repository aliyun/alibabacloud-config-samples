export declare class IParams {
    pipelineID: number;
    pipelineName: string;
    buildNumber?: number;
    workSpace: string;
    projectDir: string;
    buildJobID: number;
}
export declare function getParams(): IParams;
