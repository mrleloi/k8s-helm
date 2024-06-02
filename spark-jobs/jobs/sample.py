# kubectl delete configmap jobs-samplepy -n spark-jobs

# kubectl create configmap jobs-samplepy --from-file=sample.py=/www/wwwroot/leloi/spark-jobs/jobs/sample.py -n spark-jobs

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
    ### Đọc file excel từ Minio và lưu về folder
    # Đọc các biến môi trường
    # minio_endpoint = os.getenv('MINIO_ENDPOINT')
    # minio_access_key = os.getenv('MINIO_ACCESS_KEY')
    # minio_secret_key = os.getenv('MINIO_SECRET_KEY')
    # bucket_name = os.getenv('MINIO_BUCKET')
    
    minio_endpoint = 'minioapi.baityapp.online'
    minio_access_key = 'APhF5997dO3AvMRgmanX'
    minio_secret_key = 'EEAIaSSiFxEkp5Tm7NvgLRAKTJJlBNkAvWR73nCT'
    bucket_name = 'bigdata'
    
    default_excel_file = 'input.xlsx'
    object_name = os.getenv('EXCEL_FILE_URL', default_excel_file)
    if object_name == "${EXCEL_FILE_URL}":
        object_name = default_excel_file
    excel_file_path = "/tmp/"+ object_name
    
    # Cấu hình kết nối MinIO
    minio_config = {
        "endpoint": minio_endpoint,
        "access_key": minio_access_key,
        "secret_key": minio_secret_key,
        "secure": True  # Sử dụng True nếu MinIO cài đặt với SSL
    }
    # Tải file
    download_file_from_minio(bucket_name, object_name, excel_file_path, minio_config)

    ### Xử lý tính toán spark
    
        # .config("spark.jars.packages", "com.crealytics:spark-excel_2.12:0.13.7") \
        # .config("spark.cassandra.connection.host", "cassandra_host") \
        # .config("spark.cassandra.connection.port", "cassandra_port") \
        # .config("spark.cassandra.auth.username", "username") \
        # .config("spark.cassandra.auth.password", "password") \
    # Khởi tạo Spark Session
    spark = SparkSession.builder \
        .appName("ExcelToCassandraElasticsearch") \
        .config("spark.cassandra.connection.host", "82.180.162.37") \
        .config("spark.cassandra.connection.port", "30942") \
        .config("spark.cassandra.auth.username", "cassandra") \
        .config("spark.cassandra.auth.password", "123456a@A") \
        .getOrCreate()
    
    # Đọc file Excel sử dụng Pandas
    pandas_df = pd.read_excel(excel_file_path, engine='openpyxl')
    
        # Đọc dữ liệu từ file Excel
    # Chuyển DataFrame của pandas thành DataFrame của Spark
    df = spark.createDataFrame(pandas_df)
    # Tự dùng module của Spark đọc excel
    # df = spark.read.format("com.crealytics.spark.excel") \
    #     .option("useHeader", "true") \
    #     .option("inferSchema", "true") \
    #     .load(excel_file_path)
    
    # Xử lý và chuẩn bị dữ liệu
    # Cast the string columns that should be numeric to doubles
    numeric_cols = [
        "check_in", "check_out", "break_time_check_in", "break_time_check_out",
        "ot_check_in", "ot_check_out", "salary_per_hour", "salary_per_month", "bonus"
    ]
    
    for col_name in numeric_cols:
        df = df.withColumn(col_name, regexp_replace(col(col_name), ",", "").cast(DoubleType()).alias(col_name))
    
    # Cast date to right format
    df = df.withColumn("date_formated", to_date(col("date"), "yyyy/MM/dd"))
    
    # Thêm cột timestamp lưu thời gian cập nhật bản ghi
    df = df.withColumn("timestamp", current_timestamp())
    
    # Lưu dữ liệu nguyên gốc ban đầu line-by-line
    # Chỉ định các fields cụ thể
    data = df.select(
        "id", "first_name", "middle_name", "last_name", "date", "company_id", "company_name",
        "check_in", "check_out", "break_time_check_in", "break_time_check_out", "ot_check_in", "ot_check_out", 
        "salary_per_month", "salary_per_hour", "bonus", "timestamp"
    )
    # Sử dụng 'write' để ghi DataFrame vào Elasticsearch
    # data.write \
    #     .format("org.elasticsearch.spark.sql") \
    #     .option("es.resource", "excel_data") \
    #     .option("es.nodes", "82.180.162.37") \
    #     .option("es.port", "30920") \
    #     .option("es.net.http.auth.user", "elastic") \
    #     .option("es.net.http.auth.pass", "123456a@A") \
    #     .mode("append") \
    #     .save()
    # print("Saved data to Elasticsearch #excel_data")
    
    # Sử dụng 'write' để ghi DataFrame vào Elasticsearch
    # data.write \
    #     .format("org.apache.spark.sql.cassandra") \
    #     .mode('append') \
    #     .options(table="sample_py", keyspace="excel_result") \
    #     .save()

    # Bắt đầu tính toán ra kết quả
    # Tách ngày thành tháng/năm để gộp
    df_transformed = df.withColumn("month", expr("month(date_formated)")) \
        .withColumn("year", expr("year(date_formated)")) \
        .withColumn("work_hours", expr("check_out - check_in - (break_time_check_out - break_time_check_in)")) \
        .withColumn("ot_hours", expr("ot_check_out - ot_check_in")) \
        .withColumn("full_name", expr("concat(first_name, ' ', middle_name, ' ', last_name)"))

    # Show the DataFrame to check if the cast was successful
    #df_transformed.select("work_hours").show(truncate=False)
    
    # Tính toán dữ liệu theo nhóm
    result = df_transformed.groupBy("full_name", "month", "year", "company_id", "company_name") \
        .agg(
            countDistinct("date").alias("total_work_days"),
            _sum("work_hours").alias("total_work_hours"),
            _sum("ot_hours").alias("total_ot_hours"),
            first("salary_per_month").alias("monthly_salary"),
            first("salary_per_hour").alias("salary_per_hour"),
            first("bonus").alias("bonus")
        ) \
        .withColumn("salary", expr("monthly_salary / 21 * total_work_days + total_ot_hours * salary_per_hour + bonus"))
    result = result.withColumn("timestamp", current_timestamp())

    # Xử lý theo batch và lưu vào database
    # Chỉ định các fields cụ thể
    result = result.select(
        "full_name", "month", "year", "company_id", "company_name",
        "total_work_days", "total_work_hours", "total_ot_hours",
        "monthly_salary", "salary_per_hour", "bonus", "salary", "timestamp"
    )
    # Sử dụng 'write' để ghi DataFrame vào Elasticsearch
    # result.write \
    #     .format("org.elasticsearch.spark.sql") \
    #     .option("es.resource", "excel_result") \
    #     .option("es.nodes", "82.180.162.37") \
    #     .option("es.port", "30920") \
    #     .option("es.net.http.auth.user", "elastic") \
    #     .option("es.net.http.auth.pass", "123456a@A") \
    #     .mode("append") \
    #     .save()
    # print("Saved result to Elasticsearch #excel_result")
    
    # Sử dụng 'write' để ghi DataFrame vào Cassandra
    result.write \
        .format("org.apache.spark.sql.cassandra") \
        .mode('append') \
        .options(table="sample_py", keyspace="excel_result") \
        .save()
    # Nếu làm việc với stream như qua kafka để append nguồn dataframe liên tục
    # result.writeStream \
    #     .foreachBatch(write_to_databases) \
    #     .outputMode("update") \
    #     .trigger(processingTime='once') \
    #     .start() \
    #     .awaitTermination()
    
    # Đóng SparkSession
    spark.stop()
    
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
        'sparkapplication_file': 'sample.yaml',
        'mainapplication_file': 'sample.py',
        'input_bucket_name': bucket_name,
        'input_object_type': 'excel',
        'input_object_name': object_name,
        'elasticsearch_data_index': 'excel_data',
        'elasticsearch_result_index': 'excel_result'
    }
    # Chuyển đổi dữ liệu thành chuỗi JSON
    data_str = json.dumps(data)
    
    # Topic mà bạn muốn gửi
    topic = 'excel_result'
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

def download_file_from_minio(bucket_name, object_name, file_path, minio_config):
    """
    Tải file từ MinIO.
    
    Args:
    - bucket_name: Tên bucket trên MinIO.
    - object_name: Tên object/file bạn muốn tải.
    - file_path: Đường dẫn lưu file sau khi tải.
    - minio_config: Cấu hình kết nối đến MinIO bao gồm endpoint, access_key và secret_key.
    """
    # Tạo đối tượng MinIO client
    minio_client = Minio(
        minio_config["endpoint"],
        access_key=minio_config["access_key"],
        secret_key=minio_config["secret_key"],
        secure=minio_config["secure"]
    )
    
    try:
        # Tải file từ MinIO
        minio_client.fget_object(bucket_name, object_name, file_path)
        print(f"File {object_name} downloaded successfully.")
    except S3Error as e:
        print(f"Failed to download {object_name}: {e}")
      
# Run
main()