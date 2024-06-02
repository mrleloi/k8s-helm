# kubectl delete configmap jobs-sample1py -n spark-jobs

# kubectl create configmap jobs-sample1py --from-file=sample1.py=/www/wwwroot/leloi/spark-jobs/jobs/sample1.py -n spark-jobs

# Import the necessary modules
import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, to_date, expr, countDistinct
from pyspark.sql.functions import sum as _sum  # Ensure sum is imported as _sum
from pyspark.sql.functions import regexp_replace
from pyspark.sql.functions import first
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import DoubleType
from minio import Minio
from minio.error import S3Error
from confluent_kafka import Producer
import json

def main():
    spark = SparkSession.builder \
        .appName("ExcelToCassandraElasticsearch") \
        .getOrCreate()
    # Đóng SparkSession
    spark.stop()
    
    # Tính toán
    a = 1
    b = 2
    c = a + b
    
    # Gửi data lên kafka
    # Cấu hình Kafka Producer
    config = {
        'bootstrap.servers': '82.180.162.37:30992',  # Thay thế bằng địa chỉ máy chủ Kafka của bạn
        'sasl.mechanisms': 'PLAIN',
        'security.protocol': 'SASL_PLAINTEXT',
        'sasl.username': 'conduktor',
        'sasl.password': '123456a@A'
    }
    
    producer = Producer(**config)
    
    # Dữ liệu cần gửi
    data = {
        'status': 'success',
        'result': c
    }
    # Chuyển đổi dữ liệu thành chuỗi JSON
    data_str = json.dumps(data)
    
    # Topic mà bạn muốn gửi
    topic = 'example'
    key = 'result'
    
    # Gửi thông điệp
    try:
        producer.produce(topic, key=key.encode('utf-8'), value=data_str.encode('utf-8'), callback=acked)
        producer.poll(1)
    except BufferError as e:
        print(f'Buffer error: {e}')
    finally:
        producer.flush()
    print("Message sent to Kafka")

def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        print("Message produced: %s" % (str(msg)))

# Run
main()