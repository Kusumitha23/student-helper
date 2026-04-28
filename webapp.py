import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found in environment variables")
    st.stop()

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- 2. SESSION STATE ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None

# --- 3. UI ---
st.set_page_config(page_title="AI Study Helper", layout="wide")

st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #090616 0%, #1e2060 100%); color: white; }
    .result-container { background-color: white; border-radius: 15px; padding: 30px; color: #1e2060; }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 AI Study Helper")

# --- 4. PDF UPLOAD ---
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:

    reader = PdfReader(uploaded_file)

    raw_text = ""
    for page in reader.pages:
        raw_text += page.extract_text() or ""

    # IMPORTANT FIX: limit input size
    raw_text = raw_text[:3000]

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

    # --- SAFE GEMINI CALL WRAPPER ---
    def safe_call(prompt):
        try:
            return model.generate_content(prompt).text
        except Exception:
            return "⚠️ API limit reached or request too large. Try again after some time."

    # --- SUMMARY ---
    if sum_btn:
        st.session_state.current_mode = "summary"

        prompt = f"Summarize this clearly in simple points:\n{raw_text}"
        st.session_state.summary_text = safe_call(prompt)

    # --- TRANSLATION ---
    if trans_btn:
        st.session_state.current_mode = "translate"

        prompt = f"Explain this in simple {target_lang}:\n{raw_text}"
        st.session_state.translate_text = safe_call(prompt)
        st.session_state.translate_lang = target_lang

    # --- QUIZ ---
    if quiz_btn:
        st.session_state.current_mode = "quiz"

        prompt = f"""
Create exactly 3 MCQs from this text.

Format strictly:
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

    # --- DISPLAY SUMMARY ---
    if st.session_state.current_mode == "summary" and "summary_text" in st.session_state:
        st.markdown(f"""
        <div class="result-container">
        <h2>SUMMARY</h2>
        {st.session_state.summary_text}
        </div>
        """, unsafe_allow_html=True)

    # --- DISPLAY TRANSLATION ---
    elif st.session_state.current_mode == "translate" and "translate_text" in st.session_state:
        st.markdown(f"""
        <div class="result-container">
        <h2>TRANSLATION ({st.session_state.translate_lang})</h2>
        {st.session_state.translate_text}
        </div>
        """, unsafe_allow_html=True)

    # --- QUIZ UI ---
    elif st.session_state.current_mode == "quiz" and st.session_state.quiz_data:

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

            st.metric("Score", f"{score} / {len(st.session_state.quiz_data)}")

        st.markdown('</div>', unsafe_allow_html=True)
