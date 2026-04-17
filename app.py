import streamlit as st
import google.generativeai as genai
import io
import sqlite3
import pandas as pd
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام جماعة أسكاون الذكي", layout="wide")

# --- 2. إعداد الذكاء الاصطناعي ---
# استخدم مفتاح الـ API الخاص بك
MY_API_KEY = "AQ.Ab8RN6LtDoih_ytIju3ulJTIa18hvJdnOpfnAUpn3KMJVDNb1w"
genai.configure(api_key=MY_API_KEY)

@st.cache_resource
def get_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except:
        return "models/gemini-1.5-flash"

active_model = get_model()

# --- 3. وظائف قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('askaouen_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS letters 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  letter_num TEXT, date TEXT, sender TEXT, 
                  recipient TEXT, subject TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def get_next_num():
    try:
        conn = sqlite3.connect('askaouen_final.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM letters")
        count = c.fetchone()[0]
        conn.close()
        # يبدأ من الرقم 7 كما في نموذجك 
        return f"{count + 7:02d}/2026"
    except:
        return "07/2026"

# --- 4. دالة تنسيق ملف Word (المعايير المغربية) ---
def create_doc(l_num, date_str, sender, recipient, subject, content):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(12)

    # الرأس (يمين: الإدارة / يسار: التاريخ) [cite: 1, 3]
    tbl = doc.add_table(rows=1, cols=2)
    tbl.width = Inches(6)
    
    r_cell = tbl.cell(0, 0)
    p_r = r_cell.add_paragraph()
    p_r.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_r.add_run("المملكة المغربية\nوزارة الداخلية\nإقليم تارودانت\nدائرة تالوين\nجماعة أسكاون").bold = True
    
    l_cell = tbl.cell(0, 1)
    p_l = l_cell.add_paragraph()
    p_l.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_l.add_run(f"أسكاون في: {date_str}")

    doc.add_paragraph()
    # رقم المراسلة 
    doc.add_paragraph(f"عدد: {l_num}").alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # من ... إلى [cite: 4, 5, 6]
    doc.add_paragraph(f"\n{sender}\nإلى\n{recipient}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # الموضوع [cite: 7]
    doc.add_paragraph(f"\nالموضوع: {subject}").bold = True
    
    # التحية الرسمية [cite: 8]
    p_salut = doc.add_paragraph("\nسلام تام بوجود مولانا الإمام،")
    p_salut.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_salut.bold = True

    # النص [cite: 9]
    p_body = doc.add_paragraph(f"\nوبعد، {content}")
    p_body.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # الخاتمة والتوقيع [cite: 10, 11]
    doc.add_paragraph("\nوتقبلوا اسمى عبارات التقدير والاحترام.").alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph("\nرئيس المجلس الجماعي").alignment = WD_ALIGN_PARAGRAPH.LEFT

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# --- 5. واجهة المستخدم ---
init_db()
st.title("🏛️ نظام مراسلات جماعة أسكاون")

tab1, tab2 = st.tabs(["📝 تحرير جديد", "🗄️ الأرشيف"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        num = st.text_input("رقم المراسلة", value=get_next_num())
        dt = st.text_input("التاريخ", value="12 يناير 2026")
        snd = st.text_input("من", value="رئيس جماعة أسكاون")
    with c2:
        rcp = st.text_input("إلى", value="السيد القابض الجماعي بتالوين")
        sub = st.text_input("الموضوع", value="حضور جلسة فتح الاظرفة")
    
    hint = st.text_area("أدخل تفاصيل الطلب (ليتم صياغتها ذكياً):")
    
    if st.button("🚀 توليد وصياغة"):
        if hint:
            model = genai.GenerativeModel(active_model)
            p = f"اكتب خطاباً إدارياً مغربياً. الموضوع: {sub}. المحتوى: {hint}. استخدم أسلوب 'يشرفني دعوتكم'."
            res = model.generate_content(p)
            st.session_state['txt'] = res.text
    
    if 'txt' in st.session_state:
        edited = st.text_area("النص المولد:", value=st.session_state['txt'], height=300)
        if st.button("💾 حفظ وتحميل"):
            conn = sqlite3.connect('askaouen_final.db')
            conn.cursor().execute("INSERT INTO letters (letter_num, date, sender, recipient, subject, content) VALUES (?,?,?,?,?,?)",
                                  (num, dt, snd, rcp, sub, edited))
            conn.commit()
            conn.close()
            file = create_doc(num, dt, snd, rcp, sub, edited)
            st.download_button("تحميل الملف (.docx)", file, f"{num.replace('/', '-')}.docx")

with tab2:
    conn = sqlite3.connect('askaouen_final.db')
    df = pd.read_sql_query("SELECT * FROM letters ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
