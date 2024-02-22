import json
import os
from typing import Annotated
import logging


from transformers import (
    AutoTokenizer,
    AutoModel,
)
import requests
import boto3
from botocore.exceptions import ClientError
from pymongo import MongoClient
from pymongo.collection import Collection
from fastapi import FastAPI, File, Form
from fastapi.middleware.cors import CORSMiddleware

from utils import (
    get_secret,
    get_sentence_embedding,
    download_pem_file,
    get_similar_docs,
    load_model_and_tokenizer,
)


os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./.cache"


logger = logging.getLogger()
logger.setLevel(logging.INFO)


session = boto3.Session()
rekognition = session.client("rekognition")
mysql_config = get_secret(os.environ["MYSQL_SECRET_NAME"])

db = mysql.connector.connect(
    host=mysql_config["host"],
    user=mysql_config["username"],
    password=mysql_config["password"],
    database="app",
)
logger.info("Connected to the database.")

secret = get_secret(os.environ["MONGO_SECRET_NAME"])
logger.info("Got the secret from Secrets Manager.")

if download_pem_file():
    logger.info("Downloaded the global-bundle.pem file.")
else:
    raise Exception("Failed to download the global-bundle.pem file.")

mongo_client = MongoClient(
    f"mongodb://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
)
mongo_db = mongo_client.image_metadata
mongo_collection = mongo_db.caption_vector
logger.info("Connected to the MongoDB.")


model, tokenizer = load_model_and_tokenizer()
logger.info("Loaded the model and tokenizer.")

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/search/semantic")
async def search_semantic(
    query: Annotated[str, Form()], user_id: Annotated[str, Form()]
):
    try:
        results = get_similar_docs(mongo_collection, query, user_id)
        file_names = []
        captions = {}

        for result in results:
            file_name = result["image_url"]
            file_names.append(file_name)
            captions[file_name] = result["caption"]

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            f"SELECT * FROM Pictures WHERE image_url IN ({','.join(['%s'] * len(file_names))})",
        )
        query_results = cursor.fetchall()

        for result in query_results:
            result["caption"] = captions[result["image_url"]]

        return {"result": query_results}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


@app.post("/search/faces")
async def search_faces(file: Annotated[bytes, File()], user_id: Annotated[str, Form()]):
    try:
        cursor = None
        response = rekognition.search_faces_by_image(
            CollectionId=user_id,
            Image={"Bytes": file},
            MaxFaces=20,
            FaceMatchThreshold=90,
        )
        face_matches = response["FaceMatches"]

        if not face_matches:
            return {"result": []}

        picture_urls: list[str] = [
            match["Face"]["ExternalImageId"] for match in face_matches
        ]

        logger.info(
            f"Found {len(picture_urls)} matches in Rekognition.: {picture_urls}"
        )

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            f"SELECT * FROM Pictures WHERE image_url IN ({','.join(['%s'] * len(picture_urls))})",
            picture_urls,
        )
        query_result = cursor.fetchall()

        if not query_result:
            raise Exception("Found results in Rekognition but not in the database.")

        for result in query_result:
            result["created_at"] = result["create_at"]
            result.pop("create_at")

        return {"result": query_result}

    except rekognition.exceptions.InvalidParameterException as e:
        return {"error": str(e), "error_type": "InvalidParameterException"}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}
    finally:
        if cursor:
            cursor.close()


@app.get("/search/faces/health_check")
async def health_check():
    return {"status": 200}
