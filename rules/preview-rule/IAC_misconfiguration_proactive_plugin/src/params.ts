import process from 'process'

export class IParams {
    pipelineID!: number

    pipelineName!: string

    buildNumber?: number

    workSpace!: string

    projectDir!: string

    buildJobID!: number
}

export function getParams(): IParams {
    let params = new IParams()
    params.pipelineID = Number(process.env.PIPELINE_ID)
    params.pipelineName = process.env.PIPELINE_NAME as string
    params.buildNumber = Number(process.env.BUILD_NUMBER)
    params.workSpace = process.env.WORK_SPACE as string
    params.projectDir = process.env.PROJECT_DIR as string
    params.buildJobID = Number(process.env.BUILD_JOB_ID)
    return params
}