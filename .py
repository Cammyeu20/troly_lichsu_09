import streamlit as st
from gtts import gTTS
from io import BytesIO
import base64
import streamlit.components.v1 as components
import json
import google.generativeai as genai  

def bong_bong_bay():
    st.balloons()
   
st.set_page_config(page_title="Trợ lý Lịch sử 4.0", layout="centered")
if "page" not in st.session_state:
    st.session_state.page = "ask"
if "show_bubble" not in st.session_state:
    st.session_state.show_bubble = False

# Khởi tạo các biến lưu trạng thái kết quả để không bị mất khi trang reload
if "current_response" not in st.session_state:
    st.session_state["current_response"] = ""
if "current_summary" not in st.session_state:
    st.session_state["current_summary"] = ""
if "quiz_data" not in st.session_state:
    st.session_state["quiz_data"] = []

# ====== 🔒 ĐỌC API KEY BẢO MẬT TỪ STREAMLIT CLOUD SECRETS ======
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

def xu_ly_bai_hoc(cau_hoi: str):
    prompt = f"""
Bạn là trợ lý AI chuyên về Lịch sử.

Hãy trả lời câu hỏi dưới đây và trả về DUY NHẤT một JSON hợp lệ.

Yêu cầu:

1. answer
- Trả lời khoảng 200-300 chữ.
- Chính xác.
- Dễ hiểu như giáo viên.
- Nếu là nhân vật lịch sử thì nêu:
  + Giới thiệu
  + Cuộc đời
  + Đóng góp
  + Ý nghĩa.
- Nếu không phải lịch sử thì:
"Tôi chỉ hỗ trợ các câu hỏi về lịch sử."

2. summary

Tóm tắt thành đúng 3 ý.
3. quiz

Tạo 3 câu hỏi trắc nghiệm.

Chỉ trả về JSON:

{
  "answer": "...",
  "summary": ["...", "...", "..."],
  "quiz": [
    {
      "question": "...",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      },
      "answer": "A"
    }
  ]
}
câu hỏi:
{cau_hoi}
"""

    try:
        res = model.generate_content(prompt)
        text = res.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text) 
    except:
        return None
   
# ======================
# 🔍 TỪ KHÓA LỊCH SỬ (GIỮ NGUYÊN HIỆN TRẠNG BẢO VỆ APP)
# ======================
history_keywords = [
    "lịch sử", "chiến tranh", "khởi nghĩa", "cách mạng",
    "triều đại", "vua", "thế chiến", "cổ đại", "trung đại",
    "hiện đại", "di tích", "danh lam", "quân", "trận",
    "đế quốc", "là ai", "bác hồ", "hồ chí minh", "nạn đói", "thế giới", 
    "kể tên", "thông tin", "phát xít", "dân chủ", "hậu quả", "mỹ la-tinh", 
    "kinh tế", "hiệp hội", "giặc đói", "chiến dịch", "phong trào", "thắng lợi", "trật tự","xã hội",
    "thành tựu", "xu thế", "điện biên phủ", "cột mốc quan trọng", "tóm tắt"
]

def is_history_question(question):
    q = question.lower()
    for kw in history_keywords:
        if kw in q:
            return True
    return False

def tao_trac_nghiem_tu_AI(noi_dung):
    prompt = f"""
    Dựa vào nội dung sau, hãy tạo 3 câu hỏi trắc nghiệm lịch sử.
    Mỗi câu có 4 đáp án A, B, C, D.
    Chỉ có 1 đáp án đúng.

    Chỉ trả về định dạng mảng JSON thuần túy, KHÔNG giải thích, KHÔNG thêm ký tự suy luận Markdown ```json.

    Định dạng mẫu:
    [
      {{
        "question": "Câu hỏi là gì?",
        "options": {{
          "A": "Đáp án A",
          "B": "Đáp án B",
          "C": "Đáp án C",
          "D": "Đáp án D"
        }},
        "answer": "A"
      }}
    ]

    Nội dung:
    {noi_dung}
    """
    try:
        res = model.generate_content(prompt)
        text = res.text.strip()

        # Trích xuất chuỗi JSON chuẩn xác từ dữ liệu trả về
        start = text.find("[")
        end = text.rfind("]") + 1
        json_text = text[start:end]

        return json.loads(json_text)
    except Exception as e:
        st.error("❌ Lỗi tạo câu hỏi trắc nghiệm từ AI")
        st.code(str(e))
        return []

