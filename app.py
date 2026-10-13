import streamlit as st
from PIL import Image
from io import BytesIO
import json
from urllib.parse import quote

st.set_page_config(page_title='ธนศิลป์ AI Design',page_icon='🎨',layout='wide')
st.markdown('''<style>.block-container{max-width:1150px;padding-top:1.5rem}h1{color:#173a68}div.stButton>button[kind="primary"]{background:#16447c;border:0} </style>''',unsafe_allow_html=True)
st.title('🎨 ธนศิลป์ AI Design')
st.caption('ระบบออกแบบป้าย • เลือกตัวเลือก อัปโหลดรูป 3 ช่อง แล้วสร้างคำสั่งพร้อมใช้กับ ChatGPT — ไม่ต้องใช้ API Key')

WORK=['ออกแบบป้ายใหม่','แก้ไขภาพเดิม','ปรับคุณภาพ Ultra-Sharp','แปลงเป็นเวกเตอร์','ลบข้อความคงพื้นหลัง','เปลี่ยนสีและองค์ประกอบ','ปรับขนาดภาพ','สร้างพื้นหลังเปล่า','Depth Map / CNC']
TYPES=['ร้านค้า / อาหาร / บริการ','งานบุญ / กฐิน / วัด','ราชการ / โรงเรียน / โครงการ','งานศพ / อาลัย','เกษียณ / แสดงความยินดี','งานวิชาการ / ประชาสัมพันธ์','ป้ายชื่อหน่วยงาน','อื่น ๆ']
STYLES=['เรียบหรู มืออาชีพ','สุภาพ เป็นทางการ','โมเดิร์น ทันสมัย','ลายไทยประยุกต์','มินิมอล สะอาดตา','สีสันสดใส โดดเด่น','ตัวหนังสือสามมิติ','ตามภาพตัวอย่าง']
COLORS=['น้ำเงิน–ทอง','แดง–ทอง','เขียว–ขาว','ชมพู–ขาว','ม่วง–ทอง','ดำ–ทอง','ขาว–น้ำเงิน','ตามภาพตัวอย่าง','กำหนดเอง']
with st.container(border=True):
    c1,c2=st.columns(2)
    with c1: work=st.selectbox('1. ประเภทงาน',WORK)
    with c2: kind=st.selectbox('2. ประเภทป้าย',TYPES)

with st.container(border=True):
    st.subheader('3. ทิศทางและขนาดป้าย')
    direction=st.radio('ทิศทาง', ['แนวนอน','แนวตั้ง','สี่เหลี่ยมจัตุรัส','ตามสัดส่วนต้นฉบับ'],horizontal=True)
    presets={'กำหนดเอง':None,'200 × 100':(200,100),'300 × 150':(300,150),'400 × 200':(400,200),'120 × 240':(120,240)}
    preset=st.selectbox('ขนาดสำเร็จรูป (ซม.)',list(presets))
    if preset!='กำหนดเอง':
        a,b=presets[preset]
        if direction=='แนวตั้ง' and a>b:a,b=b,a
        if direction=='แนวนอน' and a<b:a,b=b,a
        if direction=='สี่เหลี่ยมจัตุรัส':a=b=max(a,b)
        if st.session_state.get('preset_last') != (preset,direction):
            st.session_state['w']=float(a);st.session_state['h']=float(b)
            st.session_state['preset_last']=(preset,direction)
    c1,c2=st.columns(2)
    with c1: w=st.number_input('กว้าง (ซม.)',min_value=1.0,value=300.0,step=10.0,key='w')
    with c2: h=st.number_input('สูง (ซม.)',min_value=1.0,value=150.0,step=10.0,key='h')
    actual='แนวนอน' if w>h else 'แนวตั้ง' if h>w else 'สี่เหลี่ยมจัตุรัส'
    if direction in ('แนวนอน','แนวตั้ง','สี่เหลี่ยมจัตุรัส') and direction!=actual:
        st.warning(f'ขนาดที่กรอกเป็น{actual} แต่เลือก {direction} กรุณาปรับขนาดให้ตรงกัน')

with st.container(border=True):
    c1,c2=st.columns(2)
    with c1: style=st.selectbox('4. สไตล์',STYLES)
    with c2: color=st.selectbox('5. โทนสี',COLORS)
    custom_color=st.text_input('ระบุโทนสีเพิ่มเติม (ถ้ามี)') if color=='กำหนดเอง' else ''
    textless=st.checkbox('ไม่ใส่ข้อความ จะเพิ่มเอง')
    wording=st.text_area('6. ข้อความบนป้าย',height=125,disabled=textless,placeholder='พิมพ์ข้อความ ชื่อร้าน วันเวลา สถานที่ และรายละเอียดทั้งหมด')

st.subheader('7. อัปโหลดรูปภาพแยก 3 ช่อง')
st.caption('ไฟล์จะใช้งานในเว็บบนเครื่องของคุณเท่านั้นในรุ่นฟรีนี้ และยังไม่ได้ส่งรูปเข้า ChatGPT อัตโนมัติ')
ca,cb,cc=st.columns(3)
def upload(col,title,key):
    with col:
        with st.container(border=True):
            st.markdown('**'+title+'**')
            obj=st.file_uploader('เลือกรูป',type=['png','jpg','jpeg','webp'],key=key)
            if obj:
                st.image(obj,caption=obj.name,use_container_width=True)
            return obj
