import os
import json

from pymongo.collection import Collection
from transformers import (
    AutoTokenizer,
    AutoModel,
)
import requests
import torch
import torch.nn.functional as F
import boto3
from botocore.exceptions import ClientError


def load_model_and_tokenizer() -> tuple[AutoModel, AutoTokenizer]:
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")
    return model, tokenizer


def get_secret(secret_name: str) -> dict:
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:

        raise e

    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


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


def get_similar_docs(
    collection: Collection,
    model: AutoModel,
    tokenizer: AutoTokenizer,
    query: str,
    user_id: str,
    k: int = 20,
    efSearch: int = 200,
) -> list[dict]:
    embedding = get_sentence_embedding(tokenizer, model, "cpu", query)
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
            }
        },
        {
            "$search": {
                "vectorSearch": {
                    {
                        "vector": embedding,
                        "path": "caption_vector",
                        "similarity": "euclidean",
                        "k": k,
                        "efSearch": efSearch,
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "file_name": 1,
            }
        },
    ]
    cursor = collection.aggregate(pipeline)
    return list(cursor)
    


def get_sentence_embedding(tokenizer, embedding_model, device, sentence: str) -> list:
    inputs = tokenizer(
        sentence,
        return_tensors="pt",
        padding=True,
        truncation=True,
    ).to(device)
    with torch.no_grad():
        model_output = embedding_model(**inputs)
    sentence_embeddings = mean_pooling(model_output, inputs["attention_mask"])
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
    return sentence_embeddings.squeeze().detach().cpu().tolist()


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[
        0
    ]  # First element of model_output contains all token embeddings
    input_mask_expanded = (
        attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    )
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
        input_mask_expanded.sum(1), min=1e-9
    )