# ======================
# ⚙️ CẤU HÌNH TRANG & GIAO DIỆN
# ======================
if "audio_unlocked" not in st.session_state:
    st.session_state["audio_unlocked"] = False

st.title("📚 TRỢ LÝ LỊCH SỬ 4.0")
st.write("👉 Bấm BẬT ÂM THANH (chỉ 1 lần), sau đó nhập câu hỏi rồi bấm Trả lời.")
st.write("📱 Trên IOS phải bấm ▶ để nghe.")
st.write("📱 Android/PC tự phát âm thanh.")

st.markdown("""
<style>
/* ===== NỀN GIẤY CỔ ===== */
.stApp {
    background: linear-gradient(180deg, #f6f1e7, #efe7d8);
    color: #2b2b2b;
    font-family: "Segoe UI", serif;
}
/* 🚫 TẮT MÀU CẢNH BÁO MẶC ĐỊNH CỦA RADIO */
div[role="radiogroup"] label {
    background: transparent !important;
    border: none !important;
}
div[role="radiogroup"] input:checked + div {
    background-color: transparent !important;
    box-shadow: none !important;
}
div[role="radiogroup"] input:focus + div {
    outline: none !important;
}
/* ===== TIÊU ĐỀ ===== */
h1 {
    color: #4b2e1f;
    text-align: center;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}
h2, h3 {
    color: #5c3b28;
}
/* ===== Ô NHẬP – MỀM NHƯ SỔ TAY ===== */
input[type="text"] {
    background-color: #fffdf8;
    border: 2px dashed #9c7a4a;
    border-radius: 18px;
    padding: 14px;
    font-size: 16px;
    color: #000000 !important;
    font-weight: 500;
    transition: all 0.25s ease;
}
input[type="text"]::placeholder {
    color: #3b2f1c !important;
    opacity: 1;
    font-style: italic;
}
input[type="text"]:focus {
    outline: none;
    border-color: #6b4a2d;
    box-shadow: 0 0 0 3px rgba(107,74,45,0.15);
}
/* ===== NÚT ===== */
.stButton > button {
    background: linear-gradient(180deg, #7a5536, #5c3b28);
    color: white;
    border-radius: 20px;
    padding: 14px 30px;
    font-size: 16px;
    font-weight: 600;
    border: none;
    cursor: pointer;
    box-shadow: 0 6px 0 #4b2e1f;
    animation: pulse 2.5s infinite;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 0 #3a2216;
}
.analysis-box {
    margin-top: 12px;
    padding: 14px 18px;
    background-color: #f3ead7;
    border-left: 6px solid #7a5536;
    border-radius: 14px;
    font-style: italic;
    color: #4b2e1f;
    font-weight: 500;
    animation: fadePulse 1.6s infinite;
}
@keyframes fadePulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}
.stButton > button:active {
    transform: translateY(4px);
    box-shadow: 0 2px 0 #3a2216;
}
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}
/* ===== THẺ TRẢ LỜI ===== */
.stAlert, .stInfo {
    background-color: #fff8e9;
    border-radius: 22px;
    padding: 18px;
    margin-top: 14px;
    box-shadow: 0 10px 18px rgba(0,0,0,0.12);
    border-left: 8px solid #6b4a2d;
    animation: pop 0.35s ease;
}
.stInfo {
    border-left-color: #3f6b4f;
    background-color: #eef5ef;
}
@keyframes pop {
    from { transform: scale(0.95); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}
audio {
    margin-top: 12px;
    border-radius: 14px;
}
label {
    font-weight: 600;
}
label::before {
    content: "🖋️ ";
}
</style>
""",  unsafe_allow_html=True)

