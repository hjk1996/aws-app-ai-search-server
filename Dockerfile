FROM public.ecr.aws/docker/library/python:3.11.6-slim-bullseye
WORKDIR /app
ADD . /app
