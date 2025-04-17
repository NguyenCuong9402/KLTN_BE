FROM python:3.11-slim

# Cài các gói hệ thống cần thiết để pip và mysqlclient hoạt động đúng
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# vi_VN UTF-8/vi_VN UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
RUN apt-get update && apt-get install -y wget
RUN apt-get install -y curl
RUN apt-get install -y default-mysql-client
RUN apt-get install -y gnupg
RUN curl -fsSL https://pgp.mongodb.com/server-6.0.asc |  gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg  --dearmor --yes
RUN echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
RUN apt-get update

RUN wget http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb
RUN dpkg -i libssl1.1_1.1.1f-1ubuntu2_amd64.deb

RUN apt-get install -y mongodb-org
RUN apt-get -y install zip

RUN apt update && apt install tzdata -y
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
