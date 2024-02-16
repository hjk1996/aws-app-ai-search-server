import json
from typing import Annotated
import logging


import boto3
from fastapi import FastAPI, File, Form
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

from utils import get_secret


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


session = boto3.Session()
rekognition = session.client("rekognition")
mysql_config = get_secret()

db = mysql.connector.connect(
    host=mysql_config["host"],
    user=mysql_config["username"],
    password=mysql_config["password"],
    database="app",
)

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

        picture_urls: list[str] = [match["Face"]["ExternalImageId"] for match in face_matches]
        
        logger.info(f"Found {len(picture_urls)} matches in Rekognition.: {picture_urls}")
        
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
