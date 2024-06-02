FROM apache/nifi:1.25.0

# Cài đặt Python và pip
USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Cài đặt pandas và openpyxl
RUN pip3 install pandas openpyxl

# Đảm bảo tất cả các thư mục và tập tin có quyền phù hợp
RUN chown -R nifi:nifi /opt/nifi

USER nifi
