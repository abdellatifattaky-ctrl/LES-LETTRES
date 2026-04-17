# أولاً: يجب تثبيت المكتبة عبر الأمر: pip install python-docx

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_letter(sender, recipient, subject, body):
    # إنشاء مستند جديد
    doc = Document()

    # إضافة عنوان (ترويسة)
    header = doc.add_heading('خطاب رسمي - إدارة الجماعة', 0)
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # إضافة تفاصيل المرسل إليه
    p = doc.add_paragraph()
    p.add_run(f'إلى السيد/ة: {recipient}').bold = True
    
    # إضافة الموضوع
    p = doc.add_paragraph()
    p.add_run(f'الموضوع: {subject}').bold = True

    # إضافة نص الرسالة
    doc.add_paragraph(f'\n{body}\n')

    # إضافة التوقيع
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.LEFT
    footer.add_run(f'\nمع تحيات: {sender}')

    # حفظ الملف
    filename = f"letter_to_{recipient}.docx"
    doc.save(filename)
    print(f"تم إنشاء المراسلة بنجاح: {filename}")

# مثال على التشغيل
create_letter(
    sender="رئيس الجماعة",
    recipient="مدير القسم التقني",
    subject="طلب صيانة دورية",
    body="نرجو منكم التكرم بإرسال فريق الصيانة لمقر الجماعة يوم الخميس القادم."
)
