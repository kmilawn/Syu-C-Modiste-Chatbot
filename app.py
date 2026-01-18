import streamlit as st
import os, json
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError, ServerError

# ================= INIT =================
st.set_page_config(
    page_title="Syu-C Modiste Chatbot",
    page_icon="🧵",
    layout="centered"
)

load_dotenv()
API_KEY = st.secrets["GEMINI_API_KEY"]

if not API_KEY:
    st.error("API Key Gemini belum diisi di .env")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ================= MODEL AUTO =================
MODEL_NAME = None
for m in client.models.list():
    if "generateContent" in m.supported_actions:
        MODEL_NAME = m.name
        break

if not MODEL_NAME:
    st.error("Model Gemini tidak tersedia")
    st.stop()

# ================= STYLE =================
st.markdown("""
<style>
.chat-user {
    background:#FFD1DC;
    padding:12px;
    border-radius:15px;
    text-align:right;
    margin-bottom:10px;
}
.chat-admin {
    background:#FFF0E5;
    padding:12px;
    border-radius:15px;
    text-align:left;
    margin-bottom:10px;
}
.chat-image {
    margin-top:8px;
    border-radius:10px;
}
.intro-box {
    text-align:center;
    color:#666;
    margin-top:60px;
    margin-bottom:40px;
    font-size:16px;
}
.small-caption {
    font-size:13px;
    color:#999;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown(
    "<h2 style='color:#E75480;text-align:center'>🧵 Syu-C Modiste Chatbot</h2>",
    unsafe_allow_html=True
)

# ================= SESSION =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "started" not in st.session_state:
    st.session_state.started = False

# ================= CAPTION / INTRO =================
if not st.session_state.started:
    st.markdown("""
    <div class="intro-box">
        Chatbot AI ini siap membantu menjawab pertanyaan seputar jasa jahit
        <b>Syu-C Modiste</b>, mulai dari model pakaian, harga, bahan,
        hingga estimasi waktu pengerjaan.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(
        "<div class='small-caption'>Asisten virtual usaha jahit & modiste</div>",
        unsafe_allow_html=True
    )

# ================= FAQ =================
with open("data/faq.json", encoding="utf-8") as f:
    faq = json.load(f)

def jawab_dari_faq(pertanyaan):
    for item in faq:
        if item["question"].lower() in pertanyaan.lower():
            return item["answer"]
    return None

faq_context = "\n".join(
    [f"Q: {x['question']}\nA: {x['answer']}" for x in faq]
)

# ================= DISPLAY CHAT =================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f"<div class='chat-user'>{msg['content']}</div>",
            unsafe_allow_html=True
        )
        if "image" in msg:
            st.image(msg["image"], width=250)   # <<< KECIL
    else:
        st.markdown(
            f"<div class='chat-admin'>{msg['content']}</div>",
            unsafe_allow_html=True
        )

# ================= UPLOAD (TANPA PREVIEW) =================
uploaded = st.file_uploader(
    "",
    type=["jpg", "png", "jpeg"],
    label_visibility="collapsed"
)

# ================= INPUT =================
user_input = st.chat_input("Tanya soal jahitan, harga, bahan, model...")

if user_input:
    st.session_state.started = True

    user_message = {
        "role": "user",
        "content": user_input
    }

    if uploaded:
        user_message["image"] = uploaded

    st.session_state.messages.append(user_message)

    st.markdown(
        f"<div class='chat-user'>{user_input}</div>",
        unsafe_allow_html=True
    )

    if uploaded:
        st.image(uploaded, width=250)   # <<< KECIL

    # ================= FAQ FIRST =================
    jawaban_faq = jawab_dari_faq(user_input)

    if jawaban_faq:
        bot_reply = jawaban_faq
    else:
        prompt = f"""
Kamu adalah customer service profesional untuk usaha jahit Syu-C Modiste.

Gunakan informasi ini:
{faq_context}

Jika user menanyakan harga:
- berikan estimasi
- jelaskan tergantung bahan & kerumitan

Jawab ramah, singkat, dan profesional.

Pertanyaan:
{user_input}
"""

        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            bot_reply = response.text

        except ClientError as e:
            if "429" in str(e):
                bot_reply = (
                    "🙏 Maaf, layanan sedang penuh.\n\n"
                    "Silakan tunggu sebentar atau tanyakan hal umum seperti harga dasar atau jenis bahan."
                )
            else:
                bot_reply = "❌ Terjadi kesalahan. Silakan coba lagi."

        except ServerError:
            bot_reply = "⚠️ Server sedang sibuk. Silakan coba beberapa saat lagi."

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

    st.markdown(
        f"<div class='chat-admin'>{bot_reply}</div>",
        unsafe_allow_html=True
    )
