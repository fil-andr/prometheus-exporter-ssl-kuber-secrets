FROM python:3-alpine

COPY app /app
COPY kubectl /usr/bin/kubectl
RUN apk update \
    && apk add openssl

RUN pip install -r /app/requirements.txt

ENTRYPOINT ["python"]

CMD ["/app/script.py"]
