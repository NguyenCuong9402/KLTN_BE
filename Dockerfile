FROM python:3.11-slim

# Cài gói cơ bản để pip hoạt động đúng
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

ENV TZ="Asia/Ho_Chi_Minh"
ENV LANG=vi_VN.UTF-8
ENV LC_ALL=vi_VN.UTF-8

# Tạo thư mục làm việc
WORKDIR /kltn-backend

# Copy riêng requirements để tận dụng cache
COPY requirements.txt .

# Cài gói python
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code vào container
COPY . .

EXPOSE 5012

CMD ["gunicorn", "--workers=3", "--threads=1", "--timeout=3600", "--preload", "-b", "0.0.0.0:5012", "server:app"]
