import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from io import BytesIO
import json
import html
from urllib.parse import quote

st.set_page_config(page_title='ธนศิลป์ AI Design',page_icon='🎨',layout='wide')
st.markdown("""<style>
.block-container{max-width:1150px;padding-top:1.5rem}
.t-header{display:flex;align-items:center;gap:20px;padding:19px 24px;border-radius:22px;background:linear-gradient(115deg,#11243d,#244579 65%,#f36c21 155%);box-shadow:0 10px 28px #091d3830;margin-bottom:20px}
.t-logo{height:110px;width:110px;border-radius:17px;object-fit:cover;border:3px solid white;box-shadow:0 4px 14px #0005}
.t-name{font-weight:900;font-size:clamp(27px,4vw,48px);color:white;line-height:1.12;margin:0}
.t-name span{color:#ffb35c}
.t-sub{color:#eef2fc;font-size:14px;margin-top:9px;line-height:1.5}
.t-pill{display:inline-block;margin-top:9px;color:#fff;background:#f36c21;border-radius:30px;padding:5px 12px;font-size:12px;font-weight:700}
div.stButton>button[kind="primary"]{background:#f36c21;border:0}
div.stLinkButton a{border-radius:12px;font-weight:700}
@media(max-width:600px){.t-header{padding:14px;gap:12px}.t-logo{height:76px;width:76px}.t-sub{font-size:12px}}
</style>""",unsafe_allow_html=True)
st.markdown("""<section class="t-header">
<img class="t-logo" src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA8LDA0MCg8NDA0REA8SFyYZFxUVFy8iJBwmODE7OjcxNjU9RVhLPUFUQjU2TWlOVFteY2RjPEpsdGxgc1hhY1//2wBDARARERcUFy0ZGS1fPzY/X19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fX1//wAARCABWAFYDASIAAhEBAxEB/8QAGwAAAgMBAQEAAAAAAAAAAAAAAAMCBAUBBgf/xAA3EAACAQMDAQUFBgUFAAAAAAABAgMABBESITEFE0FRYXEGIpGxwTJDUlNygRQjQmLiBxaCodH/xAAZAQACAwEAAAAAAAAAAAAAAAACAwABBAX/xAApEQADAAEDAwMCBwAAAAAAAAAAAQIRAyExBCKxEhNBI+FRYXGBkcHw/9oADAMBAAIRAxEAPwDxwpqUsUxRTECOUZxTVFQTbFOiie4fs48DAyzHhR4mj4KOxRPPJoTAAGWY8KPE1aFnq2hMxfuWWLRr/Tud/I02SSOxhWOJcud1VuSfxN9B3fE1VtricOwkdpix95GPI/t86R7l1vC28mj2ona3h+P1BMGp6atyRC6AmgOqRuD+Z/l8/XmsuCNqfFq1lCbhw8MU44xUGByBjanstRIosACCN8UV0hWY+IoqiGWKYppYp9vA9zL2ceAAMs54UeJpYQ62je4k0R4GBlmPCjxNasjLZQdnAmpwNeG2/wCb/Qd3xNczFZRrBFpDn3h2hxj+9/oO74mi0WFz2ssq6M6lDsMufxN9B3Vj1tb1cceToaGh6Xvz4+5Wjs7xz20kZZm3JJGa5LE64EiMjdxIrc7RCuoOpHjmuM8LKVZ0IPcSKXHW2tnOw6+g03xW5kRTvGxJGosffT8fmPOrzIt0omhOqRuD+Z/l8/XmpdQxxuOzcENwAckGlxXJhkYMu2PfQ7avMeBrVz9TTMT2+lqfz+H2Gk5G1LarkqC6UTQnVI3B/M/y+frzQLalJFaYtWsozXDh4ZE0Uos+ngZoqwSjbQSXMnZx4AAyztwo8TWzLLD0y3WOJcyHdVbkn8bfQd3xNZ/SZFJMGf5hlSRV/M05yvrvkeOPSjqUEkd005OuKY5V/pWS+6lD48mrT7Ydrnx+Yg6pXaSVtTsckmr/AEmyiuJnklUMkf8ASe81ng7V6D2XWOTtEmcpGZN2HdtV9Q3On2k6ZKtXNb/I+66hP0pre5tcAq+ChHusuODXsrLrfSru1jnaaGBmG8crBWU/v868l1O3MN70tWKuslyjAjgjNefkPaXEryMXcucltyd6DpZ+nhh9ZSerlH1Yp0zqcbJi2uk79OGx8OK851PpUVvPFZ3eZbC5bRBO28ltJ3DV3qfOvJ2d1L0+8hurZirowyAftDvBr6P7TRiXoF2ce8iiRT4EEEU9rDMqeT5zHJLZ3MsMqlnVykkfc2Nsjz2q5PELpRNA2qRuD+Z5fr+frzS6hL/E9Qu5kBOqV3BHhnmuWkiSW88b3Co8jA5OwQDlvX03oalw1U/uOilcuK+OBeRRXLmdZ7maVBpV3LAeRNFaMmYyOa3LC+W8U210NcrbEH73z/X8/XnCBrtIqVSwxsW4eUaF5ataMCDrgf7D/Q+dbnsm8qW97LFuFB1DGdiAPrWfYXy3im1uhrlbYg/e+f6/n684lcoalUsMKLcPKL17aNaOCp1wP9h/ofOrnQ7S1uHlur6WIQW5XMbvp1Zzvzkgd+KlYXy3qG1u11ytsQfvfT+/5+vK4LHp+qVu3aYIDnUpURebHx8uc0tXU9tLI16c33S8f0alzMs11/ECO3trKCMxn+WEL7545znYA4JH71gXV3JeSB5Aqqv2UQYAqF1dzXbKJZWkVMhWYYLeZ8+KTmnIQMzXM1DVXM1ZRMmil5oqEE1IUUUJZLNFFFWQ7imzXVzOgSe5llVeFdyQKKKhQrO1GaKKhDmaM0UVCwoooqEP/Z" alt="โลโก้ร้านธนศิลป์ ดีไซน์"/>
<div><div class="t-name">ธนศิลป์ <span>AI Design</span></div>
<div class="t-sub">ระบบสร้างคำสั่งออกแบบป้ายสำหรับ ChatGPT และ Gemini</div>
<div class="t-pill">ใช้งานฟรี • ไม่ต้องใช้ API Key</div></div></section>""",unsafe_allow_html=True)

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
    import streamlit.components.v1 as components
    # HTML-escape both text and attributes to avoid injecting untrusted prompt text.
    safe_prompt = html.escape(prompt, quote=True)
    components.html(f"""
    <div style="font-family:Arial,sans-serif">
      <button id="send-gemini" type="button"
        style="width:100%;min-height:40px;background:#fff;color:#202124;border:1px solid #bbb;border-radius:9px;font-weight:650;cursor:pointer">
        ✨ คัดลอกคำสั่ง + เปิด Gemini
      </button>
      <div id="gemini-status" role="status" aria-live="polite" style="font-size:12px;margin-top:5px;color:#575b61"></div>
      <textarea id="gemini-prompt" style="position:fixed;left:-9999px;top:0" aria-hidden="true">{safe_prompt}</textarea>
    </div>
    <script>
    document.getElementById('send-gemini').addEventListener('click', async () => {{
      const value=document.getElementById('gemini-prompt').value;
      const status=document.getElementById('gemini-status');
      // Open while still in the user click handler so popup blockers allow it.
      const tab=window.open('https://gemini.google.com/app','_blank','noopener,noreferrer');
      let copied=false;
      try {{
        if (navigator.clipboard && window.isSecureContext) {{
          await navigator.clipboard.writeText(value);
          copied=true;
        }}
      }} catch (err) {{}}
      if (!copied) {{
        try {{
          const el=document.getElementById('gemini-prompt');
          el.style.position='absolute';el.style.left='0';el.style.top='0';
          el.focus();el.select();
          copied=document.execCommand('copy');
          el.style.position='fixed';el.style.left='-9999px';
        }} catch(err) {{}}
      }}
      if (copied) {{
        status.textContent='✅ คัดลอกแล้ว! ไปที่ Gemini กด Ctrl+V แล้วส่ง';
      }} else {{
        status.textContent='⚠️ คัดลอกอัตโนมัติไม่สำเร็จ กรุณาคัดลอกจากกล่องคำสั่งด้านบน';
      }}
      if (!tab) {{
        status.textContent += ' | หาก Gemini ไม่เปิด ให้คลิกลิงก์สำรองด้านล่าง';
      }}
    }});
    </script>
    """, height=86)
    st.link_button('เปิด Gemini (ลิงก์สำรอง)', 'https://gemini.google.com/app', use_container_width=True)
