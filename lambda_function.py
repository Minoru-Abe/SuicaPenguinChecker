import boto3

ECS_CLUSTER = "suica-checker"
TASK_DEFINITION = "suica-checker:1"
SUBNET_ID = "subnet-0733f3ee9cb89f00c"
REGION = "ap-northeast-1"


def handler(event, context):
    ecs = boto3.client("ecs", region_name=REGION)
    resp = ecs.run_task(
        cluster=ECS_CLUSTER,
        taskDefinition=TASK_DEFINITION,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": [SUBNET_ID],
                "assignPublicIp": "ENABLED",
            }
        },
    )
    task_arn = resp["tasks"][0]["taskArn"] if resp["tasks"] else None
    print(f"[started] taskArn={task_arn}")
    return {"taskArn": task_arn}
