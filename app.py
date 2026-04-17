import streamlit as st
import google.generativeai as genai
import io
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الإدارة الذكي للجماعة", layout="wide", page_icon="🏛️")

# --- حل مشكلة الـ 404 (إعداد الذكاء الاصطناعي) ---
MY_API_KEY = "AQ.Ab8RN6LtDoih_ytIju3ulJTIa18hvJdnOpfnAUpn3KMJVDNb1w"
genai.configure(api_key=MY_API_KEY)

# استخدام تسمية الموديل المباشرة (هذا يحل مشكلة الـ 404 في أغلب المناطق)
MODEL_NAME = 'gemini-1.5-flash'

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('commune_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS letters 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  letter_number TEXT,
                  date TEXT, sender TEXT, recipient TEXT, 
                  subject TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_to_archive(letter_num, sender, recipient, subject, content):
    conn = sqlite3.connect('commune_system.db')
    c = conn.cursor()
    c.execute("INSERT INTO letters (letter_number, date, sender, recipient, subject, content) VALUES (?, ?, ?, ?, ?, ?)",
              (letter_num, datetime.now().strftime("%Y-%m-%d %H:%M"), sender, recipient, subject, content))
    conn.commit()
    conn.close()

def get_next_id():
    try:
        conn = sqlite3.connect('commune_system.db')
        c = conn.cursor()
        c.execute("SELECT MAX(id) FROM letters")
        result = c.fetchone()[0]
        conn.close()
        return (result + 1) if result else 1
    except:
        return 1

# --- واجهة المستخدم ---
init_db()
st.title("🏛️ نظام صياغة وأرشفة المراسلات الذكي")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 إنشاء مراسلة جديدة", "🗄️ الأرشيف والبحث"])

with tab1:
    # توليد رقم مراسلة تلقائي (جماعة/السنة/الرقم)
    next_id = get_next_id()
    current_year = datetime.now().year
    auto_letter_num = f"GEM-{current_year}/{next_id:03d}"

    col1, col2 = st.columns(2)
    with col1:
        letter_number = st.text_input("🔢 رقم المراسلة", value=auto_letter_num)
        sender = st.text_input("✍️ من (الجهة المرسلة)", "رئيس الجماعة")
    with col2:
        recipient = st.text_input("📩 إلى (الجهة المستقبلة)")
        subject = st.text_input("📌 الموضوع")

    user_hint = st.text_area("📝 محتوى مختصر (الذكاء الاصطناعي سيتولى التفاصيل):")

    if st.button("✨ صياغة المراسلة الآن"):
        if user_hint:
            with st.spinner("جاري الاتصال بالمحرك وصياغة الخطاب..."):
                try:
                    # المحاولة باستخدام الموديل المحدد
                    model = genai.GenerativeModel(MODEL_NAME)
                    prompt = f"""
                    اكتب خطاباً رسمياً إدارياً مغربياً رصيناً باللغة العربية.
                    رقم المراسلة: {letter_number}
                    من: {sender}
                    إلى: {recipient}
                    الموضوع: {subject}
                    المحتوى الأساسي: {user_hint}
                    تأكد من كتابة التحية الافتتاحية والخاتمة الرسمية.
                    """
                    response = model.generate_content(prompt)
                    st.session_state['draft_content'] = response.text
                except Exception as e:
                    # محاولة أخيرة في حال فشل الموديل المحدد (استخدام الموديل الأساسي)
                    try:
                        model_alt = genai.GenerativeModel('gemini-pro')
                        response = model_alt.generate_content(user_hint)
                        st.session_state['draft_content'] = response.text
                    except:
                        st.error(f"خطأ في الوصول للموديل: {str(e)}")
        else:
            st.warning("يرجى إدخال تفاصيل المراسلة.")

    if 'draft_content' in st.session_state:
        final_content = st.text_area("📄 النص المولد (يمكنك التعديل):", 
                                    value=st.session_state['draft_content'], height=400)
        
        if st.button("💾 حفظ في الأرشيف وتنزيل الملف"):
            save_to_archive(letter_number, sender, recipient, subject, final_content)
            
            # إنشاء ملف Word
            doc = Document()
            doc.add_heading(f"مراسلة رقم: {letter_number}", 1)
            doc.add_paragraph(f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}")
            doc.add_paragraph(f"الموضوع: {subject}")
            doc.add_paragraph("-" * 30)
            doc.add_paragraph(final_content)
            doc.add_paragraph(f"\nتوقيع: {sender}").alignment = 2

            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            st.success(f"تم الحفظ بنجاح تحت رقم: {letter_number}")
            st.download_button("⬇️ تحميل ملف Word", buffer, f"letter_{letter_number}.docx")

with tab2:
    st.subheader("🗄️ سجل الأرشيف")
    conn = sqlite3.connect('commune_system.db')
    df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        st.dataframe(df[['letter_number', 'date', 'recipient', 'subject']], use_container_width=True)
        search_id = st.text_input("أدخل رقم المراسلة لعرض محتواها:")
        if st.button("عرض المحتوى الكامل"):
            res = df[df['letter_number'] == search_id]
            if not res.empty:
                st.write("---")
                st.info(res.iloc[0]['content'])
            else:
                st.error("الرقم غير موجود.")
    else:
        st.write("الأرشيف فارغ.")
