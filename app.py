import html
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ธนศิลป์ AI Design", page_icon="🟠", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1150px;padding-top:1.4rem}
.t-header{display:flex;align-items:center;gap:20px;padding:20px 24px;border-radius:22px;background:linear-gradient(112deg,#101d31,#243d70 75%,#844c47);box-shadow:0 12px 30px #101d3130;margin-bottom:22px}

.t-title{font-size:clamp(27px,4vw,48px);font-weight:900;color:#fff;line-height:1.2;margin:0}
.t-title span{color:#ffad56}
.t-sub{color:#eef2fa;font-size:14px;line-height:1.5;margin-top:6px}
.t-tag{display:inline-block;padding:6px 12px;background:#f36c21;border-radius:16px;color:#fff;font-size:12px;font-weight:700;margin-top:10px}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px}
div.stLinkButton a{border-radius:10px;font-weight:700}
@media(max-width:700px){.t-header{padding:12px;gap:12px}.t-sub{font-size:12px}}
</style>
""",unsafe_allow_html=True)
st.markdown("""<div class="t-header">

<div><div class="t-title">ธนศิลป์ <span>AI Design</span></div>
<div class="t-sub">ระบบสร้างคำสั่งออกแบบป้ายสำหรับ ChatGPT และ Gemini</div>
<div class="t-tag">ใช้งานฟรี · ไม่ต้องใช้ API Key</div></div></div>""",unsafe_allow_html=True)

WORK = ['ออกแบบป้ายใหม่','แก้ไขภาพเดิม','ปรับคุณภาพ Ultra-Sharp','แปลงเป็นเวกเตอร์','ลบข้อความคงพื้นหลัง','เปลี่ยนสีและองค์ประกอบ','ปรับขนาดภาพ','สร้างพื้นหลังเปล่า','Depth Map / CNC']
TYPES = ['ร้านค้า / อาหาร / บริการ','งานบุญ / กฐิน / วัด','ราชการ / โรงเรียน / โครงการ','งานศพ / อาลัย','เกษียณ / แสดงความยินดี','งานวิชาการ / ประชาสัมพันธ์','ป้ายชื่อหน่วยงาน','อื่น ๆ']
STYLES = ['เรียบหรู มืออาชีพ','สุภาพ เป็นทางการ','โมเดิร์น ทันสมัย','ลายไทยประยุกต์','มินิมอล สะอาดตา','สีสันสดใส โดดเด่น','ตัวหนังสือสามมิติ','ตามภาพตัวอย่าง']

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        work = st.selectbox('1. ประเภทงาน',WORK)
    with col2:
        kind = st.selectbox('2. ประเภทป้าย',TYPES)

with st.container(border=True):
    st.subheader('3. ขนาดและทิศทางป้าย')
    direction = st.radio('ทิศทาง',['แนวนอน','แนวตั้ง','สี่เหลี่ยมจัตุรัส','ตามสัดส่วนต้นฉบับ'],horizontal=True)
    preset = st.selectbox('ขนาดสำเร็จรูป (ซม.)',['กำหนดเอง','200 × 100','300 × 150','400 × 200','120 × 240'])
    dims={'200 × 100':(200,100),'300 × 150':(300,150),'400 × 200':(400,200),'120 × 240':(120,240)}
    if preset != 'กำหนดเอง':
        a,b=dims[preset]
        if direction=='แนวตั้ง' and a>b: a,b=b,a
        if direction=='แนวนอน' and a<b: a,b=b,a
        if direction=='สี่เหลี่ยมจัตุรัส': a=b=max(a,b)
        if st.session_state.get('_last_preset')!=(preset,direction):
            st.session_state['width_cm']=float(a)
            st.session_state['height_cm']=float(b)
            st.session_state['_last_preset']=(preset,direction)
    cw,ch=st.columns(2)
    with cw: w=st.number_input('กว้าง (ซม.)', min_value=1.0, value=300.0, step=10.0, key='width_cm')
    with ch: h=st.number_input('สูง (ซม.)', min_value=1.0, value=150.0, step=10.0, key='height_cm')
    actual='แนวนอน' if w>h else 'แนวตั้ง' if h>w else 'สี่เหลี่ยมจัตุรัส'
    if direction in ['แนวนอน','แนวตั้ง','สี่เหลี่ยมจัตุรัส'] and direction!=actual:
        st.warning(f'ขนาดที่กรอกเป็น{actual} แต่เลือก {direction} โปรดแก้ให้ตรงกัน')

with st.container(border=True):
    style=st.selectbox('4. สไตล์',STYLES)
    textless=st.checkbox('ไม่ใส่ข้อความ จะเพิ่มเอง')
    wording=st.text_area('5. ข้อความบนป้าย',height=145,disabled=textless,placeholder='พิมพ์ข้อความทั้งหมดตรงตามที่ต้องการให้ปรากฏบนป้าย')
    st.caption('ไม่ต้องอัปโหลดรูปหรือเลือกโทนสีในเว็บ แนบรูปภาพหลักและโลโก้ใน ChatGPT/Gemini ได้โดยตรง')

with st.container(border=True):
    st.subheader('6. รายละเอียดเพิ่มเติม')
    opts=st.multiselect('ตัวเลือกพิเศษ',['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','เน้นรูปภาพ','คงโครงสร้างเดิม','ตกแต่งเพิ่มเติมอัตโนมัติ','ไม่ใส่ตาไก่','เพิ่มพื้นที่ว่างสำหรับข้อความ','คงใบหน้าบุคคลตามต้นฉบับ','ลบโลโก้เดิม'],default=['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','ตกแต่งเพิ่มเติมอัตโนมัติ'])
    extra=st.text_area('รายละเอียดเพิ่มเติม (ถ้ามี)',height=85)

prompt='\n'.join([
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
    'ให้นำรูปภาพหลักและโลโก้ที่ผู้ใช้แนบในแชทมาใช้ประกอบการออกแบบ จัดตำแหน่งให้สวยงาม หากไม่ได้แนบให้จัดแบบโดยไม่ใช้รูปเหล่านั้น',
    'เน้นตัวหนังสือภาษาไทยขนาดใหญ่ อ่านง่าย สีตัดพื้น สระและวรรณยุกต์ไม่ทับกัน',
    'รักษาสัดส่วนป้ายตามขนาดจริง ไม่ยืดหรือบีบรูปภาพหรือโลโก้',
    'สำคัญที่สุด: ข้อความบนป้ายทุกตัวอักษรต้องตรงตามที่ระบุ ห้ามแก้คำ เพิ่มคำ ลบคำ สะกดใหม่ หรือเรียบเรียงใหม่',
    'คงลำดับบรรทัด ชื่อบุคคล สถานที่ เบอร์โทร เลขไทย ตัวเลข วันที่ เดือน ปี พ.ศ. และเครื่องหมายวรรคตอน',
    'ตรวจสระและวรรณยุกต์ หากแสดงภาษาไทยไม่ได้แม่นยำให้เว้นพื้นที่ใส่ข้อความเอง ห้ามสร้างข้อความผิด',
    'ถ้าเลือกไม่ใส่ข้อความ ห้ามแทรกตัวอักษรบนภาพ'
])

st.subheader('7. ส่งคำสั่งไปสร้างภาพ')
st.code(prompt,language=None)
st.download_button('⬇️ ดาวน์โหลดคำสั่ง .txt',data=prompt.encode('utf-8-sig'),file_name='thanasilp_prompt.txt',mime='text/plain',use_container_width=True)
col_gpt,col_gemini=st.columns(2)
with col_gpt:
    st.link_button('🚀 ส่งคำสั่งไป ChatGPT','https://chatgpt.com/?q='+quote(prompt,safe=''),use_container_width=True)
with col_gemini:
    safe_prompt=html.escape(prompt,quote=True)
    components.html(f'''
    <button id="gemini" style="width:100%;padding:11px;border-radius:9px;border:1px solid #e87b2d;background:#f47721;color:white;font-weight:bold;cursor:pointer">✨ คัดลอกคำสั่ง + เปิด Gemini</button>
    <div id="status" role="status" style="font:12px Arial;margin-top:7px;color:#555"></div>
    <textarea id="source" style="position:absolute;left:-9999px">{safe_prompt}</textarea>
    <script>
    document.getElementById('gemini').onclick=async()=>{{
       const tab=window.open('https://gemini.google.com/app','_blank');
       let copied=false;
       const text=document.getElementById('source').value;
       try{{await navigator.clipboard.writeText(text);copied=true}}catch(e){{}}
       if(!copied){{try{{const el=document.getElementById('source');el.style.left='0px';el.select();copied=document.execCommand('copy');el.style.left='-9999px'}}catch(e){{}}}}
       document.getElementById('status').innerText=copied?'✅ คัดลอกแล้ว เปิด Gemini แล้วกด Ctrl+V เพื่อวางข้อความ':'คัดลอกไม่สำเร็จ กรุณาคัดลอกจากช่องคำสั่งด้านบน';
       if(!tab)document.getElementById('status').innerText+=' | หากไม่เปิดแท็บ ให้ใช้ลิงก์สำรองด้านล่าง';
    }};
    </script>
    ''',height=80)
    st.link_button('เปิด Gemini (ลิงก์สำรอง)','https://gemini.google.com/app',use_container_width=True)

st.info('วิธีใช้: **ChatGPT** เปิดพร้อมคำสั่ง (หากระบบรองรับ) แล้วตรวจและกดส่ง • **Gemini** กดคัดลอก+เปิด → Ctrl+V → แนบรูป/โลโก้ → กดส่ง')
st.caption('เว็บไซต์นี้สร้างคำสั่งเท่านั้น ไม่ส่งไฟล์เข้าห้องแชทอัตโนมัติ และไม่ใช้ OpenAI API')
