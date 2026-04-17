import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام مراسلات الجماعة ذكي", page_icon="📝")

# --- دالة إنشاء ملف الـ Word ---
def generate_docx(sender, recipient, subject, content):
    doc = Document()
    
    # تنسيق الخط العام للمستند
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(14)

    # إضافة عنوان الخطاب
    header = doc.add_heading('المملكة - إدارة الجماعة', 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # تفاصيل المراسلة
    p1 = doc.add_paragraph()
    p1.add_run(f"إلى السيد/ة: {recipient}").bold = True
    
    p2 = doc.add_paragraph()
    p2.add_run(f"الموضوع: {subject}").bold = True

    # نص الخطاب
    doc.add_paragraph("\nتحية طيبة وبعد،،\n")
    doc.add_paragraph(content)

    # التوقيع
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p3.add_run(f"\n\nتوقيع: {sender}").bold = True

    # حفظ المستند في ذاكرة مؤقتة (Buffer) لكي نتمكن من تحميله عبر المتصفح
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- واجهة المستخدم (Streamlit UI) ---
st.title("🏛️ نظام إدارة وتوليد المراسلات الذكي")
st.markdown("استخدم هذا النموذج لتوليد الخطابات الرسمية وحفظها.")

with st.form("letter_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        sender_name = st.text_input("اسم المرسل (أو المنصب)", value="رئيس الجماعة")
        recipient_name = st.text_input("اسم المرسل إليه", placeholder="مثال: مدير المصالح")
    
    with col2:
        subject = st.text_input("موضوع المراسلة", placeholder="مثال: طلب ترخيص")
        
    content = st.text_area("نص المراسلة (محتوى الخطاب)", height=200, 
                           placeholder="اكتب هنا تفاصيل الخطاب...")

    submitted = st.form_submit_button("توليد الملف المعاين")

# --- معالجة البيانات بعد الضغط على الزر ---
if submitted:
    if sender_name and recipient_name and subject and content:
        # توليد الملف
        docx_file = generate_docx(sender_name, recipient_name, subject, content)
        
        st.success("✅ تم تجهيز المراسلة بنجاح!")
        
        # زر التحميل
        st.download_button(
            label="تحميل الخطاب بصيغة Word",
            data=docx_file,
            file_name=f"مراسلة_{recipient_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        st.error("يرجى ملء جميع الحقول المطلوبة.")
