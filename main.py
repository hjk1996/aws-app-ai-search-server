import boto3
from glob import glob
from pprint import pprint

from models import Label, Text, FaceDetails, ImageMetadata


if __name__ == "__main__":
    session = boto3.Session(profile_name="default")
    client = session.client("rekognition")

    sample_images = glob("samples/*")

    for image in sample_images:
        with open(image, "rb") as imageFile:
            image_bytes = imageFile.read()
            # print("--------------------")
            # response_1 = client.detect_labels(
            #     Image={"Bytes": image_bytes}, MaxLabels=20, MinConfidence=90
            # )
            # labels = response_1["Labels"]
            # labels = [Label.model_validate(label) for label in labels]
            # pprint(labels)
            # response_2 = client.detect_text(Image={"Bytes": image_bytes})
            # texts = response_2["TextDetections"]
            # texts = [Text.model_validate(text) for text in texts]
            response_3 = client.detect_faces(
                Image={"Bytes": image_bytes}, Attributes=["ALL"]
            )
            face_details = response_3["FaceDetails"]
            face_details = [
                FaceDetails.model_validate(face_detail) for face_detail in face_details
            ]
            pprint(face_details)
            # image_metadata = ImageMetadata(
            #     id=image, labels=labels, texts=texts, face_details=face_details
            # )
            # pprint(image_metadata.dict())
            print("--------------------")
