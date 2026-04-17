import streamlit as st
from google import genai
from google.genai import types
import io
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام ذكاء الجماعة المتكامل", layout="wide", page_icon="🏛️")

# --- دمج مفتاح الـ API الخاص بك ---
MY_API_KEY = "AQ.Ab8RN6LtDoih_ytIju3ulJTIa18hvJdnOpfnAUpn3KMJVDNb1w"

# تهيئة العميل
try:
    client = genai.Client(api_key=MY_API_KEY)
except Exception as e:
    st.error(f"فشل الاتصال بـ Google API: {e}")

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('commune_archive.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS letters 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, sender TEXT, recipient TEXT, 
                  subject TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_to_archive(sender, recipient, subject, content):
    conn = sqlite3.connect('commune_archive.db')
    c = conn.cursor()
    c.execute("INSERT INTO letters (date, sender, recipient, subject, content) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M"), sender, recipient, subject, content))
    conn.commit()
    conn.close()

# --- دالة التوليد (تعديل صيغة الموديل) ---
def generate_ai_letter(prompt_details):
    try:
        # ملاحظة: في المكتبة الجديدة نستخدم الاسم المباشر للموديل
        # جربنا gemini-1.5-flash، وإذا فشل سنستخدم الإصدار التجريبي المتاح عالمياً
        model_name = "gemini-1.5-flash" 
        
        # تفعيل البحث من جوجل
        search_tool = types.Tool(google_search=types.GoogleSearch())
        
        config = types.GenerateContentConfig(
            tools=[search_tool],
            system_instruction="أنت مساعد إداري خبير. صغ المراسلات باللغة العربية الرسمية."
        )

        # استدعاء التوليد
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_details,
            config=config,
        )
        
        # استخراج النص الناتج
        return response.text
    except Exception as e:
        # إذا استمر الخطأ، سنقوم بتجربة استدعاء مبسط جداً كخطة بديلة
        try:
            simple_response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"اكتب خطاباً رسمياً عن: {prompt_details}"
            )
            return simple_response.text
        except:
            return f"عذراً، لا يزال هناك تعارض في الموديل: {str(e)}"

# --- واجهة المستخدم ---
init_db()

st.title("🏛️ نظام الإدارة الذكي للجماعة")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 إنشاء مراسلة", "🗄️ الأرشيف الإلكتروني"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        sender = st.text_input("جهة الإرسال", "رئيس الجماعة")
        recipient = st.text_input("المرسل إليه")
    with col2:
        subject = st.text_input("الموضوع")
        user_hint = st.text_area("وصف سريع للمطلوب:")

    if st.button("✨ صياغة بواسطة الذكاء الاصطناعي"):
        if user_hint:
            with st.spinner("جاري معالجة الطلب..."):
                result = generate_ai_letter(user_hint)
                st.session_state['current_draft'] = result
        else:
            st.warning("أدخل تفاصيل المراسلة أولاً.")

    if 'current_draft' in st.session_state:
        final_text = st.text_area("النص الناتج:", value=st.session_state['current_draft'], height=300)
        
        if st.button("💾 حفظ وتنزيل"):
            save_to_archive(sender, recipient, subject, final_text)
            
            doc = Document()
            doc.add_heading(subject, 0)
            doc.add_paragraph(final_text)
            
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            st.success("تم الحفظ!")
            st.download_button("تحميل الملف (Word)", output, f"{subject}.docx")

with tab2:
    st.subheader("المراسلات السابقة")
    conn = sqlite3.connect('commune_archive.db')
    df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df[['id', 'date', 'recipient', 'subject']], use_container_width=True)
        search_id = st.number_input("أدخل رقم المراسلة لعرضها", min_value=1, step=1)
        if st.button("فتح من السجل"):
            content = df[df['id'] == search_id]['content'].values
            if len(content) > 0:
                st.info(content[0])
    else:
        st.write("الأرشيف فارغ.")
