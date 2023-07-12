# FROM python:3.11
FROM python:alpine

WORKDIR /snearl

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

RUN chmod -R 777 .