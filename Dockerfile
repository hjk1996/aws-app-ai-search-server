FROM public.ecr.aws/docker/library/python:3.12.2-slim
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install transformers boto3 pymongo fastapi "uvicorn[standard]" requests  mysql-connector-python python-multipart
WORKDIR /app
RUN mkdir /app/.cache
ADD download_model.py /app
RUN python download_model.py
ADD main.py /app
ADD utils.py /app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
