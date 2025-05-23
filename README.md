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
- Chạy lệnh sau để cho connect db: docker exec -it mysql_container mysql -u root -p
-  Xong nhập password mysql
```
-connect mongo compass
- mongodb://root:admin-password@127.0.0.1:27017/dev-shop?authSource=admin

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
sudo nginx -s reload

 + ngrok http 5012
 + Thấy dòng https://599e-42-112-72-4.ngrok-free.app -> http://localhost:5012
- Đặt env:( Chỉ cần khi test phần thanh toán QR)
 BASE_URL_WEBSITE=https://599e-42-112-72-4.ngrok-free.app
     
- run file Server.py
```
```