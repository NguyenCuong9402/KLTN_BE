import json

import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCe2e9GWXqFkLBmQ2zec4YjZCOF-5QhDig")

model = genai.GenerativeModel(model_name="models/learnlm-2.0-flash-experimental")

# Prompt cố định
prompt = """
Bạn là AI trích xuất thông tin từ yêu cầu mua sắm thời trang.

Cho một đoạn văn tiếng Việt, hãy phân tích và trả về JSON có dạng sau:

{
  "min_price": <giá tối thiểu dưới dạng số nguyên VNĐ, nếu không có thì null>,
  "max_price": <giá tối đa dưới dạng số nguyên VNĐ, nếu không có thì null>,
  "type": <danh sách các loại sản phẩm có trong đoạn văn, lấy từ: ["Áo sơ mi", "áo khoác", "áo phông", "quần thun"]>
}

**Lưu ý khi xác định loại sản phẩm:**
- Nếu người dùng đề cập đến mùa hè hoặc thời tiết nóng → ưu tiên "áo phông", "áo sơ mi", "quần thun".
- Nếu người dùng đề cập mùa đông, trời lạnh → ưu tiên "áo khoác".
- Nếu không rõ mùa, chỉ dựa vào từ khóa xuất hiện trong đoạn văn.
- Chỉ trả về những loại nằm trong danh sách cho trước.
- Chỉ trả về JSON, không thêm giải thích.

Ví dụ đoạn văn:
"Tôi muốn tìm áo mùa hè khoảng 300 nghìn đến 1 triệu VNĐ."

Kết quả mong muốn:
{
  "min_price": 300000,
  "max_price": 1000000,
  "type": ["Áo sơ mi", "áo phông"]
}
"""

# ✏️ Text đầu vào có thể thay đổi
user_text = "Tôi muốn tìm áo mùa thu, mùa hè mặc được mà giá chưa đến 1 triệu VNĐ."

# Gộp prompt với văn bản người dùng
full_prompt = prompt + f'\n\nĐoạn văn:\n"{user_text}"'

# Gửi tới model
response = model.generate_content(full_prompt)

text = response.text.strip()

# Nếu có markdown ```json thì loại bỏ
if text.startswith("```json"):
    text = text.removeprefix("```json").strip()
if text.endswith("```"):
    text = text.removesuffix("```").strip()

# Parse JSON
try:
    result = json.loads(text)
    print("✅ Kết quả loại:", type(result))
    print("✅ Kết quả parse JSON:", result)

except json.JSONDecodeError as e:
    print("❌ JSON không hợp lệ:", e)
    print("Dữ liệu lỗi:", text)