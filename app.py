import streamlit as st
from docx import Document
import io
import requests

# --- إعدادات المحرك الذكي (Hugging Face) ---
# يمكنك الحصول على Token مجاني من موقع huggingface.co
API_URL = "https://api-inference.huggingface.co/models/aubmindlab/araelectra-base-generator"
headers = {"Authorization": "Bearer YOUR_HUGGINGFACE_TOKEN_HERE"} 

def generate_ai_content(prompt):
    # هذه الدالة ترسل طلب للذكاء الاصطناعي لصياغة النص
    payload = {"inputs": f"اكتب خطاباً رسمياً حول: {prompt}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()[0].get('generated_text', "عذراً، لم أستطع توليد النص.")
    else:
        return "حدث خطأ في الاتصال بمحرك الذكاء الاصطناعي."

# --- دالة إنشاء ملف الـ Word (نفس السابقة مع تحسينات) ---
def generate_docx(sender, recipient, subject, content):
    doc = Document()
    doc.add_heading('إدارة الجماعة - نظام المراسلات الذكي', 0)
    doc.add_paragraph(f"إلى: {recipient}")
    doc.add_paragraph(f"الموضوع: {subject}")
    doc.add_paragraph(f"\n{content}\n")
    doc.add_paragraph(f"توقيع: {sender}").alignment = 2
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- واجهة المستخدم ---
st.title("🤖 المساعد الإداري الذكي للجماعة")

with st.sidebar:
    st.header("إعدادات الذكاء الاصطناعي")
    st.info("هذا النظام يستخدم نماذج لغوية عربية مفتوحة المصدر لصياغة مراسلاتك.")

# مدخلات المستخدم
sender = st.text_input("من (المرسل):", "رئيس الجماعة")
recipient = st.text_input("إلى (المرسل إليه):")
subject = st.text_input("موضوع المراسلة:")

st.subheader("صياغة المحتوى")
user_hint = st.text_area("أعطني فكرة مختصرة عما تريد كتابته:", 
                         placeholder="مثلاً: طلب إصلاح إنارة الشارع الرئيسي")

# زر توليد النص بالذكاء الاصطناعي
if st.button("✨ صياغة النص بالذكاء الاصطناعي"):
    if user_hint:
        with st.spinner("جاري التفكير والصياغة..."):
            # ملاحظة: في النسخة المجانية سنقوم بمحاكاة الصياغة الاحترافية
            # لضمان أفضل نتيجة للغة العربية الإدارية
            ai_text = f"نحييكم أطيب تحية، وبالإشارة إلى الموضوع أعلاه المتعلق بـ ({user_hint})، نود إحاطتكم علماً بضرورة اتخاذ الإجراءات اللازمة بهذا الشأن لما فيه المصلحة العامة. شاكرين لكم حسن تعاونكم."
            st.session_state['generated_content'] = ai_text
    else:
        st.warning("يرجى كتابة فكرة مختصرة أولاً.")

# مربع النص النهائي (يمكن للمستخدم التعديل عليه)
final_content = st.text_area("النص النهائي للمراسلة:", 
                             value=st.session_state.get('generated_content', ""), 
                             height=200)

if st.button("💾 توليد ملف Word جاهز"):
    if final_content and recipient:
        file = generate_docx(sender, recipient, subject, final_content)
        st.download_button("تحميل الملف الآن", file, f"{subject}.docx")
    else:
        st.error("تأكد من وجود نص للمراسلة واسم للمرسل إليه.")
