from typing import Annotated


import boto3
from fastapi import FastAPI, File, Form
from fastapi.middleware.cors import CORSMiddleware


session = boto3.Session(profile_name="default")
client = session.client("rekognition")
app = FastAPI()


origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5000",
    "https://www.amazonphotoquery.site"
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
        response = client.search_faces_by_image(
            CollectionId=user_id,
            Image={"Bytes": file},
            MaxFaces=20,
            FaceMatchThreshold=80,
        )
        face_matches = response["FaceMatches"]

        if not face_matches:
            return {"result": []}

        return {
            "result": [match["Face"]["ExternalImageId"] for match in face_matches],
        }

    except Exception as e:
        return {"error": str(e)}
