import os
from typing import Annotated
import logging


from transformers import (
    AutoTokenizer,
    AutoModel,
)
import boto3

from fastapi import FastAPI, File, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request, File, UploadFile

from middlewares import AuthMiddleware
from db import get_db, get_mongo_db
from utils import (
    get_similar_docs,
    load_model_and_tokenizer,
)


os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./.cache"

K_VALUE = int(os.environ.get("K", 20))
EF_SEARCH = int(os.environ.get("EF_SEARCH", 200))


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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware, jwks_url=os.environ["JWKS_URL"])


@app.post("/search/semantic/reset", status_code=200)
async def reset_caption(request: Request):
    try:
        user_id = request.state.user["username"]
        mongo_collection.delete_many({"user_id": user_id})
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/semantic", status_code=200)
async def search_semantic(request: Request, query: str):
    try:
        # 사용자 식별자 추출
        user_id = request.state.user["username"]
        # DocumentDB에서 벡터화한 query와 유사한 문서 k개 추출
        result = get_similar_docs(
            model=model,
            tokenizer=tokenizer,
            collection=mongo_collection,
            query=query,
            user_id=user_id,
            k=K_VALUE,
            efSearch=EF_SEARCH,
        )
        # 조회된 이미지 정보 반환
        return {"result": result}
    except Exception as e:
        logging.error(f"Error in search_semantic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/faces", status_code=200)
async def search_faces(request: Request, file: UploadFile):
    try:
        user_id = request.state.user["username"]
        # Rekognition의 face index에서 사용자가 제공한 이미지와 유사한 얼굴 검색
        response = rekognition.search_faces_by_image(
            CollectionId=user_id,
            Image={"Bytes": await file.read()},
            MaxFaces=20,
            FaceMatchThreshold=90,
        )
        face_matches = response["FaceMatches"]

        # 유사한 얼굴이 없으면 빈 리스트 반환
        if not face_matches:
            return {"result": []}

        picture_urls = [match["Face"]["ExternalImageId"] for match in face_matches]
        logger.info(f"Found {len(picture_urls)} matches in Rekognition: {picture_urls}")

        # 유사한 얼굴이 등장하는 이미지 url 반환
        return {"result": picture_urls}
    except Exception as e:
        logging.error(f"Error in search_faces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/faces/reset", status_code=200)
async def reset_face_index(request: Request):
    try:
        user_id = request.state.user["username"]
        rekognition.delete_collection(CollectionId=user_id)
        rekognition.create_collection(CollectionId=user_id)
        return {"status": "success"}
    except rekognition.exceptions.ResourceNotFoundException as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="ResourceNotFoundException")
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/faces/health_check")
async def health_check():
    return {"status": 200}
