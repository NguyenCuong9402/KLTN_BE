# coding=utf-8
# Python 3.6

from time import time
from datetime import datetime
import json, hmac, hashlib, urllib.request, urllib.parse, random
from shortuuid import uuid
import requests
config = {
  "app_id": 2553,
  "key1": "PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL",
  "key2": "kLtgPl8HHhfvMuDHPwKfgfsY4Ydm9eIz",
  "endpoint": "https://sb-openapi.zalopay.vn/v2/create"
}
transID = random.randrange(1000000)


order = {
  "app_id": config["app_id"],
  "app_trans_id": "{:%y%m%d}_{}".format(datetime.today(), transID), # mã giao dich có định dạng yyMMdd_xxxx
  "app_user": "user123",
  "app_time": int(round(time() * 1000)), # miliseconds
  "embed_data": json.dumps({}),
  "item": json.dumps([{}]),
  "amount": 50000,
  "description": "Lazada - Payment for the order #"+str(transID),
  "bank_code": "zalopayapp"
}

# app_id|app_trans_id|app_user|amount|apptime|embed_data|item
data = "{}|{}|{}|{}|{}|{}|{}".format(order["app_id"], order["app_trans_id"], order["app_user"],
order["amount"], order["app_time"], order["embed_data"], order["item"])

order["mac"] = hmac.new(config['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()

response = requests.post(config["endpoint"], data=order)

# Đọc kết quả JSON
result = response.json()

print(result)