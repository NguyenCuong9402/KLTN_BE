import json
import google.generativeai as genai

genai.configure(api_key="AIzaSyCe2e9GWXqFkLBmQ2zec4YjZCOF-5QhDig")

model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

# product_types = [
#     "Kính Mát", "Nón", "Quần Jeans", "Quần Kaki",
#     "Quần Shorts", "Quần Tây", "Thắt Lưng", "Ví Da", "Áo Bò",
#     "Áo Khoác", "Áo Sơ Mi", "Áo Thun", "Áo cộc tay"
# ]




# ✏️ Text đầu vào có thể thay đổi
# user_text = "Tôi cần tìm một chiếc áo khoác dày để mặc vào mùa đông, nhưng giá phải dưới 800 nghìn VNĐ. Nếu có thể, tôi cũng muốn xem thêm một vài chiếc quần jeans hoặc quần kaki, không quá đắt đỏ. Thêm vào đó, tôi cần một chiếc nón để che nắng trong những ngày mùa hè nóng bức, tốt nhất là dưới 200 nghìn."



def search_ai(prompt_ai, text_search: str, list_san_pham: list):
    # Chuyển danh sách sản phẩm thành một chuỗi có định dạng phù hợp
    product_list_str = ", ".join([f'"{item}"' for item in list_san_pham])
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


def about_us(prompt):
    response = model.generate_content(prompt)
    text = response.text.strip()
    return text

def love_nhung():
    prompt = """
Hãy viết một bài văn tình cảm, lãng mạn, chân thành, như một bức thư tình gửi đến một cô gái tên Nhung. Chúng tôi đều đang ở Hà Nội, Việt Nam

Người viết là một chàng trai đang yêu cô ấy rất nhiều. Hãy thể hiện nỗi nhớ, sự quan tâm, và cảm xúc thật lòng. Bài viết cần mềm mại, cảm xúc, không sến súa quá mức, nhưng phải truyền tải được rằng "Anh yêu em, Nhung, rất nhiều".

Ngôn ngữ: Tiếng Việt
Phong cách: Trầm lắng, ấm áp, đầy cảm xúc
"""

    response = model.generate_content(prompt)
    text = response.text.strip()
    return text

# Gọi hàm search để phân tích
# result = search(prompt, user_text, product_types)
# print(result)
