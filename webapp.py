import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import re

# --- 1. CONFIGURATION ---
import os
import streamlit as st
import google.generativeai as genai

API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
# Using Gemini 3 for 2026 compatibility
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- 2. SESSION STATE ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None

# --- 2. STYLING (Image 1 & 2 Vibe) ---
st.set_page_config(page_title="AI Study Helper", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #090616 0%, #1e2060 100%); color: white; }
    .result-container { background-color: white; border-radius: 15px; padding: 30px; color: #1e2060; }
    .stRadio > div { background: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Help yourself better learning")

# PDF Upload
uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

if uploaded_file:
    reader = PdfReader(uploaded_file)
    raw_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        raw_text += text
raw_text = raw_text[:8000]

    # Menu Buttons
    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1: sum_btn = st.button("📄 Summarize")
    with col2: quiz_btn = st.button("📝 Generate Quiz")
    with col3: target_lang = st.selectbox("Lang", ["Telugu", "Spanish", "Hindi"], label_visibility="collapsed")
    with col4: trans_btn = st.button("🌐 Translate")

    # --- RESULT LOGIC ---
    if sum_btn:
        st.session_state.current_mode = "summary"
        with st.spinner("Summarizing..."):
            res = model.generate_content(f"Summarize this: {raw_text}")
            st.session_state.summary_text = res.text

    if trans_btn:
        st.session_state.current_mode = "translate"
        with st.spinner("Translating..."):
            res = model.generate_content(f"Explain this in simple {target_lang}: {raw_text}")
            st.session_state.translate_text = res.text
            st.session_state.translate_lang = target_lang

    if quiz_btn:
        st.session_state.current_mode = "quiz"
        with st.spinner("Creating Interactive Quiz..."):
            prompt = f"Create 3 MCQs. Format: Question | Opt1, Opt2, Opt3 | Correct. Text: {raw_text}"
            res = model.generate_content(prompt)
            
            parsed = []
            for line in res.text.strip().split('\n'):
                if "|" in line:
                    p = line.split('|')
                    parsed.append({"q": p[0], "o": p[1].split(','), "a": p[2].strip()})
            st.session_state.quiz_data = parsed

    # --- DISPLAY PERSISTENT RESULTS ---
    if st.session_state.current_mode == "summary" and "summary_text" in st.session_state:
        st.markdown(f'<div class="result-container"><h2>SUMMARIZED</h2>{st.session_state.summary_text}</div>', unsafe_allow_html=True)
        
    elif st.session_state.current_mode == "translate" and "translate_text" in st.session_state:
        lang = st.session_state.translate_lang
        st.markdown(f'<div class="result-container"><h2>TRANSLATED ({lang})</h2>{st.session_state.translate_text}</div>', unsafe_allow_html=True)

    elif st.session_state.current_mode == "quiz" and st.session_state.quiz_data:
        st.markdown('<div class="result-container"><h2 style="color:#9d4edd">INTERACTIVE QUIZ</h2>', unsafe_allow_html=True)
        for i, item in enumerate(st.session_state.quiz_data):
            st.radio(f"Q{i+1}: {item['q']}", item['o'], key=f"quiz_q_{i}")
        
        if st.button("Check Answers"):
            score = 0
            for i, item in enumerate(st.session_state.quiz_data):
                user_ans = st.session_state.get(f"quiz_q_{i}", "")
                if user_ans.strip() == item['a'].strip():
                    st.success(f"Q{i+1}: Correct! ✅")
                    score += 1
                else:
                    st.error(f"Q{i+1}: Incorrect. The correct answer was {item['a']} ❌")
            
            st.metric("Final Score", f"{score} / {len(st.session_state.quiz_data)}")
            if score == len(st.session_state.quiz_data):
                st.balloons()
        st.markdown('</div>', unsafe_allow_html=True)
