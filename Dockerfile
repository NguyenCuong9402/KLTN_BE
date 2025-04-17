FROM python:3.11-slim

# Cài các gói hệ thống cần thiết cho pip, mysqlclient và MongoDB
RUN apt-get update && \
    apt-get install -y \
    locales \
    curl \
    default-mysql-client \
    gnupg \
    wget \
    mongodb-org \
    zip \
    tzdata && \
    # Cài đặt tiếng Việt và timezone
    sed -i -e 's/# vi_VN.UTF-8/vi_VN.UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    # Cài đặt MongoDB
    curl -fsSL https://pgp.mongodb.com/server-6.0.asc | gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor --yes && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    # Cài đặt libssl1.1 cần thiết cho một số thư viện
    wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb && \
    dpkg -i libssl1.1_1.1.1f-1ubuntu2_amd64.deb && \
    # Cài đặt lại các gói sau khi cài đặt libssl
    apt-get install -f -y

# Cài đặt timezone và cấu hình ngôn ngữ cho ứng dụng
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

# Lệnh khởi động ứng dụng
CMD ["gunicorn", "--workers=3", "--threads=1", "--timeout=3600", "--preload", "-b", "0.0.0.0:5012", "server:app"]
