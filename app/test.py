import json

import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCe2e9GWXqFkLBmQ2zec4YjZCOF-5QhDig")

model = genai.GenerativeModel(model_name="models/learnlm-2.0-flash-experimental")

# Prompt cố định
base_prompt = """
Bạn là AI trích xuất thông tin từ yêu cầu mua sắm.

Cho một đoạn văn tiếng Việt, hãy phân tích và trả về JSON có dạng sau:

{
  "min_price": <giá tối thiểu dưới dạng số nguyên VNĐ, nếu không có thì null>,
  "max_price": <giá tối đa dưới dạng số nguyên VNĐ, nếu không có thì null>,
  "type": <danh sách các loại sản phẩm có trong đoạn văn, lấy từ: ["Áo sơ mi", "áo khoác", "áo phông", "quần thun", "Áo cộc tay", "Áo đi biển"]>
}

Chỉ trả về JSON, không thêm giải thích.
"""

# ✏️ Text đầu vào có thể thay đổi
user_text = "Tôi muốn tìm áo mùa đông khoảng tám trăm nghìn đến 1 triệu VNĐ."

# Gộp prompt với văn bản người dùng
full_prompt = base_prompt + f'\n\nĐoạn văn:\n"{user_text}"'

# Gửi tới model
response = model.generate_content(full_prompt)

# Convert từ chuỗi JSON sang dict
try:
    result = json.loads(response.text)
    print(result)
except json.JSONDecodeError as e:
    print("Lỗi khi chuyển JSON:", e)
    print("Text gốc:", response.text)