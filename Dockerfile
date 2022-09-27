FROM python:3.8-slim

ARG VERSION

RUN pip3 install mqtt2measurinator==$VERSION

ENTRYPOINT mqtt2measurinator