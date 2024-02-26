import os
import requests
from pymongo import MongoClient

from utils import (
    get_secret
)


def download_pem_file() -> bool:
    # URL에서 파일을 가져옵니다.
    response = requests.get(
        os.environ["GLOBAL_BUNDLE_URL"],
    )
    # HTTP 요청이 성공했는지 확인합니다 (상태 코드 200).
    if response.status_code == 200:
        # 파일을 쓰기 모드로 열고 내용을 기록합니다.
        with open("global-bundle.pem", "wb") as file:
            file.write(response.content)
        return True
    else:
        return False


def get_mongo_db() -> MongoClient:
    secret = get_secret(os.environ["MONGO_SECRET_NAME"])
    if not download_pem_file():
        raise Exception("Failed to download the global-bundle.pem file.")

    return  MongoClient(
        f"mongodb://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
    )
