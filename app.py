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
client = genai.Client(api_key=MY_API_KEY)

# --- وظائف قاعدة البيانات (الأرشيف) ---
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

# --- دالة التوليد المحدثة (نسخة مستقرة) ---
def generate_ai_letter(prompt_details):
    try:
        # استخدام الموديل المستقر لتجنب خطأ 404
        model_id = "gemini-1.5-flash" 
        
        # تفعيل أدوات البحث في جوجل لضمان دقة المعلومات
        tools = [types.Tool(google_search=types.GoogleSearch())]
        
        config = types.GenerateContentConfig(
            tools=tools,
            system_instruction="أنت خبير في الإدارة العمومية والمراسلات الرسمية. صغ خطاباً رسمياً بأسلوب رصين ومنظم."
        )

        response = client.models.generate_content(
            model=model_id,
            contents=f"قم بصياغة مراسلة رسمية عربية احترافية حول الموضوع التالي: {prompt_details}",
            config=config,
        )
        return response.text
    except Exception as e:
        return f"عذراً، حدث خطأ: {str(e)}"

# --- بناء واجهة المستخدم ---
init_db()

st.title("🏛️ نظام الإدارة الذكي للجماعة")
st.info("تم تحديث النظام إلى النسخة المستقرة Gemini 1.5 Flash لضمان سرعة الاستجابة.")

tab1, tab2 = st.tabs(["📝 إنشاء مراسلة", "🗄️ الأرشيف الإلكتروني"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        sender = st.text_input("جهة الإرسال", "رئيس الجماعة")
        recipient = st.text_input("المرسل إليه", placeholder="مثال: السيد مدير المصالح")
    with col2:
        subject = st.text_input("موضوع المراسلة")
        
    user_hint = st.text_area("وصف مختصر للمطلوب صياغته:")

    if st.button("✨ توليد النص بالذكاء الاصطناعي"):
        if user_hint:
            with st.spinner("جاري الصياغة والتحقق..."):
                full_text = generate_ai_letter(user_hint)
                st.session_state['current_draft'] = full_text
        else:
            st.error("الرجاء كتابة وصف بسيط للمراسلة.")

    if 'current_draft' in st.session_state:
        edited_text = st.text_area("النص المقترح (يمكنك التعديل):", 
                                   value=st.session_state['current_draft'], height=350)
        
        if st.button("💾 حفظ في الأرشيف وتنزيل الملف"):
            save_to_archive(sender, recipient, subject, edited_text)
            
            # إنشاء ملف Word
            doc = Document()
            doc.add_heading(subject, 0)
            doc.add_paragraph(f"بتاريخ: {datetime.now().strftime('%Y-%m-%d')}")
            doc.add_paragraph(f"إلى: {recipient}")
            doc.add_paragraph("\n" + edited_text)
            doc.add_paragraph(f"\nتوقيع: {sender}").alignment = 2
            
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            st.success("تم الحفظ في الأرشيف!")
            st.download_button("تحميل المراسلة (Word)", output, f"{subject}.docx")

with tab2:
    st.subheader("سجل المراسلات المؤرشفة")
    conn = sqlite3.connect('commune_archive.db')
    df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df[['id', 'date', 'recipient', 'subject']], use_container_width=True)
        search_id = st.number_input("أدخل رقم العملية لعرض التفاصيل", min_value=1, step=1)
        if st.button("فتح الملف"):
            content = df[df['id'] == search_id]['content'].values
            if len(content) > 0:
                st.markdown("---")
                st.write(content[0])
            else:
                st.error("رقم المراسلة غير موجود.")
    else:
        st.write("الأرشيف لا يحتوي على أي سجلات حالياً.")