# ======================
# 🔓 NÚT BẬT ÂM THANH
# ======================
if st.button("🔊 BẬT ÂM THANH (1 lần)"):
    js = """
    <script>
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            if (ctx.state === 'suspended') ctx.resume();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            gain.gain.value = 0;
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.05);
        } catch(e) {}
    </script>
    """
    components.html(js, height=0)
    st.session_state["audio_unlocked"] = True
    st.success("Âm thanh đã mở khoá!")

# ======================
# 📜 DỮ LIỆU LỊCH SỬ CƠ BẢN
# ======================
lich_su_data = {
    "trưng trắc": "Hai Bà Trưng khởi nghĩa chống quân Hán năm 40 sau Công Nguyên.",
    "ngô quyền": "Ngô Quyền đánh bại quân Nam Hán trên sông Bạch Đằng năm 938.",
    "lý thái tổ": "Năm 1010, Lý Thái Tổ dời đô về Thăng Long."
}

# =========================================================
# 💬 KHU VỰC HỎI ĐÁP CHÍNH VÀ LUỒNG XỬ LÝ DỮ LIỆU
# =========================================================
cau_hoi = st.text_input("Nhập câu hỏi lịch sử của bạn tại đây:", placeholder="Ví dụ: Ý nghĩa chiến dịch Điện Biên Phủ?")

if st.button("Trả lời"):
    if cau_hoi.strip() == "":
        st.warning("Vui lòng điền nội dung câu hỏi!")
    elif not is_history_question(cau_hoi):
        st.error("🛑 Trợ lý chỉ xử lý các câu hỏi thuộc lĩnh vực Lịch sử!")
    else:
        with st.spinner("📜 Hệ thống đang lục tìm sử sách..."):
            ans = ""
            for key, val in lich_su_data.items():
                if key in cau_hoi.lower():
                    ans = val
                    break
            
            if ans:
                    st.session_state["current_response"] = ans
                    st.session_state["current_summary"] = ""
                    st.session_state["quiz_data"] = []
                    st.rerun()
            else:
                    data = xu_ly_bai_hoc(cau_hoi)
                    if data:
                        st.session_state["current_response"] = data.get("answer", "")

                        st.session_state["current_summary"] = "\n".join(data.get("summary", []))                    
                    
                        st.session_state["quiz_data"] = data.get("quiz", [])  
          
                        st.rerun()

# Hiển thị kết quả lưu trữ ra màn hình sau khi tải lại trang
if st.session_state["current_response"]:
    st.markdown("### 🤖 Câu trả lời từ AI:")
    st.write(st.session_state["current_response"])
    
    try:
        tts = gTTS(text=st.session_state["current_response"], lang='vi')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        st.audio(audio_bytes, format='audio/mp3')
    except Exception as e:
        st.caption(f"Không kết nối được bộ phát âm thanh: {e}")

if st.session_state["current_summary"]:
    st.markdown("### 📝 Ghi nhớ nhanh (Tóm tắt 3 ý):")
    st.info(st.session_state["current_summary"])

if st.session_state["quiz_data"]:
    st.markdown("### ✍️ Bài tập trắc nghiệm...")
    for idx, q in enumerate(st.session_state["quiz_data"]):
        st.markdown(f"**Câu {idx+1}: {q['question']}**")
        options_list = list(q['options'].keys())
        
        user_choice = st.radio(
            f"Chọn đáp án cho câu {idx+1}:", 
            options_list, 
            format_func=lambda x: f"{x}. {q['options'][x]}",
            key=f"quiz_{idx}"
        )
        
        if st.button(f"Kiểm tra câu {idx+1}"):
            if user_choice == q['answer']:
                st.success("🎉 Bạn đã chọn chính xác!")
                bong_bong_bay()
            else:
                st.error(f"❌ Sai rồi! Đáp án đúng là: {q['answer']}")
