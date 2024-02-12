import boto3
import json


def lambda_handler(event, context):
    s3_client = boto3.client("s3")
    rekognition_client = boto3.client("rekognition")

    # S3 이벤트에서 파일 정보 추출
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    file_name = event["Records"][0]["s3"]["object"]["key"]
    # 파일 이름만 필요한 경우
    file_name_only = file_name.split("/")[-1]

    # S3 오브젝트의 메타데이터 가져오기
    object_metadata = s3_client.head_object(Bucket=bucket_name, Key=file_name)
    user_id = object_metadata.get("Metadata", {}).get("x-amz-meta-user_id")

    # user_id가 없거나 비어있는 경우 기본값 처리
    if not user_id:
        user_id = "default_collection_id"  # 여기서 적절한 기본값 설정

    response = rekognition_client.index_faces(
        CollectionId=user_id,  # 메타데이터에서 읽은 user_id 사용
        Image={"S3Object": {"Bucket": bucket_name, "Name": file_name}},
        ExternalImageId=file_name_only,
        MaxFaces=1,
        QualityFilter="AUTO",
        DetectionAttributes=["ALL"],
    )

    # 데이터베이스에 얼굴 데이터 저장
    # (이 부분은 구현 필요)

    return {"statusCode": 200, "body": json.dumps("Face analysis completed.")}
