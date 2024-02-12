FROM public.ecr.aws/docker/library/python:3.11.6-slim-bullseye
WORKDIR /app
ADD requirements.txt /app
RUN pip install -r requirements.txt
ADD main.py /app
CMD ["uvicorn", "main:app",]
