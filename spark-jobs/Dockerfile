FROM bitnami/spark:3.5.1

USER root

RUN apt update && apt upgrade -y && apt install -y nano  && apt install -y curl && \
    pip install minio pandas openpyxl confluent_kafka

COPY ./jars/ /opt/bitnami/spark/jars/

COPY ./jobs/ /opt/spark/work-dir/jobs/

#USER 1001
