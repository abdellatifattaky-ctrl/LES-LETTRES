import streamlit as st
import requests
import json
import io
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الإدارة الذكي للجماعة", layout="wide")

# --- إعدادات الاتصال المباشر بـ Gemini ---
API_KEY = "AQ.Ab8RN6LtDoih_ytIju3ulJTIa18hvJdnOpfnAUpn3KMJVDNb1w"
# استخدام الرابط المباشر للإصدار المستقر v1
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def call_gemini_api(prompt):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        response_json = response.json()
        
        if response.status_code == 200:
            # استخراج النص من الاستجابة الرسمية
            return response_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"خطأ من Google: {response_json.get('error', {}).get('message', 'خطأ غير معروف')}"
    except Exception as e:
        return f"فشل الاتصال بالخادم: {str(e)}"

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('commune_safe_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS letters 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  letter_number TEXT, date TEXT, sender TEXT, 
                  recipient TEXT, subject TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def get_next_letter_num():
    conn = sqlite3.connect('commune_safe_system.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM letters")
    count = c.fetchone()[0]
    conn.close()
    return f"GEM-{datetime.now().year}/{count + 1:03d}"

# --- واجهة المستخدم ---
init_db()
st.title("🏛️ نظام المراسلات الإداري (النسخة المستقرة)")

tab1, tab2 = st.tabs(["📝 إنشاء مراسلة", "🗄️ الأرشيف"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        l_num = st.text_input("رقم المراسلة", value=get_next_letter_num())
        sender = st.text_input("المرسل", "رئيس الجماعة")
    with col2:
        recipient = st.text_input("المرسل إليه")
        subject = st.text_input("الموضوع")

    hint = st.text_area("وصف المراسلة:")

    if st.button("✨ صياغة بالذكاء الاصطناعي"):
        if hint:
            with st.spinner("جاري التوليد عبر الرابط المستقر..."):
                full_prompt = f"اكتب خطاباً رسمياً إدارياً باللغة العربية. الرقم: {l_num}. من: {sender}. إلى: {recipient}. الموضوع: {subject}. المحتوى: {hint}."
                result = call_gemini_api(full_prompt)
                st.session_state['result_text'] = result
        else:
            st.error("يرجى إدخال الوصف.")

    if 'result_text' in st.session_state:
        final_text = st.text_area("النص المولد:", value=st.session_state['result_text'], height=300)
        
        if st.button("💾 حفظ وتنزيل"):
            # حفظ في الأرشيف
            conn = sqlite3.connect('commune_safe_system.db')
            c = conn.cursor()
            c.execute("INSERT INTO letters (letter_number, date, sender, recipient, subject, content) VALUES (?,?,?,?,?,?)",
                      (l_num, datetime.now().strftime("%Y-%m-%d"), sender, recipient, subject, final_text))
            conn.commit()
            conn.close()
            
            # تصدير Word
            doc = Document()
            doc.add_heading(f"مراسلة رقم: {l_num}", 1)
            doc.add_paragraph(final_text)
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            
            st.success("تم الحفظ!")
            st.download_button("تحميل الملف", buf, f"letter_{l_num}.docx")

with tab2:
    conn = sqlite3.connect('commune_safe_system.db')
    df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df[['letter_number', 'date', 'recipient', 'subject']])
    else:
        st.write("الأرشيف فارغ.")