primary=upload(ca,'รูปภาพหลัก','primary')
logo=upload(cb,'โลโก้','logo')
reference=upload(cc,'ภาพตัวอย่างแนวทาง','reference')
position=st.selectbox('ตำแหน่งรูปภาพ', ['ให้ AI จัดวางเอง','พื้นหลังเต็มป้าย','ด้านซ้าย','ด้านขวา','ตรงกลาง','ด้านบน'])
logo_position=st.selectbox('ตำแหน่งโลโก้',['ให้ AI จัดวางเอง','ซ้ายบน','ขวาบน','กลางบน','ด้านล่าง'])

with st.container(border=True):
    st.subheader('8. ตัวเลือกเพิ่มเติม')
    opts=st.multiselect('เลือกได้หลายข้อ',['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','เน้นรูปภาพ','คงโครงสร้างเดิม','ตกแต่งเพิ่มเติมอัตโนมัติ','ไม่ใส่ตาไก่','เพิ่มพื้นที่ว่างสำหรับข้อความ','คงใบหน้าบุคคลตามต้นฉบับ','ลบโลโก้เดิม'],default=['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','ตกแต่งเพิ่มเติมอัตโนมัติ'])
    extra=st.text_area('รายละเอียดเพิ่มเติม (ถ้ามี)',placeholder='เช่น ใช้รูปด้านหลังแบบจาง ๆ ใส่ลายตกแต่งเล็กน้อย')

attached=', '.join([label for label,f in [('รูปภาพหลัก',primary),('โลโก้',logo),('ภาพตัวอย่างแนวทาง',reference)] if f]) or 'ไม่มี'
lines=[f'เริ่มออกแบบป้ายตามรายละเอียดนี้',f'ประเภทงาน: {work}',f'ประเภทป้าย: {kind}',f'ขนาด: {w:g} × {h:g} ซม. ({actual})',f'ทิศทางที่เลือก: {direction}',f'สไตล์: {style}',f'โทนสี: {custom_color if color=="กำหนดเอง" else color}',f'ข้อความบนป้าย: {"ไม่มีข้อความ จะเพิ่มเอง" if textless else (wording or "ยังไม่ได้ระบุ")}',f'ไฟล์แนบที่เตรียมไว้: {attached}',f'การจัดรูปภาพ: {position}',f'ตำแหน่งโลโก้: {logo_position}',f'ตัวเลือกเพิ่มเติม: {", ".join(opts) if opts else "ไม่มี"}',f'รายละเอียดเพิ่มเติม: {extra or "ไม่มี"}', 'คำสั่งออกแบบ: ใช้ตัวหนังสือไทยตัวใหญ่ เด่น อ่านง่าย สีตัดพื้น สระและวรรณยุกต์ไม่ทับกัน จัดองค์ประกอบสมดุล เหมาะกับงานพิมพ์ขนาดใหญ่ ไม่ยืดหรือบีบภาพผิดสัดส่วน', 'ถ้ามีรูปภาพหลัก โลโก้ หรือภาพตัวอย่างแนวทาง ให้ใช้ไฟล์ที่ฉันอัปโหลดในแชทตามบทบาทของแต่ละไฟล์ รักษารายละเอียดเดิมเท่าที่ทำได้', 'หากผู้ใช้ระบุว่ามีไฟล์แต่ยังไม่ได้แนบใน ChatGPT ให้ขอรูปก่อนสร้าง ไม่อ้างว่าไฟล์มีความละเอียด 16K จริงโดยไม่ตรวจสอบ']
prompt='\n'.join(lines)
st.subheader('9. คำสั่งพร้อมใช้')
st.code(prompt,language=None)
st.download_button('⬇️ ดาวน์โหลดคำสั่ง .txt',data=prompt.encode('utf-8-sig'),file_name='thanasilp_prompt.txt',mime='text/plain',use_container_width=True)
st.link_button('🚀 ส่งคำสั่งไป ChatGPT (เปิดพร้อมข้อความ)', 'https://chatgpt.com/?q=' + quote(prompt, safe=''), use_container_width=True)
st.caption('เมื่อ ChatGPT เปิดขึ้นมา ให้ตรวจข้อความแล้วกดส่งอีกครั้ง หากไม่มีข้อความปรากฏ ให้คัดลอกคำสั่งจากด้านบนไปวางเอง')
st.info('วิธีใช้ฟรี: กดปุ่มส่งคำสั่งไป ChatGPT → ตรวจคำสั่งแล้วกดส่ง หากมีรูปภาพหลัก/โลโก้/ตัวอย่าง ให้กด + แนบไฟล์ใน ChatGPT เอง ระบบยังไม่สามารถย้ายรูปจากเว็บไปได้อัตโนมัติ')
st.caption('เวอร์ชันนี้ยังไม่เชื่อม API และไม่สามารถส่งไฟล์เข้า ChatGPT ให้เองโดยอัตโนมัติ การทำเช่นนั้นต้องพัฒนาการเชื่อมต่อเพิ่ม')
