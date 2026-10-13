import html
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ธนศิลป์ AI Design", page_icon="🟠", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1150px;padding-top:1.3rem;padding-bottom:2.5rem}
.t-header{
  position:relative;overflow:hidden;isolation:isolate;
  padding:30px 36px;border-radius:25px;margin:0 0 24px;
  background:linear-gradient(118deg,#0c244e 0%,#154984 45%,#2768a4 72%,#ef7526 130%);
  box-shadow:0 14px 32px rgba(17,51,95,.23);
  border:1px solid rgba(255,255,255,.18);
}
.t-header:before{
  content:"";position:absolute;right:-70px;top:-110px;
  width:360px;height:360px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,178,74,.49),rgba(255,178,74,0) 70%);
  z-index:-1;
}
.t-header:after{
  content:"";position:absolute;left:28%;bottom:-135px;
  width:430px;height:250px;border-radius:50%;transform:rotate(-17deg);
  background:radial-gradient(ellipse,rgba(141,209,255,.22),transparent 72%);
  z-index:-1;
}
.t-title{font-size:clamp(32px,4.1vw,55px);font-weight:900;line-height:1.17;margin:0 0 10px;color:white;letter-spacing:-.6px;text-shadow:0 3px 13px rgba(5,21,46,.27)}
.t-title .brand{color:#fff}
.t-title .ai{color:#ffce69;text-shadow:0 2px 16px rgba(250,147,30,.4)}
.t-sub{font-size:clamp(13px,1.35vw,17px);font-weight:550;color:#f5f8ff;line-height:1.6;margin-top:6px;max-width:710px}
.t-accent{color:#ffdf89;font-weight:800}
.t-tags{display:flex;gap:9px;flex-wrap:wrap;margin-top:17px}
.t-tag{padding:7px 13px;border-radius:999px;font-size:12px;font-weight:800;color:#fff;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.26)}
.t-tag.orange{background:linear-gradient(120deg,#f66e20,#ffa43b);border-color:transparent}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:17px}
div.stLinkButton a{border-radius:12px;font-weight:750}
h2,h3{color:#173a68}
@media(max-width:700px){
.t-header{padding:23px 19px;border-radius:19px}
.t-title{font-size:clamp(27px,7vw,39px)}
.t-tags{gap:6px}.t-tag{font-size:11px;padding:6px 9px}
}
</style>
""",unsafe_allow_html=True)
st.markdown("""
<section class="t-header">
  <div class="t-title"><span class="brand">ธนศิลป์</span> <span class="ai">AI Design</span></div>
  <div class="t-sub">เครื่องมือสร้างคำสั่งออกแบบป้าย <span class="t-accent">สวย คมชัด อ่านง่าย</span><br>
  พร้อมนำไปสร้างภาพใน ChatGPT และ Gemini</div>
  <div class="t-tags">
    <span class="t-tag orange">✦ ใช้งานฟรี</span>
    <span class="t-tag">ไม่ต้องใช้ API Key</span>
    <span class="t-tag">ป้ายร้านค้า · งานบุญ · ราชการ · อื่น ๆ</span>
  </div>
</section>
""",unsafe_allow_html=True)

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
    'ถ้าเลือกไม่ใส่ข้อความ ห้ามแทรกตัวอักษรบนภาพ',
    'กรณีแนบรูปถ่ายเอกสาร ป้ายเก่า หรือภาพที่มีข้อความ: ให้อ่านและถอดข้อความจากภาพต้นฉบับอย่างละเอียด แล้วพิมพ์ลงป้ายตามตัวอักษรที่มองเห็นจริงทุกตัว ห้ามเปลี่ยนคำหรือแต่งประโยคใหม่',
    'ตรวจทานข้อความที่ถอดจากรูปทีละบรรทัด โดยเฉพาะชื่อ-นามสกุล ชื่อหน่วยงาน สถานที่ วันเดือนปี พ.ศ. เลขไทย ตัวเลข เบอร์โทรศัพท์ สระ วรรณยุกต์ และเครื่องหมายวรรคตอน ให้ตรงกับรูปต้นฉบับ',
    'หากส่วนใดในภาพเบลอ ถูกบัง อ่านไม่ชัด หรือไม่แน่ใจ ห้ามเดาและห้ามสร้างข้อความที่ไม่เห็นจริง ให้ถามผู้ใช้เพื่อยืนยันข้อความส่วนนั้นก่อนออกแบบ',
    'ถ้าผู้ใช้พิมพ์ข้อความแก้ไขเพิ่มเติมไว้ ให้ใช้ข้อความแก้ไขที่ผู้ใช้ระบุเป็นหลักเฉพาะจุดนั้น ส่วนข้อความอื่นให้ยึดภาพที่แนบ',
    'เมื่อทำภาพป้ายเสร็จให้ตรวจเทียบข้อความทั้งหมดกับภาพอ้างอิงอีกครั้ง หากไม่สามารถรับประกันความตรงของตัวหนังสือในภาพที่สร้าง ให้ทำพื้นหลังและเว้นช่องข้อความสำหรับใส่ภายหลังแทนการปล่อยคำผิด'
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


st.divider()
st.subheader('8. 🛍️ สั่งออกแบบ / สั่งพิมพ์ป้ายกับร้านธนศิลป์ ดีไซน์')
st.markdown('กรอกข้อมูลด้านล่างเพื่อทำ **ใบสรุปคำสั่งซื้อ** แล้วคัดลอกส่งให้ร้านทาง LINE ได้โดยตรง')
st.caption('เว็บไซต์นี้ไม่เก็บคำสั่งซื้อในฐานข้อมูลและไม่ส่งข้อมูลไปหาร้านโดยอัตโนมัติ ลูกค้าต้องส่งใบสั่งงานใน LINE ด้วยตนเอง')

with st.container(border=True):
    order_type = st.selectbox('ประเภทบริการ', ['ออกแบบป้าย', 'ออกแบบและพิมพ์ป้าย', 'พิมพ์ป้ายจากไฟล์ที่มี', 'แก้ไขไฟล์เดิม', 'สอบถามราคาก่อนสั่ง'])
    oc1,oc2=st.columns(2)
    with oc1:
        customer_name=st.text_input('ชื่อลูกค้า / ชื่อหน่วยงาน', key='order_customer', placeholder='ชื่อผู้ติดต่อ')
    with oc2:
        customer_phone=st.text_input('เบอร์โทรติดต่อ', key='order_phone', placeholder='เช่น 08XXXXXXXX')
    order_note=st.text_area('รายละเอียดงานและข้อกำหนดเพิ่มเติม', height=105, key='order_note',
                             placeholder='เช่น จำนวนป้าย วัสดุ สถานที่รับงาน กำหนดส่ง หรือรายละเอียดที่ต้องการให้ร้านประเมิน')
    order_deadline=st.text_input('วันที่ต้องการรับงาน (ถ้ามี)', placeholder='เช่น 25 ต.ค. 2569',key='order_deadline')
    use_current_design=st.checkbox('นำรายละเอียดป้ายจากแบบฟอร์มด้านบนมาใช้ในใบสั่งงาน',value=True)

order_lines=[
    'ใบสั่งงาน / ขอใบเสนอราคา - ร้านธนศิลป์ ดีไซน์',
    f'บริการ: {order_type}',
    f'ผู้ติดต่อ: {customer_name.strip() or "ยังไม่ระบุ"}',
    f'เบอร์โทร: {customer_phone.strip() or "ยังไม่ระบุ"}',
    f'วันที่ต้องการรับงาน: {order_deadline.strip() or "ยังไม่ระบุ"}',
]
if use_current_design:
    order_lines.extend([
        f'ประเภทงาน: {work}', f'ประเภทป้าย: {kind}',
        f'ขนาดป้าย: {w:g} × {h:g} ซม.',
        f'รูปแบบ: {actual}', f'สไตล์: {style}',
        f'ข้อความบนป้าย: {"ไม่มีข้อความ" if textless else (wording.strip() or "ยังไม่ระบุ")}',
    ])
order_lines.extend([
    f'รายละเอียดเพิ่มเติม: {order_note.strip() or "ไม่มี"}',
    'หมายเหตุ: โปรดแจ้งราคาหรือยืนยันคิวก่อนเริ่มดำเนินงาน',
])
order_summary='\n'.join(order_lines)
st.markdown('**ใบสรุปสำหรับส่งร้าน**')
st.code(order_summary, language=None,wrap_lines=True)
st.download_button('⬇️ ดาวน์โหลดใบสั่งงาน .txt',order_summary.encode('utf-8-sig'),
                   file_name='thanasilp_order.txt',mime='text/plain',use_container_width=True)

# Set an official LINE contact URL via Streamlit Secrets; never store customer data in query strings.
try:
    line_url=st.secrets.get('LINE_CONTACT_URL','')
except Exception:
    line_url=''
line_url=str(line_url).strip()
line_valid=line_url.startswith(('https://line.me/','https://lin.ee/','https://page.line.me/','https://liff.line.me/'))
if line_valid:
    st.link_button('💬 เปิด LINE ติดต่อร้านธนศิลป์ ดีไซน์',line_url,use_container_width=True)
    st.info('วิธีส่งออเดอร์: กดคัดลอกข้อความจากกรอบใบสั่งงานด้านบน → กดเปิด LINE → วางข้อความในแชทร้าน → แนบรูปตัวอย่าง/ไฟล์ที่ต้องการ → กดส่ง')
else:
    st.warning('ยังไม่ได้ตั้งค่าลิงก์ LINE ของร้าน จึงยังไม่แสดงปุ่มติดต่อ เพื่อป้องกันการส่งออเดอร์ผิดบัญชี')
    st.caption('เจ้าของร้าน: ไปที่ Streamlit Community Cloud → Manage app → Settings → Secrets แล้วเพิ่มบรรทัด LINE_CONTACT_URL = "https://lin.ee/รหัสจริงของร้าน"')
