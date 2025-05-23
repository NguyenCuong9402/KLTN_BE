FROM python:3.11


RUN apt-get update && apt-get install -y \
    zip \
    tzdata \
    default-mysql-client \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài mongodump từ MongoDB Tools
RUN curl -fsSL https://pgp.mongodb.com/server-6.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server.gpg && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server.gpg ] https://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" \
    | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    apt-get install -y mongodb-database-tools && \
    rm -rf /var/lib/apt/lists/* \

ENV TZ="Asia/Ho_Chi_Minh"
ENV LANG=vi_VN.UTF-8
ENV LC_ALL=vi_VN.UTF-8

# Tạo thư mục làm việc
WORKDIR /kltn-backend

# Copy requirements để tận dụng cache Docker
COPY requirements.txt .

# Cài gói python từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code vào container
COPY . .

# Mở cổng ứng dụng
EXPOSE 5012

# Lệnh khởi động
CMD ["gunicorn", "--workers=3", "--threads=1", "--timeout=3600", "--preload", "-b", "0.0.0.0:5012", "server:app"]
