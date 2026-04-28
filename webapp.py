import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# ---------------- CONFIG ----------------
import os

API_KEY = st.secrets["GEMINI_API_KEY"]  # use Streamlit secrets (IMPORTANT)
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------- SESSION STATE ----------------
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="AI Study Helper", layout="wide")

st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #090616 0%, #1e2060 100%);
        color: white;
    }
    .result-container {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 AI Study Helper")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

raw_text = ""

if uploaded_file is not None:
    reader = PdfReader(uploaded_file)

    for page in reader.pages:
        text = page.extract_text()
        if text:
            raw_text += text

    raw_text = raw_text[:8000]

# ---------------- BUTTONS (ALWAYS VISIBLE) ----------------
st.write("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    sum_btn = st.button("📄 Summarize")

with col2:
    quiz_btn = st.button("📝 Generate Quiz")

with col3:
    target_lang = st.selectbox("Language", ["Telugu", "Spanish", "Hindi"])

with col4:
    trans_btn = st.button("🌐 Translate")

# ---------------- ACTION LOGIC ----------------
if uploaded_file is not None and raw_text:

    # -------- SUMMARIZE --------
    if sum_btn:
        st.session_state.current_mode = "summary"

        with st.spinner("Summarizing..."):
            res = model.generate_content("Summarize this:\n" + raw_text)
            st.session_state.summary_text = res.text

    # -------- TRANSLATE --------
    if trans_btn:
        st.session_state.current_mode = "translate"

        with st.spinner("Translating..."):
            res = model.generate_content(
                f"Explain this in simple {target_lang}:\n{raw_text}"
            )
            st.session_state.translate_text = res.text
            st.session_state.translate_lang = target_lang

    # -------- QUIZ --------
    if quiz_btn:
        st.session_state.current_mode = "quiz"

        with st.spinner("Generating Quiz..."):
            prompt = f"""
Create exactly 3 MCQs.

Format:
Question | Option1, Option2, Option3 | CorrectOption

Text:
{raw_text}
"""

            res = model.generate_content(prompt)

            parsed = []

            if res and res.text:
                for line in res.text.split("\n"):
                    if "|" in line:
                        parts = line.split("|")

                        if len(parts) == 3:
                            parsed.append({
                                "q": parts[0].strip(),
                                "o": [x.strip() for x in parts[1].split(",")],
                                "a": parts[2].strip()
                            })

            st.session_state.quiz_data = parsed

else:
    st.info("📄 Please upload a PDF to start")

# ---------------- OUTPUT DISPLAY ----------------

# -------- SUMMARY --------
if st.session_state.current_mode == "summary" and "summary_text" in st.session_state:
    st.markdown(
        f"<div class='result-container'><h3>SUMMARY</h3>{st.session_state.summary_text}</div>",
        unsafe_allow_html=True
    )

# -------- TRANSLATE --------
elif st.session_state.current_mode == "translate" and "translate_text" in st.session_state:
    st.markdown(
        f"<div class='result-container'><h3>TRANSLATION ({st.session_state.translate_lang})</h3>{st.session_state.translate_text}</div>",
        unsafe_allow_html=True
    )

# -------- QUIZ --------
elif st.session_state.current_mode == "quiz":

    if st.session_state.quiz_data:

        st.markdown("<div class='result-container'><h3>QUIZ</h3>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.quiz_data):
            st.radio(
                f"Q{i+1}: {item['q']}",
                item["o"],
                key=f"q_{i}"
            )

        if st.button("Check Answers"):

            score = 0

            for i, item in enumerate(st.session_state.quiz_data):
                user_ans = st.session_state.get(f"q_{i}")

                if user_ans == item["a"]:
                    st.success(f"Q{i+1} Correct ✅")
                    score += 1
                else:
                    st.error(f"Q{i+1} Wrong ❌ (Ans: {item['a']})")

            st.metric("Score", f"{score}/{len(st.session_state.quiz_data)}")

            if score == len(st.session_state.quiz_data):
                st.balloons()

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("No quiz generated. Try again.")
