import streamlit as st
import google.generativeai as genai
import io
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الإدارة الذكي للجماعة", layout="wide", page_icon="🏛️")

# --- إعداد الذكاء الاصطناعي (المكتبة المستقرة) ---
MY_API_KEY = "AQ.Ab8RN6LtDoih_ytIju3ulJTIa18hvJdnOpfnAUpn3KMJVDNb1w"
genai.configure(api_key=MY_API_KEY)

# استخدام موديل مستقر جداً ومتاح عالمياً
model = genai.GenerativeModel('gemini-1.5-flash')

# --- وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('commune_system.db')
    c = conn.cursor()
    # إضافة حقل letter_number للجدول
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
    conn = sqlite3.connect('commune_system.db')
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM letters")
    result = c.fetchone()[0]
    conn.close()
    return (result + 1) if result else 1

# --- بناء الواجهة ---
init_db()
st.title("🏛️ نظام صياغة وأرشفة المراسلات الذكي")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 إنشاء مراسلة جديدة", "🗄️ الأرشيف والبحث"])

with tab1:
    # توليد رقم مراسلة تلقائي (السنة / الرقم التسلسلي)
    next_id = get_next_id()
    current_year = datetime.now().year
    auto_letter_num = f"ج/{current_year}/{next_id:04d}"

    col1, col2 = st.columns(2)
    with col1:
        letter_number = st.text_input("رقم المراسلة", value=auto_letter_num)
        sender = st.text_input("من (الجهة المرسلة)", "رئيس الجماعة")
    with col2:
        recipient = st.text_input("إلى (الجهة المستقبلة)")
        subject = st.text_input("الموضوع")

    user_hint = st.text_area("عن ماذا تريد كتابة المراسلة؟ (اكتب تفاصيل بسيطة هنا)")

    if st.button("✨ صياغة المراسلة بالذكاء الاصطناعي"):
        if user_hint:
            with st.spinner("جاري صياغة الخطاب بأسلوب رسمي..."):
                try:
                    prompt = f"اكتب خطاباً رسمياً إدارياً باللغة العربية. رقم المراسلة: {letter_number}. من: {sender}. إلى: {recipient}. الموضوع: {subject}. التفاصيل: {user_hint}. تأكد من استخدام لغة رصينة وتحية رسمية وخاتمة."
                    response = model.generate_content(prompt)
                    st.session_state['draft_content'] = response.text
                except Exception as e:
                    st.error(f"حدث خطأ في الاتصال بمحرك الذكاء الاصطناعي: {str(e)}")
        else:
            st.warning("يرجى كتابة تفاصيل المراسلة أولاً.")

    if 'draft_content' in st.session_state:
        final_content = st.text_area("نص المراسلة الناتج (يمكنك التعديل عليه):", 
                                    value=st.session_state['draft_content'], height=400)
        
        if st.button("💾 اعتماد وحفظ في الأرشيف"):
            save_to_archive(letter_number, sender, recipient, subject, final_content)
            
            # إنشاء ملف Word
            doc = Document()
            doc.add_heading(f"مراسلة رقم: {letter_number}", 1)
            doc.add_paragraph(f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}")
            doc.add_paragraph(f"من: {sender}")
            doc.add_paragraph(f"إلى: {recipient}")
            doc.add_paragraph(f"الموضوع: {subject}")
            doc.add_paragraph("-" * 20)
            doc.add_paragraph(final_content)
            doc.add_paragraph(f"\nتوقيع: {sender}").alignment = 2

            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            st.success(f"تم حفظ المراسلة رقم {letter_number} في الأرشيف!")
            st.download_button("تحميل الخطاب كملف Word", buffer, f"مراسلة_{letter_number}.docx")

with tab2:
    st.subheader("🗄️ سجل المراسلات الإدارية")
    conn = sqlite3.connect('commune_system.db')
    df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        # عرض الجدول مع رقم المراسلة
        st.dataframe(df[['letter_number', 'date', 'recipient', 'subject']], use_container_width=True)
        
        search_num = st.text_input("ابحث عن محتوى مراسلة برقمها:")
        if st.button("عرض التفاصيل"):
            record = df[df['letter_number'] == search_num]
            if not record.empty:
                st.info(f"**نص المراسلة:**\n\n{record.iloc[0]['content']}")
            else:
                st.error("لم يتم العثور على مراسلة بهذا الرقم.")
    else:
        st.write("الأرشيف فارغ حالياً.")
