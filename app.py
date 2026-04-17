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

# --- الإعدادات التقنية (الحل النهائي للـ 404) ---
API_KEY = "AQ.Ab8RN6LtDoih_ytIju3ulJTIa18hvJdnOpfnAUpn3KMJVDNb1w"

# استخدمنا هنا gemini-pro لأنه الموديل الأكثر شمولية وقبولاً
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"

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
            return response_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # محاولة أخيرة برابط v1 عادي إذا فشل v1beta
            alt_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"
            alt_res = requests.post(alt_url, headers=headers, data=json.dumps(data))
            if alt_res.status_code == 200:
                return alt_res.json()['candidates'][0]['content']['parts'][0]['text']
            return f"خطأ من جوجل: {response_json.get('error', {}).get('message', 'يرجى التأكد من تفعيل الموديل في إعدادات API Studio')}"
    except Exception as e:
        return f"فشل الاتصال: {str(e)}"

# --- نظام الأرشفة ورقم المراسلة ---
def init_db():
    conn = sqlite3.connect('commune_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS letters 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  letter_number TEXT, date TEXT, sender TEXT, 
                  recipient TEXT, subject TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def get_next_num():
    conn = sqlite3.connect('commune_final.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM letters")
    count = c.fetchone()[0]
    conn.close()
    return f"N°-{datetime.now().year}/{count + 1:03d}"

# --- الواجهة ---
init_db()
st.title("🏛️ النظام الإداري الموحد")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("إدخال البيانات")
    letter_num = st.text_input("رقم المراسلة التلقائي", value=get_next_num())
    sender = st.text_input("من", "رئيس الجماعة")
    recipient = st.text_input("إلى")
    subject = st.text_input("الموضوع")
    hint = st.text_area("وصف سريع للمحتوى")
    generate_btn = st.button("✨ صياغة الخطاب")

with col2:
    st.subheader("المعاينة والتحميل")
    if generate_btn:
        if hint:
            with st.spinner("جاري الاتصال بالموديل المستقر..."):
                full_prompt = f"أنت مساعد إداري خبير. اكتب خطاباً رسمياً بأسلوب رصين. الرقم: {letter_num}. من: {sender}. إلى: {recipient}. الموضوع: {subject}. المحتوى: {hint}."
                st.session_state['final_txt'] = call_gemini_api(full_prompt)
        else:
            st.error("أدخل تفاصيل المحتوى أولاً.")

    if 'final_txt' in st.session_state:
        final_text = st.text_area("النص المولد (قابلة للتعديل):", value=st.session_state['final_txt'], height=400)
        
        if st.button("💾 حفظ في الأرشيف وتنزيل Word"):
            # حفظ قاعدة البيانات
            conn = sqlite3.connect('commune_final.db')
            c = conn.cursor()
            c.execute("INSERT INTO letters (letter_number, date, sender, recipient, subject, content) VALUES (?,?,?,?,?,?)",
                      (letter_num, datetime.now().strftime("%Y-%m-%d"), sender, recipient, subject, final_text))
            conn.commit()
            conn.close()
            
            # تصدير Word
            doc = Document()
            doc.add_heading(f"مراسلة رقم: {letter_num}", 1)
            doc.add_paragraph(final_text)
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            
            st.success("تم الحفظ في الأرشيف!")
            st.download_button("تحميل الملف النهائي", buf, f"letter_{letter_num}.docx")

st.markdown("---")
st.subheader("🗄️ سجل المراسلات")
conn = sqlite3.connect('commune_final.db')
df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
conn.close()
st.dataframe(df, use_container_width=True)
