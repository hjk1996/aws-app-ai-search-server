from typing import Annotated


import boto3
from fastapi import FastAPI, File, Form
from fastapi.middleware.cors import CORSMiddleware


session = boto3.Session()
client = session.client("rekognition")
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
        response = client.search_faces_by_image(
            CollectionId=user_id,
            Image={"Bytes": file},
            MaxFaces=20,
            FaceMatchThreshold=80,
        )
        face_matches = response["FaceMatches"]
        client.delete

        if not face_matches:
            return {"result": []}

        return {
            "result": [match["Face"]["ExternalImageId"] for match in face_matches],
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/search/faces/health_check")
async def health_check():
    return {"status": "ok"}