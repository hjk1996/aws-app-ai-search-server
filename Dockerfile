FROM bitnami/pytorch:2.2.0
RUN pip install transformers boto3 pymongo fastapi "uvicorn[standard]" requests
WORKDIR /app
RUN mkdir /app/.cache
ADD download_model.py /app
RUN python download_model.py
ADD main.py /app
ADD utils.py /app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
