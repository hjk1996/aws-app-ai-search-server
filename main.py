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
from fastapi import FastAPI, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

from middlewares import AuthMiddleware
from db import get_db, get_mongo_db
from utils import (
    get_secret,
    get_sentence_embedding,
    download_pem_file,
    get_similar_docs,
    load_model_and_tokenizer,
)


os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./.cache"

K_VALUE = int(os.environ.get("K", 20))
EF_SEAERCH = int(os.environ.get("EF_SEARCH", 200))


logger = logging.getLogger()
logger.setLevel(logging.INFO)


session = boto3.Session()
rekognition = session.client("rekognition")
db = get_db()
logger.info("Connected to the database.")


mongo_client = get_mongo_db()
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
app.add_middleware(AuthMiddleware, jwks_url=os.environ["JWKS_URL"])


@app.get("/search/semantic")
async def search_semantic(request: Request,  query: str):
    try:
        user_id = request.state.user["user_id"]
        results = get_similar_docs(
            mongo_collection, query, user_id, k=K_VALUE, efSearch=EF_SEAERCH
        )
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
async def search_faces(request: Request, file: Annotated[bytes, File()]):
    try:
        user_id = request.state.user["user_id"]
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
