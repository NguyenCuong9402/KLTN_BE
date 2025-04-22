import json
import google.generativeai as genai

genai.configure(api_key="AIzaSyCe2e9GWXqFkLBmQ2zec4YjZCOF-5QhDig")

model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

product_types = [
    "Kính Mát", "Nón", "Quần Jeans", "Quần Kaki",
    "Quần Shorts", "Quần Tây", "Thắt Lưng", "Ví Da", "Áo Bò",
    "Áo Khoác", "Áo Sơ Mi", "Áo Thun", "Áo cộc tay"
]


# Prompt cố định
prompt = """
Bạn là AI chuyên phân tích yêu cầu mua sắm thời trang từ người dùng tại Việt Nam.

**Nhiệm vụ của bạn** là phân tích một đoạn văn tiếng Việt để trích xuất các thông tin sau:
1. **Giá tối thiểu**: Giá người dùng mong muốn tìm sản phẩm, nếu có. Nếu không có giá tối thiểu, trả về null.
2. **Giá tối đa**: Giá cao nhất mà người dùng sẵn sàng chi trả, nếu có. Nếu không có giá tối đa, trả về null.
3. **Loại sản phẩm**: Danh sách các loại sản phẩm mà người dùng yêu cầu tìm kiếm, lấy từ danh sách sau: [#LIST_SAN_PHAM]. Bạn chỉ được chọn các sản phẩm có trong danh sách này.

**Cách phân tích**:
1. **Thời tiết và mùa** tại Việt Nam có sự phân hóa rõ rệt giữa các vùng miền và mùa trong năm:
   - **Mùa hè** (tháng 4 đến tháng 8) thường rất nóng, đặc biệt là các khu vực miền Nam và miền Trung. 
   - **Mùa thu** (tháng 9 đến tháng 11) thời tiết mát mẻ, đôi khi có mưa, nhưng vẫn không quá lạnh.
   - **Mùa đông** (tháng 12 đến tháng 2) ở miền Bắc và miền Trung khá lạnh, cần áo khoác hoặc sản phẩm giữ ấm.
   - **Mùa xuân** (tháng 3) cũng có thời tiết mát mẻ, không quá lạnh.

2. **Nếu không có thông tin rõ ràng về mùa**, bạn cần phải suy luận từ các yếu tố khác trong đoạn văn:
   - **Từ khóa chỉ mùa hoặc thời tiết**: Nếu không có từ khóa trực tiếp như "mùa hè", "mùa đông", "lạnh", "nóng", bạn cần xem xét các từ mô tả cảm giác hoặc hành vi của người mua sắm. 
   Ví dụ: "mặc vào mùa thu", "mặc cho thời tiết ấm", "cần áo mát", "nên mặc áo giữ ấm", "áo cho thời tiết mưa".
   - **Các từ khóa cảm giác**: Tìm kiếm các từ mô tả cảm giác về nhiệt độ, ví dụ: "ấm", "mát mẻ", "lạnh", "nóng".
    Những từ này sẽ giúp xác định mùa.
   - **Các từ mô tả tính chất thời tiết**: "Mưa", "gió", "khô ráo", "nắng", "lạnh", "ẩm ướt" có thể giúp suy luận mùa hoặc thời điểm trong năm.

3. **Giá**: Nếu trong đoạn văn có đề cập đến giá hoặc khoảng giá (ví dụ: "khoảng 300 nghìn đến 1 triệu VNĐ"), bạn cần xác định và trả về giá tối thiểu và tối đa.
   - Nếu chỉ có một giá duy nhất, hãy xác định là giá tối đa hoặc tối thiểu tùy thuộc vào cách người dùng diễn đạt.
   - Nếu không có giá cụ thể, trả về `null` cho cả hai trường giá.

**Lưu ý**:
- Chỉ trả về JSON, không thêm giải thích.
- Các loại sản phẩm phải nằm trong danh sách cho trước, và danh sách không bao gồm các sản phẩm ngoài danh sách này.

**Ví dụ yêu cầu**:
- "Tôi muốn tìm áo mùa hè khoảng 300 nghìn đến 1 triệu VNĐ."
**Kết quả mong muốn**:

Với yêu cầu: "Tôi muốn tìm áo mùa hè khoảng 300 nghìn đến 1 triệu VNĐ."
   Kết quả:
   ```json
   {
     "min_price": 300000,
     "max_price": 1000000,
     "type": ["Áo sơ mi", "Áo phông"]
   }
"""

# ✏️ Text đầu vào có thể thay đổi
user_text = "Tôi cần tìm một chiếc áo khoác dày để mặc vào mùa đông, nhưng giá phải dưới 800 nghìn VNĐ. Nếu có thể, tôi cũng muốn xem thêm một vài chiếc quần jeans hoặc quần kaki, không quá đắt đỏ. Thêm vào đó, tôi cần một chiếc nón để che nắng trong những ngày mùa hè nóng bức, tốt nhất là dưới 200 nghìn."



def search(prompt_ai, text_search: str, list_san_pham: list):
    # Chuyển danh sách sản phẩm thành một chuỗi có định dạng phù hợp
    product_list_str = ", ".join([f'"{item}"' for item in list_san_pham])
    print(product_list_str)
    # Thay thế #LIST_SAN_PHAM trong prompt bằng danh sách sản phẩm
    full_prompt = prompt_ai.replace("#LIST_SAN_PHAM", product_list_str) + f'\n\nĐoạn văn:\n"{text_search}"'

    response = model.generate_content(full_prompt)

    text = response.text.strip()

    # Nếu có markdown ```json thì loại bỏ
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        result = {}

    return result


# Gọi hàm search để phân tích
result = search(prompt, user_text, product_types)
print(result)
