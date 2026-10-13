import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from io import BytesIO
import json
from urllib.parse import quote

st.set_page_config(page_title='ธนศิลป์ AI Design',page_icon='🎨',layout='wide')
st.markdown('''<style>.block-container{max-width:1150px;padding-top:1.5rem}h1{color:#173a68}div.stButton>button[kind="primary"]{background:#16447c;border:0} </style>''',unsafe_allow_html=True)
st.title('🎨 ธนศิลป์ AI Design')
st.caption('ระบบสร้างคำสั่งออกแบบป้ายสำหรับ ChatGPT • ไม่ต้องเลือกสีหรืออัปโหลดรูปในเว็บ • ไม่ต้องใช้ API Key')

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
    style=st.selectbox('4. สไตล์',STYLES)
    textless=st.checkbox('ไม่ใส่ข้อความ จะเพิ่มเอง')
    wording=st.text_area('5. ข้อความบนป้าย',height=125,disabled=textless,placeholder='พิมพ์ข้อความ ชื่อร้าน วันเวลา สถานที่ และรายละเอียดทั้งหมด')
    st.caption('ไม่ต้องอัปโหลดรูปในเว็บ เมื่อเปิด ChatGPT หรือ Gemini ค่อยแนบรูปภาพหลักและโลโก้ได้เลย')

with st.container(border=True):
    st.subheader('6. ตัวเลือกเพิ่มเติม')
    opts=st.multiselect('เลือกได้หลายข้อ',['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','เน้นรูปภาพ','คงโครงสร้างเดิม','ตกแต่งเพิ่มเติมอัตโนมัติ','ไม่ใส่ตาไก่','เพิ่มพื้นที่ว่างสำหรับข้อความ','คงใบหน้าบุคคลตามต้นฉบับ','ลบโลโก้เดิม'],default=['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','ตกแต่งเพิ่มเติมอัตโนมัติ'])
    extra=st.text_area('รายละเอียดเพิ่มเติม (ถ้ามี)',placeholder='เช่น ใช้รูปด้านหลังแบบจาง ๆ ใส่ลายตกแต่งเล็กน้อย')

lines=[
    'เริ่มออกแบบป้ายตามรายละเอียดนี้',
    f'ประเภทงาน: {work}',
    f'ประเภทป้าย: {kind}',
    f'ขนาด: {w:g} × {h:g} ซม. ({actual})',
    f'ทิศทางที่เลือก: {direction}',
    f'สไตล์: {style}',
    f'ข้อความบนป้าย: {"ไม่มีข้อความ จะเพิ่มเอง" if textless else (wording or "ยังไม่ได้ระบุ")}',
    f'ตัวเลือกเพิ่มเติม: {", ".join(opts) if opts else "ไม่มี"}',
    f'รายละเอียดเพิ่มเติม: {extra or "ไม่มี"}',
    'เลือกโทนสีและจัดแต่งองค์ประกอบให้อัตโนมัติตามประเภทงาน ไม่ต้องถามให้ผู้ใช้เลือกสี',
    'ให้นำรูปภาพหลักและโลโก้ที่ผู้ใช้แนบในแชท AI (ChatGPT หรือ Gemini) มาใช้ประกอบการออกแบบ จัดตำแหน่งให้สวยงาม หากผู้ใช้ไม่แนบก็ออกแบบโดยไม่ใช้รูปเหล่านั้น',
    'เน้นตัวหนังสือภาษาไทยใหญ่ อ่านง่าย สีตัดพื้น สระและวรรณยุกต์ไม่ทับกัน การจัดวางสมดุล เหมาะกับงานพิมพ์ขนาดใหญ่',
    'รักษาสัดส่วนของป้ายตามขนาดจริง ไม่ยืดหรือบีบรูปภาพและโลโก้',
    'ข้อกำหนดสำคัญที่สุด: ข้อความทุกตัวอักษรต้องตรงตามข้อความบนป้ายที่ผู้ใช้ระบุ 100% ห้ามแก้คำ สะกดใหม่ ย่อ ตัด เติม หรือเรียบเรียงข้อความเอง',
    'ต้องคงลำดับบรรทัด เว้นวรรค ชื่อบุคคล ชื่อสถานที่ เบอร์โทรศัพท์ ตัวเลข วันที่ เดือน ปี พ.ศ. รวมถึงเลขไทยและเครื่องหมายวรรคตอนตามต้นฉบับ',
    'วรรณยุกต์ สระบน สระล่าง ต้องไม่ทับกัน ไม่หาย ไม่ตกหล่น ตรวจความถูกต้องของข้อความก่อนส่งภาพ',
    'หาก AI ไม่สามารถแสดงข้อความไทยให้ตรงทุกตัวอักษรได้ ให้ทำพื้นหลังและองค์ประกอบพร้อมเว้นพื้นที่ข้อความ ห้ามเดาข้อความหรือสร้างข้อความผิด และแจ้งให้ผู้ใช้ใส่ข้อความภายหลัง',
    'กรณีผู้ใช้เลือกไม่ใส่ข้อความ จะเพิ่มเอง ห้ามสร้างข้อความหรืออักษรตกแต่งใด ๆ บนป้าย'
]
prompt='\\n'.join(lines)
st.subheader('7. คำสั่งพร้อมใช้')
st.code(prompt,language=None)
st.download_button('⬇️ ดาวน์โหลดคำสั่ง .txt',data=prompt.encode('utf-8-sig'),file_name='thanasilp_prompt.txt',mime='text/plain',use_container_width=True)
c_chatgpt, c_gemini = st.columns(2)
with c_chatgpt:
    st.link_button('🚀 ส่งคำสั่งไป ChatGPT', 'https://chatgpt.com/?q=' + quote(prompt, safe=''), use_container_width=True)
with c_gemini:
    st.link_button('✨ เปิด Google Gemini', 'https://gemini.google.com/app', use_container_width=True)
st.caption('Gemini: คัดลอกคำสั่งจากกล่องด้านบน แล้วนำไปวางใน Gemini (ลิงก์ทั่วไปไม่สามารถแนบคำสั่งยาวและรูปเข้าแชทให้โดยตรงได้)')
st.caption('เมื่อ ChatGPT เปิดขึ้นมา ให้ตรวจข้อความแล้วกดส่งอีกครั้ง หากไม่มีข้อความปรากฏ ให้คัดลอกคำสั่งจากด้านบนไปวางเอง')
st.info('ใช้ฟรี: เลือกเปิด ChatGPT หรือ Gemini; สำหรับ Gemini ให้คัดลอกคำสั่งไปวางเอง จากนั้นแนบรูปภาพและโลโก้ในแชท AI ก่อนกดส่ง')
st.caption('เวอร์ชันนี้ยังไม่เชื่อม API และไม่สามารถส่งไฟล์เข้า ChatGPT ให้เองโดยอัตโนมัติ การทำเช่นนั้นต้องพัฒนาการเชื่อมต่อเพิ่ม')