st.markdown('**วิธีใช้ Gemini:** ① กดปุ่ม **คัดลอกคำสั่ง + เปิด Gemini** ② ไปหน้าต่าง Gemini ③ กด **Ctrl + V** (มือถือ: แตะค้างแล้ววาง) ④ แนบรูปและโลโก้ใน Gemini ถ้ามี ⑤ ตรวจข้อความแล้วกดส่ง')
st.caption('เบราว์เซอร์บางตัวอาจบล็อกการคัดลอกหรือเปิดแท็บใหม่ หากไม่สำเร็จให้คัดลอกข้อความในกรอบคำสั่งด้านบน แล้วใช้ลิงก์สำรอง')
st.caption('เมื่อ ChatGPT เปิดขึ้นมา ให้ตรวจข้อความแล้วกดส่งอีกครั้ง หากไม่มีข้อความปรากฏ ให้คัดลอกคำสั่งจากด้านบนไปวางเอง')
st.info('ใช้ฟรี: เลือกเปิด ChatGPT หรือ Gemini; สำหรับ Gemini ให้คัดลอกคำสั่งไปวางเอง จากนั้นแนบรูปภาพและโลโก้ในแชท AI ก่อนกดส่ง')
st.caption('เวอร์ชันนี้ยังไม่เชื่อม API และไม่สามารถส่งไฟล์เข้า ChatGPT ให้เองโดยอัตโนมัติ การทำเช่นนั้นต้องพัฒนาการเชื่อมต่อเพิ่ม')


