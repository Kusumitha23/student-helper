import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os
import time
import random

# ---------------- CONFIG ----------------
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found in environment variables")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# ---------------- SESSION STATE ----------------
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None
if "last_action" not in st.session_state:
    st.session_state.last_action = None

# ---------------- UI ----------------
st.set_page_config(page_title="AI Study Helper", layout="wide")

st.markdown("""
<style>
.main { background: linear-gradient(135deg, #090616 0%, #1e2060 100%); color: white; }
.result-container { background-color: white; border-radius: 15px; padding: 30px; color: #1e2060; }
</style>
""", unsafe_allow_html=True)

st.title("🎓 AI Study Helper")

# ---------------- SAFE GEMINI CALL ----------------
def safe_call(prompt):
    for attempt in range(3):
        try:
            return model.generate_content(prompt).text
        except Exception:
            time.sleep(2 * (attempt + 1) + random.random())
    return "⚠️ Gemini limit reached. Please wait and try again."

# ---------------- PDF UPLOAD ----------------
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:

    reader = PdfReader(uploaded_file)

    raw_text = ""
    for page in reader.pages:
        raw_text += page.extract_text() or ""

    # CLEAN + LIMIT TEXT (VERY IMPORTANT FIX)
    raw_text = " ".join(raw_text.split())
    raw_text = raw_text[:2000]

    st.write("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sum_btn = st.button("📄 Summarize")

    with col2:
        quiz_btn = st.button("📝 Generate Quiz")

    with col3:
        target_lang = st.selectbox("Lang", ["Telugu", "Spanish", "Hindi"])

    with col4:
        trans_btn = st.button("🌐 Translate")

    # ---------------- SUMMARY ----------------
    if sum_btn and st.session_state.last_action != "summary":
        st.session_state.last_action = "summary"

        prompt = f"Summarize this in clear points:\n{raw_text}"
        st.session_state.summary_text = safe_call(prompt)

    # ---------------- TRANSLATION ----------------
    if trans_btn and st.session_state.last_action != "translate":
        st.session_state.last_action = "translate"

        prompt = f"Explain this in simple {target_lang}:\n{raw_text}"
        st.session_state.translate_text = safe_call(prompt)
        st.session_state.translate_lang = target_lang

    # ---------------- QUIZ ----------------
    if quiz_btn and st.session_state.last_action != "quiz":
        st.session_state.last_action = "quiz"

        prompt = f"""
Create exactly 3 MCQs.

FORMAT ONLY:
Question | option1, option2, option3 | correct option

No extra text.

Text:
{raw_text}
"""

        response = safe_call(prompt)

        parsed = []

        for line in response.split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    q = parts[0].strip()
                    opts = [o.strip() for o in parts[1].split(",")]
                    ans = parts[2].strip()
                    parsed.append({"q": q, "o": opts, "a": ans})

        st.session_state.quiz_data = parsed

    # ---------------- DISPLAY SUMMARY ----------------
    if st.session_state.current_mode == "summary" or sum_btn:
        if "summary_text" in st.session_state:
            st.markdown(f"""
            <div class="result-container">
            <h2>SUMMARY</h2>
            {st.session_state.summary_text}
            </div>
            """, unsafe_allow_html=True)

    # ---------------- DISPLAY TRANSLATION ----------------
    if st.session_state.current_mode == "translate" or trans_btn:
        if "translate_text" in st.session_state:
            st.markdown(f"""
            <div class="result-container">
            <h2>TRANSLATION ({st.session_state.translate_lang})</h2>
            {st.session_state.translate_text}
            </div>
            """, unsafe_allow_html=True)

    # ---------------- QUIZ UI ----------------
    if st.session_state.current_mode == "quiz" or quiz_btn:

        if st.session_state.quiz_data:

            st.markdown('<div class="result-container"><h2>QUIZ</h2>', unsafe_allow_html=True)

            for i, item in enumerate(st.session_state.quiz_data):
                st.radio(f"Q{i+1}: {item['q']}", item['o'], key=f"q_{i}")

            if st.button("Check Answers"):

                score = 0

                for i, item in enumerate(st.session_state.quiz_data):
                    user_ans = st.session_state.get(f"q_{i}", "")

                    if user_ans.strip() == item["a"].strip():
                        st.success(f"Q{i+1}: Correct ✅")
                        score += 1
                    else:
                        st.error(f"Q{i+1}: Wrong ❌ | Correct: {item['a']}")

                st.metric("Final Score", f"{score} / {len(st.session_state.quiz_data)}")

            st.markdown('</div>', unsafe_allow_html=True)
