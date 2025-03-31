# Hướng dẫn chạy local cho Lộc

* Cài đặt ví momo và zalo ( Chỉ cần khi test phần thanh toán QR)
-https://beta-docs.zalopay.vn/docs/developer-tools/test-instructions/test-wallets/
-https://developers.momo.vn/v3/vi/download/
* Cách nạp tiền ví zalo
- Xác thực căn cước công dân
- Mở https://docs.zalopay.vn/v1/start/#A , chọn phần trải nghiệm với zaloPay II Nạp tiền vào tài khoản
* Nạp tiền ví momo
- Liên kết ngân hàng bidv ( Nhập bừa theo hướng dẫn, mã 000000)
- Nạp tiền vào.

* chạy Docker-compose
```
-connect mongo compass
- mongodb://root:admin@127.0.0.1:27017/dev-shop?authSource=admin

```


* Cài đặt base và data
```
- Tải mysql và cài tạo 1 db dev_kltn với cấu hình
- Chạy lệnh: 
+ cd app
+ flask db upgrade
+ Sửa setting Devconfig: mật khẩu mysql server vào PASSWORD
     SQLALCHEMY_DATABASE_URI = 'mysql://root:PASSWORD@127.0.0.1:3306/dev_kltn?charset=utf8mb4'
- run file.py init db ở folder init_db
```
* Chạy chương trình
```

- Cài đặt ngrok -> Sau đó bật ngrok chạy lệnh: ( Chỉ cần khi test phần thanh toán QR)
 + ngrok http 5012
 + Thấy dòng https://599e-42-112-72-4.ngrok-free.app -> http://localhost:5012
- Đặt env:( Chỉ cần khi test phần thanh toán QR)
 BASE_URL_WEBSITE=https://599e-42-112-72-4.ngrok-free.app
     
- run file Server.py
```




# Table of Contents
1. [Installation](#Installation)
2. [Init mysql by docker](#Init mysql by docker)
3. [Migrations Database](#Migrations Database)
4. [Build container in local](#Build container in local)

# Installation

* Python 3.7: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
* Get Docker: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
* Install docker for Ubuntu 18.04: [https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04)
* Install docker compose for Linux: [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

# Init mysql by docker

```
- cd init_db/init_mysql
- docker-compose up --build -d
```

# Migrations Database
Note command line upgrate database

Note link demo : https://flask-migrate.readthedocs.io/en/latest/

```
- cd app
- flask db init
- flask db migrate -m "<comment update database>"
- flask db upgrade

SELECT @@sql_mode
SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''))
NOTE: Set chartset utf8bm4_vietnamese_ci for db 

```

# Update settings.py khi thay đổi domain
```
* Khi thay đổi domain cần update settings.py

BASE_URL_WEBSITE = 'https://inict.mta.edu.vn'

```

# Build container in local
```
cd fit-backend
```
Using Docker BuildKit for save time building later: [Build images with BuildKit](https://docs.docker.com/develop/develop-images/build_enhancements/)

### Do not use this for Product environment
```commandline
setx DOCKER_BUILDKIT 1
setx COMPOSE_DOCKER_CLI_BUILD 1
```
* Staging
```
docker-compose --env-file ./config/.env.stg up --build -d
```
* Production
```
docker-compose --env-file ./config/.env.prd up --build -d
```

```
note: before migrate foreign key must check status of parent table and
 set chartset/collate for child table
example:
SHOW TABLE STATUS WHERE name = 'user';

   __table_args__ = {
        'mysql_charset': 'utf8',
        'mysql_collate': 'utf8_general_ci',
    }

```

* Backup data
```
   mongo: 
    restore data:
        mongorestore /host:<hostname> /port:<port> /username:<username> /password:<password> /authenticationDatabase:admin /d <dbname> <path\to\folder>
    backup data:
        mongodump --host=<hostname> --port=<port> --username=<username> -p "<password>" --authenticationDatabase=admin -d <dbname> -o ./<folder>
    note: password of mongodb not recognize special character
   mysql:
    backup data:
        mysqldump -c -P <port> -h <host> -u <username> --password=<password> <dbname> > <path\to\file>
```


* Setting nginx
```
   nginx: 
        server {

        server_name prd.fit.boot.ai;

        root /var/lib/jenkins/workspace/fit_frontend_prd/build;

        # Add index.php to the list if you are using PHP
        index index.html index.htm index.nginx-debian.html;
        client_max_body_size 150M;

        #server_name prd.fit.boot.ai;

        location / {
                # First attempt to serve request as file, then
                # as directory, then fall back to displaying a 404.
                try_files $uri $uri/ /index.html;
        }

        location /api {
                proxy_pass  http://localhost:5010/api;
        }

        location /files {
                proxy_pass  http://localhost:5010/files;
        }
        
        location /Images {
                proxy_pass  http://localhost:5010/files/Images;
        }

   }
   
* Lưu ý cần set client_max_body_size để có thể upload ảnh
```