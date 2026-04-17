import streamlit as st
import google.generativeai as genai
import io
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الإدارة الذكي للجماعة", layout="wide")

# --- إعداد المفتاح والبحث عن الموديل المتاح ---
MY_API_KEY = "AQ.Ab8RN6LtDoih_ytIju3ulJTIa18hvJdnOpfnAUpn3KMJVDNb1w"
genai.configure(api_key=MY_API_KEY)

@st.cache_resource
def get_available_model():
    # هذه الوظيفة تبحث في حسابك عن الموديل الذي تسمح به جوجل
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name # سيعيد أول موديل متاح (مثل gemini-1.5-flash أو gemini-pro)
    except:
        return "models/gemini-pro" # كخيار احتياطي

active_model_name = get_available_model()

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('commune_final_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS letters 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  letter_number TEXT, date TEXT, sender TEXT, 
                  recipient TEXT, subject TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def get_next_num():
    try:
        conn = sqlite3.connect('commune_final_v3.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM letters")
        count = c.fetchone()[0]
        conn.close()
        return f"REF-{datetime.now().year}/{count + 1:03d}"
    except: return "REF-001"

# --- واجهة المستخدم ---
init_db()
st.title("🏛️ النظام الإداري المتطور")
st.caption(f"الموديل النشط حالياً في حسابك: {active_model_name}")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("📝 بيانات المراسلة")
    l_num = st.text_input("رقم المراسلة", value=get_next_num())
    sender = st.text_input("من", "رئيس الجماعة")
    recipient = st.text_input("إلى")
    subject = st.text_input("الموضوع")
    hint = st.text_area("عن ماذا سيتحدث الخطاب؟")
    
    generate_btn = st.button("🚀 صياغة بالذكاء الاصطناعي")

with col2:
    st.subheader("📄 المعاينة")
    if generate_btn:
        if hint:
            with st.spinner("جاري التوليد باستخدام الموديل المتاح في حسابك..."):
                try:
                    model = genai.GenerativeModel(active_model_name)
                    prompt = f"اكتب خطاباً رسمياً بأسلوب إداري. الرقم: {l_num}. المرسل: {sender}. المرسل إليه: {recipient}. الموضوع: {subject}. المحتوى: {hint}."
                    response = model.generate_content(prompt)
                    st.session_state['text_out'] = response.text
                except Exception as e:
                    st.error(f"فشل التوليد: {str(e)}")
        else:
            st.warning("أدخل تفاصيل المحتوى.")

    if 'text_out' in st.session_state:
        final_text = st.text_area("النص المولد:", value=st.session_state['text_out'], height=350)
        
        if st.button("💾 حفظ في الأرشيف وتنزيل"):
            # حفظ في قاعدة البيانات
            conn = sqlite3.connect('commune_final_v3.db')
            c = conn.cursor()
            c.execute("INSERT INTO letters (letter_number, date, sender, recipient, subject, content) VALUES (?,?,?,?,?,?)",
                      (l_num, datetime.now().strftime("%Y-%m-%d"), sender, recipient, subject, final_text))
            conn.commit()
            conn.close()
            
            # ملف Word
            doc = Document()
            doc.add_heading(f"مراسلة رقم: {l_num}", 1)
            doc.add_paragraph(final_text)
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            st.download_button("تحميل الملف", buf, f"letter_{l_num}.docx")

st.markdown("---")
st.subheader("🗄️ الأرشيف")
conn = sqlite3.connect('commune_final_v3.db')
df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
conn.close()
st.dataframe(df, use_container_width=True)
