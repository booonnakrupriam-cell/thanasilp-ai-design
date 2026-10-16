import html
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ธนศิลป์ AI Design", page_icon="🟠", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1480px;padding-top:1.05rem;padding-bottom:2.4rem}
.t-header{
 position:relative;isolation:isolate;overflow:hidden;text-align:center;
 background:
 radial-gradient(ellipse at 48% 0%,rgba(0,155,255,.65),transparent 38%),
 radial-gradient(circle at 91% 60%,rgba(0,159,255,.45),transparent 32%),
 linear-gradient(135deg,#00143c 0%,#004cc7 38%,#033fbd 62%,#001038 100%);
 border:2px solid #2379e8;border-radius:22px;padding:23px 30px 22px;margin:0 0 23px;
 box-shadow:inset 0 0 46px #006bff8c,0 14px 28px #001a4c3a;
}
.t-header:before{
 content:"";position:absolute;inset:-25% -12%;pointer-events:none;z-index:-1;
 background:repeating-linear-gradient(135deg,transparent 0,transparent 130px,#00c6ff24 131px,#009dff11 148px,transparent 161px);
 transform:skewY(-5deg);
}
.t-header:after{
 content:"";position:absolute;inset:0;pointer-events:none;z-index:-1;
 background:radial-gradient(circle at 8% 17%,#00bbff44,transparent 21%),radial-gradient(circle at 98% 85%,#00baff55,transparent 25%);
}
.t-title{font-size:clamp(37px,6.3vw,88px);font-weight:1000;line-height:1.21;margin:0 0 14px;letter-spacing:-1.3px;filter:drop-shadow(0 5px 2px #00102e)}
.t-title .brand,.t-title .design{color:#f8fcff;-webkit-text-stroke:1px #91c8ff;text-shadow:1px 3px 0 #1258bc,3px 6px 0 #001e68,0 0 19px #36b6ff}
.t-title .ai{color:#ffcf35;-webkit-text-stroke:1px #fff2a9;text-shadow:1px 3px 0 #e89000,3px 6px 0 #704000,0 0 24px #ffdd40}
.t-title .design{font-style:italic}
.t-sub{font-size:clamp(17px,2.15vw,30px);font-weight:850;color:#fff;line-height:1.42;margin:10px auto 14px;padding:13px 18px;max-width:1120px;border-radius:65px;background:linear-gradient(95deg,#001849de,#031451d9);border:2px solid #00c5ff;box-shadow:0 0 17px #00c8ffb0,inset 0 0 22px #004fce}
.t-accent{color:#ffcf32;font-weight:1000;text-shadow:0 1px 7px #b26b00}
.t-ai-names{color:#14e4ff;font-weight:950;text-shadow:0 0 8px #009ad1}
.t-shop-offer{max-width:1110px;margin:20px auto 14px;padding:13px 20px;border-radius:20px;line-height:1.3;background:linear-gradient(180deg,#fff5ad,#ffcf23 50%,#fba911);border:3px solid #ffe977;box-shadow:inset 0 0 9px #ffffffbb,0 5px 0 #a66400,0 8px 21px #020e2b8c;color:#052c80;font-size:clamp(20px,3vw,42px);font-weight:1000;text-shadow:1px 1px 0 #fff7bd}
.t-service-highlight{color:#05286c;font-weight:1000}
.t-shop-offer strong{color:#d20f14;font-weight:1000;text-shadow:1px 1px #fff}
.t-shop-contact{display:table;max-width:100%;margin:12px auto 14px;padding:9px 20px;color:white;background:#002057;border-radius:50px;border:2px solid #23d5ff;box-shadow:0 0 15px #00ccff99;font-size:clamp(19px,2.3vw,31px);font-weight:850}
.t-shop-contact a{display:inline-block;margin-left:8px;padding:1px 16px;border-radius:28px;background:linear-gradient(#fff59e,#ffc02c);color:#002969!important;text-decoration:none;font-weight:1000;font-size:1.12em;box-shadow:inset 0 0 9px #fff,0 3px 0 #b17100}
.t-shop-buttons{display:flex;justify-content:center;gap:11px;flex-wrap:wrap;margin:14px 0 8px}
.t-contact-call,.t-contact-line{display:inline-block;padding:10px 17px;border-radius:12px;font-weight:800;text-decoration:none!important;color:white!important}
.t-contact-call{background:linear-gradient(120deg,#e96d12,#ff9d26);border:1px solid #ffd58a}
.t-contact-line{background:#07a74e;border:1px solid #74da96}
.t-tags{display:flex;justify-content:center;gap:9px;flex-wrap:wrap;margin-top:12px}
.t-tag{padding:6px 13px;border-radius:999px;font-size:12px;font-weight:800;color:#fff;background:#052e74bb;border:1px solid #5ba9f8}
.t-tag.orange{background:linear-gradient(120deg,#f66e20,#ffa43b);border-color:#ffe39b}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px}
div.stLinkButton a{border-radius:11px;font-weight:750}
h2,h3{color:#0e3a7a}
.form-section-title{font-size:22px!important;line-height:1.35;font-weight:850;color:#0a3679;margin:2px 0 11px;letter-spacing:0}
@media(max-width:700px){
 .t-header{padding:17px 10px;border-radius:15px}
 .t-title{font-size:clamp(31px,8.2vw,49px)}
 .t-sub{font-size:clamp(14px,4.1vw,19px);border-radius:19px;padding:12px 10px}
 .t-shop-offer{font-size:clamp(18px,5vw,25px);padding:11px 8px;border-radius:13px}
 .t-shop-contact{font-size:clamp(15px,4.3vw,22px);padding:8px}
 .t-shop-contact a{margin-left:3px;padding:2px 6px}
 .t-tags{gap:6px}.t-tag{font-size:11px;padding:6px 9px}
}

/* Reference-inspired feature cards and responsive form workspace */
body,[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,#e9f5ff 0,#f4f9ff 420px,#ffffff 100%)}
.th-nav{background:linear-gradient(90deg,#001848,#0745a5);color:white;padding:12px 22px;border-radius:14px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap;border-bottom:2px solid #11d5ff;font-size:15px;font-weight:750}
.th-nav strong{font-size:20px;color:#ffe075}.th-nav a{color:#fff5ce;text-decoration:none}
.th-features{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin:0 0 20px}
.th-feature{background:linear-gradient(155deg,#fff,#eaf4ff);border:1px solid #d1e3f9;border-radius:17px;padding:16px 13px;display:flex;gap:12px;align-items:center;box-shadow:0 5px 14px #002b6d18}
.th-feature-icon{font-size:28px;background:#0759e9;color:white;border-radius:12px;padding:9px 12px}
.th-feature:nth-child(2) .th-feature-icon{background:#f43877}.th-feature:nth-child(3) .th-feature-icon{background:#0cac6d}.th-feature:nth-child(4) .th-feature-icon{background:#f27617}
.th-feature b{font-size:15px;color:#042e77}.th-feature span{color:#607089;font-size:12px;line-height:1.5}
.th-section-h{background:linear-gradient(100deg,#063b9c,#0060e0);border-radius:11px;padding:13px 17px;color:white;font-size:19px;font-weight:850;margin:4px 0 18px}
.form-section-title{font-size:19px!important;border-left:5px solid #1766e9;padding-left:9px;line-height:1.4;margin:5px 0 10px}
.th-preview{background:linear-gradient(120deg,#120902,#7b3c04 55%,#291303);min-height:280px;border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#fff;box-shadow:inset 0 0 70px #e2aa3566;margin:11px 0 8px;overflow:hidden}
.th-preview .coffee{font-size:68px;filter:drop-shadow(2px 5px 6px #0009)}
.th-preview .coffee-title{color:#ffdf8f;font-size:clamp(34px,3.3vw,55px);font-weight:950;text-shadow:0 4px 2px #290d00}
.th-preview .coffee-sub{font-size:20px;font-weight:750}.th-preview .price{font-size:25px;color:#ffdc62;font-weight:950}
.th-foot{background:linear-gradient(105deg,#00246c,#0752b3,#00246c);border-radius:16px;color:white;display:flex;flex-wrap:wrap;justify-content:space-around;gap:14px;padding:19px;margin-top:27px;font-weight:750;text-align:center}
@media(max-width:950px){.th-features{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:570px){.th-features{grid-template-columns:1fr}.th-nav{font-size:12px}.th-feature{padding:12px}}
</style>
""",unsafe_allow_html=True)

# LINE URL can be configured in Streamlit Cloud Settings > Secrets.
# Do not insert a guessed LINE account: it might send customers to the wrong person.
try:
    line_url = str(st.secrets.get("LINE_CONTACT_URL", "")).strip()
except Exception:
    line_url = ""
line_ok = line_url.startswith(("https://lin.ee/", "https://line.me/", "https://page.line.me/"))
line_html = (
    '<a class="t-contact-line" href="' + html.escape(line_url, quote=True) +
    '" target="_blank" rel="noopener noreferrer">💬 รับออเดอร์ออกแบบ / พิมพ์ป้ายผ่าน LINE</a>'
    if line_ok else ""
)
st.markdown("""
<div class="th-nav"><strong>✦ ธนศิลป์ AI Design</strong><span>หน้าแรก　 ·　 สร้างคำสั่ง AI　 ·　 บริการงานพิมพ์</span><a href="tel:0913675929">☎ 091-367-5929</a></div>
""", unsafe_allow_html=True)

st.markdown("""
<section class="t-header">
  <div class="t-title"><span class="brand">ธนศิลป์</span> <span class="ai">AI</span> <span class="design">Design</span></div>
  <div class="t-sub">เครื่องมือสร้างคำสั่งออกแบบป้าย <span class="t-accent">สวย คมชัด อ่านง่าย</span> พร้อมนำไปสร้างภาพใน <span class="t-ai-names">ChatGPT และ Gemini</span></div>
  <div class="t-shop-offer"><span class="t-service-highlight">รับพิมพ์งานสิ่งพิมพ์ทุกชนิด</span> <strong>จัดส่งทั่วไทย</strong></div>
  <div class="t-shop-contact">สอบถามราคา <a href="tel:0913675929">091-367-5929</a></div>
  <div class="t-shop-buttons">
    <a class="t-contact-call" href="tel:0913675929">📞 โทรสอบถามราคา</a>
    """ + line_html + """
  </div>
  <div class="t-tags">
    <span class="t-tag orange">✦ ใช้งานฟรี</span>
    <span class="t-tag">ไม่ต้องใช้ API Key</span>
  </div>
</section>
""", unsafe_allow_html=True)

st.markdown("""
<div class="th-features">
<div class="th-feature"><div class="th-feature-icon">✦</div><div><b>สร้างคำสั่ง AI ได้ทันที</b><br><span>ใช้กับ ChatGPT และ Gemini</span></div></div>
<div class="th-feature"><div class="th-feature-icon">▣</div><div><b>สวย คมชัด อ่านง่าย</b><br><span>คำสั่งออกแบบหลายประเภท</span></div></div>
<div class="th-feature"><div class="th-feature-icon">▤</div><div><b>บริการงานพิมพ์จริง</b><br><span>สอบถามงานพิมพ์กับร้านโดยตรง</span></div></div>
<div class="th-feature"><div class="th-feature-icon">🚚</div><div><b>จัดส่งทั่วไทย</b><br><span>บริการจัดส่งงานสิ่งพิมพ์</span></div></div>
</div>
""", unsafe_allow_html=True)

def section_title(title):
    st.markdown(f'<div class="form-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)

WORK = ['ออกแบบป้ายใหม่','ฟื้นฟูภาพบุคคล / ภาพเก่า','แก้ไขภาพเดิม','ปรับคุณภาพ Ultra-Sharp','แปลงเป็นเวกเตอร์','ลบข้อความคงพื้นหลัง','เปลี่ยนสีและองค์ประกอบ','ปรับขนาดภาพ','สร้างพื้นหลังเปล่า','Depth Map / CNC']
TYPES = ['ร้านค้า / อาหาร / บริการ','งานบุญ / กฐิน / วัด','ราชการ / โรงเรียน / โครงการ','งานศพ / อาลัย','เกษียณ / แสดงความยินดี','งานวิชาการ / ประชาสัมพันธ์','ป้ายชื่อหน่วยงาน','อื่น ๆ']
STYLES = ['เรียบหรู มืออาชีพ','สุภาพ เป็นทางการ','โมเดิร์น ทันสมัย','ลายไทยประยุกต์','มินิมอล สะอาดตา','สีสันสดใส โดดเด่น','ตัวหนังสือสามมิติ','ตามภาพตัวอย่าง']

tab_sign,tab_photo,tab_graphic,tab_extra,tab_shirt_relief=st.tabs(['🪧 ออกแบบป้าย','📸 แต่งภาพบุคคล','🎨 ออกแบบกราฟิก','🧰 เครื่องมือพิเศษ','👕 เสื้อพิมพ์ลาย / รูปนูน 3D'])

with tab_sign:
    st.markdown('<div class="th-section-h">✦ สร้างคำสั่งออกแบบป้ายด้วย AI</div>',unsafe_allow_html=True)
    st.caption('เลือกประเภทงาน ขนาดป้าย และรูปแบบ แล้วนำคำสั่งไปใช้ใน ChatGPT หรือ Gemini')

    with st.container(border=True):
        first,second=st.columns(2)
        with first:
            section_title('1. ประเภทงาน')
            work=st.selectbox('ประเภทงาน',WORK,label_visibility='collapsed')
        with second:
            section_title('2. ประเภทป้าย')
            kind=st.selectbox('ประเภทป้าย',TYPES,label_visibility='collapsed')

        cs1,cs2=st.columns([1.15,1])
        with cs1:
            section_title('3. ขนาดและทิศทางป้าย')
            direction=st.radio('ทิศทาง',['แนวนอน','แนวตั้ง','สี่เหลี่ยมจัตุรัส','ตามสัดส่วนต้นฉบับ'],horizontal=False)
            preset=st.selectbox('ขนาดสำเร็จรูป (ซม.)',['กำหนดเอง','200 × 100','300 × 150','400 × 200','120 × 240'])
        with cs2:
            section_title('4. สไตล์')
            style=st.selectbox('สไตล์',STYLES,label_visibility='collapsed')
            st.caption('เลือกสไตล์การออกแบบให้เหมาะกับงาน')
            st.info('แนบรูปตัวอย่างใน ChatGPT หรือ Gemini ได้โดยตรง',icon='🎨')
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
        with cw: w=st.number_input('กว้าง (ซม.)',min_value=1.0,value=300.0,step=10.0,key='width_cm')
        with ch: h=st.number_input('สูง (ซม.)',min_value=1.0,value=150.0,step=10.0,key='height_cm')
        actual='แนวนอน' if w>h else 'แนวตั้ง' if h>w else 'สี่เหลี่ยมจัตุรัส'
        if direction in ['แนวนอน','แนวตั้ง','สี่เหลี่ยมจัตุรัส'] and direction!=actual:
            st.warning(f'ขนาดที่กรอกเป็น{actual} แต่เลือก {direction} โปรดแก้ให้ตรงกัน')
        section_title('5. ข้อความบนป้าย')
        textless=st.checkbox('ไม่ใส่ข้อความ จะเพิ่มเอง')
        wording=st.text_area('ข้อความบนป้าย',label_visibility='collapsed',height=125,disabled=textless,placeholder='พิมพ์ข้อความที่ต้องการให้ปรากฏบนป้าย')
        section_title('6. รายละเอียดเพิ่มเติม')
        opts=st.multiselect('ตัวเลือกพิเศษ',['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','เน้นรูปภาพ','คงโครงสร้างเดิม','ตกแต่งเพิ่มเติมอัตโนมัติ','ไม่ใส่ตาไก่','เพิ่มพื้นที่ว่างสำหรับข้อความ','คงใบหน้าบุคคลตามต้นฉบับ','ลบโลโก้เดิม'],default=['Ultra-Sharp','เน้นข้อความให้อ่านชัด','พร้อมสำหรับงานพิมพ์','ตกแต่งเพิ่มเติมอัตโนมัติ'])
        extra=st.text_area('รายละเอียดเพิ่มเติม (ถ้ามี)',height=83)


with tab_photo:
    st.markdown('### 📸 แต่งภาพบุคคล / ฟื้นฟูภาพ')
    st.caption('เลือกงานแล้วแนบรูปต้นฉบับใน ChatGPT หรือ Gemini เพื่อใช้เป็นภาพอ้างอิง')
    photo_task=st.selectbox('ประเภทงานแต่งภาพ', ['ฟื้นฟูภาพเก่า / เพิ่มความคมชัด','ภาพชุดแต่งงาน (ใช้ใบหน้าอ้างอิง)','ภาพครอบครัว (ใช้ใบหน้าหลายภาพ)','เปลี่ยนพื้นหลัง / สถานที่ทั่วโลก','เปลี่ยนชุดไทย / ชุดสูท / ชุดอื่น ๆ','ลบคนหรือสิ่งของออกจากภาพ','รูปงานบวช / ภาพนาค','แต่งสีผิว รูปร่าง ดวงตา รอยยิ้ม','ภาพติดบัตร / ภาพหน้าตรง','ภาพเหมือนถ่ายในสตูดิโอ'],key='photo_task')
    photo_details=st.text_area('รายละเอียดภาพที่ต้องการ เช่น ชุด สถานที่ จำนวนคน ฉากหลัง',height=110,key='photo_details')
    photo_ratio=st.selectbox('สัดส่วนภาพ',['คงสัดส่วนต้นฉบับ','3:4 แนวตั้ง','4:3 แนวนอน','1:1 สี่เหลี่ยม','9:16 แนวตั้ง','16:9 แนวนอน'],key='photo_ratio')
    photo_real=st.checkbox('รักษาใบหน้าและเอกลักษณ์บุคคลตามภาพต้นฉบับ',value=True,key='photo_real')
    st.caption('ภาพ AI อาจไม่เหมือนต้นฉบับทุกจุด และต้องแนบภาพบุคคลด้วยตนเองในบริการ AI ที่เลือก')
with tab_graphic:
    st.markdown('### ✨ ออกแบบกราฟิก')
    graphic_task=st.selectbox('ประเภทงานกราฟิก',['ออกแบบโลโก้','ออกแบบกรอบ QR Code','ออกแบบป้ายขายของ','ออกแบบตารางเรียน / ตารางกิจกรรม','ออกแบบงานกราฟิกอื่น ๆ'],key='graphic_task')
    graphic_text=st.text_area('ข้อความ / รายการ / ชื่อร้าน / ตารางเรียน',height=130,key='graphic_text')
    graphic_details=st.text_area('รายละเอียด สี รูปแบบ ขนาด และข้อมูลอื่น ๆ',height=95,key='graphic_details')
    if graphic_task=='ออกแบบกรอบ QR Code':
        st.info('เพื่อให้สแกนได้จริง ให้นำ QR Code ที่สร้างจากลิงก์จริงมาใส่ในกรอบที่ออกแบบ ไม่ใช้ QR Code ที่ AI วาดขึ้น')


with tab_extra:
    st.markdown('### 🧰 เครื่องมือพิเศษสำหรับงานออกแบบ')
    st.caption('เลือกงานที่ต้องการ กรอกข้อความ แล้วเลือกหมวดเครื่องมือพิเศษก่อนส่งคำสั่งในข้อ 7')
    special_categories={
        'ตัวหนังสือ / ไดคัท':['ตัวหนังสือ 3D / ไดคัท'],
        'ปรับปรุงรูปถ่าย':['ซ่อมภาพเก่า / ภาพขาด'],
        'เวกเตอร์ / งานผลิต':['เวกเตอร์ / CNC / เลเซอร์'],
        'ออกแบบสินค้า':['ออกแบบลายเสื้อ','เสื้อพิมพ์ลาย','ออกแบบเมนูอาหาร'],
        'ภาพและสื่อออนไลน์':['ภาพอาลัย / กรอบรูปงานศพ','โพสต์ Facebook / TikTok'],
        'งานนูน / Relief 3D':['แปลงรูปนูน 2.5D / 3D'],
        'คำสั่งสำเร็จรูป':['คำสั่งสำเร็จรูป']
    }
    special_category=st.selectbox('หมวดงาน',list(special_categories),key='special_category')
    special_task=st.selectbox('ฟังก์ชัน',special_categories[special_category],key='special_task')
    relief_mode=''
    relief_view=''
    shirt_style=''
    shirt_view=''
    if special_task=='แปลงรูปนูน 2.5D / 3D':
        relief_mode=st.selectbox('ประเภทงานนูน',['2.5D Bas-Relief','3D Sculpture / Multi-view'],key='relief_mode')
        relief_view=st.selectbox('มุมมอง',['หน้าตรง Orthographic','หน้า + ซ้าย + ขวา','หน้า + ซ้าย + ขวา + หลัง','หลายมุม Orthographic (แยกภาพแต่ละมุม)'],key='relief_view')
    if special_task=='เสื้อพิมพ์ลาย':
        shirt_style=st.selectbox('ชนิดเสื้อ',['เสื้อคอกลม','เสื้อโปโล','เสื้อกีฬา','เสื้อทีม','เสื้อแฟชั่น'],key='shirt_style')
        shirt_view=st.selectbox('ด้านของเสื้อ',['ด้านหน้า','ด้านหลัง','ด้านหน้าและด้านหลัง','รอบตัว'],key='shirt_view')
    special_template=''
    if special_task=='คำสั่งสำเร็จรูป':
        special_template=st.selectbox('เลือกคำสั่งด่วน',[
            'ทำภาพคมชัด คงใบหน้าเดิม','ลบข้อความ คงพื้นหลัง',
            'เปลี่ยนฉากหลัง คงบุคคล','ทำภาพสีสมจริงจากภาพเก่า',
            'ตัวหนังสือ 3D เด่นชัด','ป้ายสำหรับพิมพ์ ไม่ใส่ตาไก่',
            'รูปติดบัตรหน้าตรง','ทำลายเส้นขาวดำสำหรับเวกเตอร์'
        ],key='special_template')
    special_text=st.text_area('ข้อความบนภาพ / ชื่อร้าน / รายละเอียดหลัก (ถ้ามี)',height=105,key='special_text')
    special_details=st.text_area('รายละเอียดเพิ่มเติม เช่น สี ขนาด ชุด ฉาก องค์ประกอบ',height=90,key='special_details')
    special_ratio=st.selectbox('สัดส่วน', ['ตามต้นฉบับ / ตามรายละเอียด','แนวนอน 16:9','แนวตั้ง 3:4','สี่เหลี่ยม 1:1','แนวนอน 2:1'],key='special_ratio')
    st.caption('หากใช้อ้างอิงภาพหรือใบหน้า ให้นำภาพไปแนบใน ChatGPT หรือ Gemini หลังเปิดแชท')


with tab_shirt_relief:
    st.markdown('### 👕 เสื้อพิมพ์ลาย / รูปนูน 2.5D–3D')
    direct_task=st.radio('เลือกงาน',['เสื้อพิมพ์ลาย','แปลงรูปนูน 2.5D / 3D'],horizontal=True,key='direct_task')
    if direct_task=='เสื้อพิมพ์ลาย':
        direct_shirt=st.selectbox('ชนิดเสื้อ',['เสื้อคอกลม','เสื้อโปโล','เสื้อกีฬา','เสื้อทีม','เสื้อแฟชั่น'],key='direct_shirt')
        direct_view=st.selectbox('ด้านที่ต้องการ',['ด้านหน้า','ด้านหลัง','ด้านหน้าและด้านหลัง','รอบตัว'],key='direct_shirt_view')
    else:
        direct_relief=st.selectbox('รูปแบบงานนูน',['2.5D Bas-Relief','3D Sculpture / Multi-view'],key='direct_relief')
        direct_relief_view=st.selectbox('มุมมอง',['หน้าตรง Orthographic','หน้า + ซ้าย + ขวา','หน้า + ซ้าย + ขวา + หลัง','หลายมุม Orthographic แยกภาพ'],key='direct_relief_view')
    direct_text=st.text_area('ข้อความ / ลวดลาย / สิ่งที่ต้องการสร้าง',height=110,key='direct_text')
    direct_details=st.text_area('รายละเอียดเพิ่มเติม (สี รูปภาพอ้างอิง ขนาด)',height=90,key='direct_details')
    st.caption('เลือกหมวด “เสื้อพิมพ์ลาย / รูปนูน 3D” ที่หัวข้อส่งคำสั่งด้านล่างเพื่อใช้ข้อมูลแท็บนี้')

def get_font_guideline(kind, style):
    """เลือกแนวทางจัดฟอนต์อัตโนมัติ ให้หัวเรื่องและรายละเอียดแตกต่างแต่ยังอ่านง่าย"""
    if any(term in kind for term in ('งานบุญ', 'กฐิน', 'วัด')):
        theme='หัวเรื่องฟอนต์ไทยอ่อนช้อยสง่างาม มีกลิ่นอายลายไทยประยุกต์เล็กน้อย; ข้อความรองใช้ฟอนต์สุภาพ; กำหนดการใช้ฟอนต์เรียบชัด'
    elif any(term in kind for term in ('ราชการ', 'โรงเรียน', 'โครงการ', 'หน่วยงาน')):
        theme='หัวเรื่องฟอนต์ไทยทางการเด่นชัด; ชื่อหน่วยงานและเนื้อหาใช้ฟอนต์มาตรฐานสุภาพ อ่านง่าย'
    elif any(term in kind for term in ('ร้านค้า', 'อาหาร', 'บริการ')):
        theme='ชื่อร้านใช้ฟอนต์โดดเด่นมีเอกลักษณ์หรือตัวอักษรมีมิติ; เมนูและโปรโมชั่นใช้ฟอนต์หนาชัด; รายละเอียดติดต่อใช้ฟอนต์เรียบ'
    elif any(term in kind for term in ('งานศพ', 'อาลัย')):
        theme='หัวเรื่องฟอนต์ไทยเรียบหรู สำรวม; ชื่อบุคคลเด่นชัด; รายละเอียดใช้ฟอนต์สุภาพอ่านง่าย'
    elif any(term in kind for term in ('เกษียณ', 'แสดงความยินดี')):
        theme='หัวเรื่องฟอนต์ไทยอบอุ่นนุ่มนวลและสง่างาม; ชื่อบุคคลเด่น; ข้อมูลรองใช้ฟอนต์อ่านง่าย'
    else:
        theme='หัวเรื่องใช้ฟอนต์เด่นเข้ากับประเภทงาน; ข้อความรองและรายละเอียดใช้ฟอนต์อ่านง่าย'
    return (
        'แนวทางฟอนต์ตามงาน ('+style+'): '+theme+
        '; ไม่ใช้ฟอนต์รูปแบบเดียวทั้งป้าย ให้จับคู่ฟอนต์ 2–3 บุคลิกที่เข้ากัน '+
        'แยกหัวเรื่อง ข้อความรอง และรายละเอียดด้วยขนาด น้ำหนัก สี และลวดลายอย่างสมดุล '+
        'หัวเรื่องเพิ่มมิติ เงา หรือเส้นขอบได้ตามสมควร แต่ห้ามลดความอ่านง่าย '+
        'รักษาตัวสะกด ช ซ ด ต ถ ฮ สระ วรรณยุกต์ และช่องไฟให้ถูกต้อง'
    )

font_guideline = get_font_guideline(kind, style)

portrait_restore_guideline = (
    'ฟื้นฟูภาพบุคคลที่แนบให้เป็นภาพสีสมจริงแบบ Hyperrealism โดยยึดใบหน้าเดิมต้นฉบับอย่างเคร่งครัด '
    'รักษาเอกลักษณ์และสัดส่วนใบหน้า ตา จมูก ปาก รูปหน้า และทรงผม ห้ามเปลี่ยนเป็นคนอื่นหรือแต่งโครงหน้าใหม่ '
    'คงท่าทาง เสื้อผ้า และฉากต้นฉบับให้ใกล้เคียงที่สุด พร้อมฟื้นฟูสี แสง รายละเอียดเส้นผม ผิว และเนื้อผ้าอย่างเป็นธรรมชาติ '
    'แต่งหน้าอ่อน ๆ เฉพาะเมื่อเหมาะสมและไม่ขัดกับบุคคลหรือความต้องการเดิม: แก้มพีช ปากนู้ด ผิวพอร์ซเลนแบบสมจริง '
    'โทนภาพเหมือนถ่ายด้วย Canon EOS R5, 85mm f/1.2 ฉากหลังละลายอย่างพอดีเฉพาะเมื่อไม่ทำให้ฉากเดิมสูญหาย '
    'เน้นคุณภาพภาพระดับ 4K เท่าที่ระบบรองรับ; ใช้อัตราส่วน 3:4 เฉพาะเมื่อผู้ใช้ไม่ระบุขนาดหรือสัดส่วนอื่น '
    'ห้ามอ้างว่ารักษาใบหน้าได้ 100% หากภาพต้นฉบับไม่ชัด และห้ามสร้างรายละเอียดใบหน้าที่ไม่สามารถยืนยันได้เป็นข้อเท็จจริง'
)
is_portrait_restore = (work == 'ฟื้นฟูภาพบุคคล / ภาพเก่า')
portrait_instruction = portrait_restore_guideline if is_portrait_restore else ''

# The three tabs share the same output controls, but generate prompts for their own work type.
TASK_GUIDES = {
    "ฟื้นฟูภาพเก่า / เพิ่มความคมชัด": "คืนสีและรายละเอียดที่ยังตรวจสอบได้ ลดรอยขีดข่วนและความพร่า ไม่สร้างหรือเปลี่ยนใบหน้าใหม่",
    "ภาพชุดแต่งงาน (ใช้ใบหน้าอ้างอิง)": "ใช้ใบหน้าจากภาพอ้างอิง สร้างชุดแต่งงานและฉากงานแต่ง โดยรักษาเอกลักษณ์บุคคลเดิม",
    "ภาพครอบครัว (ใช้ใบหน้าหลายภาพ)": "นำบุคคลจากภาพอ้างอิงแต่ละใบมารวมเป็นภาพครอบครัว จัดตำแหน่งและแสงให้สอดคล้อง ห้ามสลับใบหน้า",
    "เปลี่ยนพื้นหลัง / สถานที่ทั่วโลก": "เปลี่ยนเฉพาะฉากหลังเป็นสถานที่ที่ระบุในรายละเอียด ให้แสงและมุมกล้องสมจริง",
    "เปลี่ยนชุดไทย / ชุดสูท / ชุดอื่น ๆ": "เปลี่ยนชุดตามที่ระบุ เช่น ชุดไทย ชุดสูท หรือชุดอื่น แต่รักษาใบหน้าและบุคลิกเดิม",
    "ลบคนหรือสิ่งของออกจากภาพ": "ลบเฉพาะบุคคลหรือวัตถุที่ระบุ เติมพื้นหลังอย่างแนบเนียน โดยคงบุคคลหลักและส่วนอื่น",
    "รูปงานบวช / ภาพนาค": "สร้างภาพที่ระลึกงานบวชจากภาพบุคคลอ้างอิง แต่งชุดและฉากตามที่กำหนด โดยรักษาใบหน้าเดิม",
    "แต่งสีผิว รูปร่าง ดวงตา รอยยิ้ม": "ปรับเฉพาะจุดที่ผู้ใช้ร้องขออย่างเป็นธรรมชาติ ไม่เปลี่ยนเอกลักษณ์ใบหน้าหรือสัดส่วนจนผิดคน",
    "ภาพติดบัตร / ภาพหน้าตรง": "ปรับภาพหน้าตรง แสงสม่ำเสมอ พื้นหลังและชุดตามที่กำหนด รักษาเอกลักษณ์เดิม; ตรวจข้อกำหนดรูปสำหรับเอกสารราชการจริง",
    "ภาพเหมือนถ่ายในสตูดิโอ": "จัดแสงฉากและองค์ประกอบแบบสตูดิโอ พร้อมรายละเอียดผิวและเส้นผมสมจริง โดยรักษาใบหน้าเดิม",
    "ออกแบบโลโก้": "สร้างแนวคิดตราสัญลักษณ์เรียบชัด จดจำง่าย ตรงชื่อธุรกิจ เหมาะต่อการต่อยอดเป็นเวกเตอร์",
    "ออกแบบกรอบ QR Code": "ออกแบบกรอบ พื้นหลัง และข้อความรอบพื้นที่ QR Code โดยเว้นช่องกลางให้แทรก QR Code จริง ห้ามสร้าง QR Code ปลอมด้วยภาพ AI",
    "ออกแบบป้ายขายของ": "ออกแบบป้ายขายของเน้นชื่อสินค้า ราคา จุดขายและข้อมูลติดต่อ อ่านง่ายสีตัดพื้น",
    "ออกแบบตารางเรียน / ตารางกิจกรรม": "ออกแบบตารางอ่านง่าย ช่องวันเวลาเป็นระเบียบ ตรวจความครบถ้วนและตัวสะกด; หากไม่มีข้อมูลให้เว้นช่องสำหรับกรอก",
    "ออกแบบงานกราฟิกอื่น ๆ": "ออกแบบกราฟิกตามรายละเอียดที่ระบุ รักษาตัวสะกดและสัดส่วนที่ต้องการ",
}
SPECIAL_GUIDES={
    'ตัวหนังสือ 3D / ไดคัท':'ออกแบบตัวอักษรไทยตกแต่ง 3 มิติหรือไดคัท แยกจากพื้นหลัง ขอบคม สีและเงามีมิติ จัดสระวรรณยุกต์ไม่ทับกัน รักษาการสะกดทุกตัว',
    'ซ่อมภาพเก่า / ภาพขาด':'ซ่อมรอยฉีก จุดรบกวน คราบ ฝุ่น และความซีด ฟื้นฟูสีและรายละเอียดจากต้นฉบับ โดยรักษาใบหน้าจริงและฉาก ไม่สร้างรายละเอียดที่ยืนยันไม่ได้',
    'เวกเตอร์ / CNC / เลเซอร์':'แปลงภาพอ้างอิงเป็นลายเส้นสะอาด ขอบชัด เส้นต่อเนื่อง พื้นขาวเส้นดำหรือกำหนดสีตามรายละเอียด ลดจุดรบกวน เหมาะเป็นต้นแบบสำหรับนำไปทำเวกเตอร์ CNC หรือเลเซอร์ ตรวจไฟล์เวกเตอร์จริงก่อนผลิต',
    'ออกแบบลายเสื้อ':'ออกแบบลายเสื้อหรือเสื้อกีฬา จัดลวดลาย สี คอปก แขนเสื้อ และตัวเสื้ออย่างสมดุล สามารถแสดงหน้าหลังตามคำสั่ง และรักษาโลโก้ข้อความตามต้นฉบับ',
    'ออกแบบเมนูอาหาร':'จัดเมนูอาหารพร้อมภาพประกอบน่ารับประทาน ชื่ออาหารและราคาตรงตามที่ให้ อ่านง่าย ภาพอาหารเหมาะกับรายการ ไม่แต่งข้อความเกินจริง',
    'ภาพอาลัย / กรอบรูปงานศพ':'ออกแบบภาพอาลัยอย่างสุภาพ ดอกไม้และพื้นหลังพอเหมาะ รักษาใบหน้าเดิมของบุคคลอย่างเคร่งครัด และสะกดชื่อ วันเดือนปี สิริอายุให้ตรงต้นฉบับ',
    'โพสต์ Facebook / TikTok':'ออกแบบสื่อโปรโมทสำหรับ Facebook หรือ TikTok พาดหัวเด่น อ่านง่ายบนมือถือ เว้นระยะขอบไม่ตัดข้อความ และใช้ขนาดภาพตามที่กำหนด',
    'เสื้อพิมพ์ลาย':'ออกแบบลายพิมพ์ลงเสื้อจริง สีสด คมชัด รายละเอียดเหมาะกับชนิดผ้าและเทคนิคการพิมพ์ สะกดชื่อทีมและโลโก้ตรงต้นฉบับ แสดงแบบเสื้อด้านที่เลือก',
    'แปลงรูปนูน 2.5D / 3D':'แปลงภาพอ้างอิงเป็นงานประติมากรรมนูนแบบ 2.5D หรือ 3D หลายมุม โครงสร้างสะอาด แยกชั้นความลึก คมชัดเหมาะใช้เป็นต้นแบบ CNC และงานแกะสลัก',
    'คำสั่งสำเร็จรูป':'สร้างงานจากคำสั่งด่วนตามตัวเลือกที่ระบุ โดยรักษาภาพอ้างอิง ข้อความ และข้อกำหนดอย่างเคร่งครัด'
}
PRESET_GUIDES={
    'ทำภาพคมชัด คงใบหน้าเดิม':'เพิ่มความละเอียดและฟื้นฟูภาพโดยไม่เปลี่ยนเอกลักษณ์ใบหน้า ตา จมูก ปาก ทรงผม',
    'ลบข้อความ คงพื้นหลัง':'ลบตัวหนังสือทั้งหมดและเติมบริเวณเดิมให้เนียน คงภาพ สี และองค์ประกอบอื่น',
    'เปลี่ยนฉากหลัง คงบุคคล':'เปลี่ยนเฉพาะฉากหลังเป็นสถานที่ที่ระบุ คงหน้าตาและท่าทางบุคคลหลัก',
    'ทำภาพสีสมจริงจากภาพเก่า':'คืนสีสมจริงตามหลักฐานจากภาพเดิม โดยไม่แต่งโครงหน้าหรือเปลี่ยนเอกลักษณ์',
    'ตัวหนังสือ 3D เด่นชัด':'ทำตัวหนังสือสามมิติ มีเงาและขอบชัด อ่านง่าย เหมาะกับการไดคัท',
    'ป้ายสำหรับพิมพ์ ไม่ใส่ตาไก่':'จัดงานป้ายตามขนาดที่ระบุ คมชัดสำหรับพิมพ์ ไม่มีตาไก่ ไม่มีภาพจำลองติดตั้ง',
    'รูปติดบัตรหน้าตรง':'รูปหน้าตรง พื้นหลังเรียบ ชุดสุภาพ แสงธรรมชาติ โดยคงใบหน้าจริง ตรวจข้อกำหนดของหน่วยงานก่อนใช้',
    'ทำลายเส้นขาวดำสำหรับเวกเตอร์':'สร้างต้นแบบลายเส้นขาวดำเส้นคม ต่อกันครบ พร้อมนำไปทำเวกเตอร์จริง'
}
def build_special_prompt():
    pieces=[
        'สร้างคำสั่งออกแบบ / แก้ไขภาพจากภาพที่ผู้ใช้แนบ (หากมี)',
        f'หมวดงาน: {special_category}',
        f'ประเภทงาน: {special_task}',
        f'สัดส่วนภาพ: {special_ratio}',
        f'ข้อความหลัก: {special_text or "ไม่มีข้อความเพิ่มเติม"}',
        f'รายละเอียด: {special_details or "ออกแบบให้เหมาะกับประเภทงาน"}',
        SPECIAL_GUIDES[special_task]
    ]
    if special_task=='เสื้อพิมพ์ลาย':
        pieces.extend([
            f'ชนิดเสื้อ: {shirt_style}',f'มุมแสดงแบบ: {shirt_view}',
            'ออกแบบแพตเทิร์นลายเสื้อพิมพ์ลายจริง ทั้งภาพต้นแบบลายแบนและภาพจำลองการสวมใส่ตามมุมที่เลือก โดยคงตัวหนังสือ โลโก้ และตำแหน่งให้ตรงตามที่ระบุ'
        ])
    if special_task=='แปลงรูปนูน 2.5D / 3D':
        pieces.extend([
            f'ชนิดงานนูน: {relief_mode}',f'มุมที่ต้องการ: {relief_view}',
            'Create a highly detailed Thai bas-relief sculpture in ultra-high resolution 16K, subject based on the attached reference. '
            'Smooth polished white ivory plaster or creamy white stone, flawless matte surface, no grain, cracks, scratches or pores. '
            'Deep clean relief with crisp sharp edges, separated depth layers, large ornate Thai Kanok motifs when appropriate to the source, '
            'balanced symmetry when the reference is symmetrical, bold CNC-friendly contours and reduced tiny noisy details. '
            'Strong relief visibility, uniform grayscale depth-map-inspired shading, solid pure black (#000000) background, '
            'no dramatic side lighting, no perspective distortion. Clearly defined flowing contours and anatomical transitions where relevant. '
            'Museum-quality, ultra-clean and detailed, depth-optimized appearance suitable as an image reference for SculptOK or CNC relief extraction. '
            'For 2.5D produce one orthographic front elevation with a consistent shallow relief depth; '
            'for 3D multi-view produce front, left, right and back only as requested, all showing the same object with consistent geometry and aligned scale, '
            'each orthographic view clearly separated, without hallucinated decorative details. '
            'Aim for ultra-sharp 16K aesthetics within the image generator resolution limits. '
            'This is an image / prompt concept, not a manufactured 3D mesh, watertight STL, or verified CNC depth map.'
        ])
    if special_template:
        pieces.extend([f'คำสั่งด่วน: {special_template}',PRESET_GUIDES[special_template]])
    pieces.append('สร้างผลลัพธ์ที่คมชัดตามความสามารถของระบบ ตรวจความถูกต้องของข้อความ และอย่าเปลี่ยนใบหน้าเดิมหากมีบุคคลอ้างอิง')
    return '\n'.join(pieces)

def build_photo_prompt():
    parts=[
        'แก้ไขหรือสร้างภาพบุคคลจากรูปอ้างอิงตามรายละเอียดนี้',
        f'ประเภทงาน: {photo_task}',
        f'สัดส่วนภาพ: {photo_ratio}',
        f'รายละเอียด: {photo_details or "ใช้ภาพที่แนบเป็นต้นฉบับ"}',
        TASK_GUIDES[photo_task],
        'แสง สี เส้นผม ผิวและเสื้อผ้าสมจริง รายละเอียดคมชัดระดับสูงตามที่ระบบรองรับ'
    ]
    if photo_real:
        parts.append('รักษาอัตลักษณ์ของบุคคลในภาพอ้างอิง โดยเฉพาะดวงตา จมูก ปาก โครงหน้า และทรงผม ไม่เปลี่ยนเป็นคนอื่น')
    if photo_task=='ฟื้นฟูภาพเก่า / เพิ่มความคมชัด':
        parts.append(portrait_restore_guideline)
    return '\n'.join(parts)
def build_graphic_prompt():
    return '\n'.join([
        'ออกแบบงานกราฟิกตามข้อมูลต่อไปนี้',
        f'ประเภทงาน: {graphic_task}',
        f'ข้อความที่ต้องใส่: {graphic_text or "ไม่มีข้อความระบุ"}',
        f'รายละเอียด: {graphic_details or "ออกแบบให้เหมาะกับงาน"}',
        TASK_GUIDES[graphic_task],
        'จัดองค์ประกอบให้สวยงาม คมชัด อ่านตัวอักษรภาษาไทยง่าย และรักษาข้อความตามต้นฉบับ'
    ])
sign_prompt='\n'.join([
    'เริ่มออกแบบป้ายตามรายละเอียดนี้',
    f'ประเภทงาน: {work}',
    f'ประเภทป้าย: {kind}',
    f'ขนาด: {w:g} × {h:g} ซม. ({actual})',
    f'ทิศทางที่เลือก: {direction}',
    f'สไตล์: {style}',
    f'ข้อความบนป้าย: {"ไม่มีข้อความ จะเพิ่มเอง" if textless else (wording or "ยังไม่ได้ระบุ")}',
    f'ตัวเลือกเพิ่มเติม: {", ".join(opts) if opts else "ไม่มี"}',
    f'รายละเอียดเพิ่มเติม: {extra or "ไม่มี"}',
    'เลือกโทนสีและจัดองค์ประกอบให้เหมาะกับงาน เน้นข้อความภาษาไทยขนาดใหญ่และอ่านง่าย',
    'รักษาข้อความ ชื่อ วันที่ ตัวเลข และเบอร์โทรให้ตรงต้นฉบับ ตรวจสระ วรรณยุกต์ และพยัญชนะ ช ซ ด ต ถ ฮ',
    'หากมีภาพตัวอย่างให้คงสัดส่วนและรูปแบบเดิม เส้นคมชัด รายละเอียดครบ พร้อมงานพิมพ์',
    font_guideline,
    portrait_instruction,
    'เน้นภาพ Ultra-Sharp คุณภาพสูงสุดที่ระบบรองรับ และหากเลือกไม่ใส่ข้อความ ห้ามสร้างตัวอักษร'
])
def build_direct_prompt():
    pieces=[
        f'ประเภทงาน: {direct_task}',
        f'สิ่งที่ต้องการ: {direct_text or "ใช้รูปภาพอ้างอิงที่แนบ"}',
        f'รายละเอียด: {direct_details or "ออกแบบให้เหมาะกับงาน"}',
        SPECIAL_GUIDES[direct_task]
    ]
    if direct_task=='เสื้อพิมพ์ลาย':
        pieces += [f'ชนิดเสื้อ: {direct_shirt}', f'ด้านที่ต้องการ: {direct_view}',
                   'ขอทั้งลายพิมพ์แบนและภาพจำลองเสื้อ คงองค์ประกอบและข้อความตรงต้นฉบับ พร้อมเป็นแนวทางการผลิต']
    else:
        pieces += [f'ชนิดงานนูน: {direct_relief}',f'มุมมองที่ต้องการ: {direct_relief_view}',
                   'Create an ultra-detailed Thai bas-relief sculpture reference with smooth polished ivory white plaster, pure black #000000 background, orthographic views, flat front lighting, crisp depth layers, bold clean Thai Kanok ornaments where relevant, perfectly clean matte sculpted surfaces without pores or grain, distinct CNC-friendly relief contours and high contrast. 2.5D: produce one frontal shallow bas-relief. 3D: show consistent front, left, right and back orthographic views as selected; do not invent geometry not present in reference. Aim for 16K quality within system limits; image reference only, not a CNC-ready STL or depth map.']
    return '\n'.join(pieces)

# Use a visible selection to control which tab's prompt is sent; Streamlit tabs do not expose active tab to Python.
st.markdown('#### เลือกหมวดคำสั่งที่จะส่ง')
selected_prompt_type=st.radio('เลือกคำสั่งที่ต้องการใช้งาน',['ออกแบบป้าย','แต่งภาพบุคคล','ออกแบบกราฟิก','เครื่องมือพิเศษ','เสื้อพิมพ์ลาย / รูปนูน 3D'],horizontal=True,label_visibility='collapsed',key='selected_prompt_type')
prompt=sign_prompt if selected_prompt_type=='ออกแบบป้าย' else build_photo_prompt() if selected_prompt_type=='แต่งภาพบุคคล' else build_graphic_prompt() if selected_prompt_type=='ออกแบบกราฟิก' else build_special_prompt() if selected_prompt_type=='เครื่องมือพิเศษ' else build_direct_prompt()

section_title('7. ส่งคำสั่งไปสร้างภาพ')
st.caption('คำสั่งของคุณอยู่ในช่องด้านล่าง สามารถคลิกแล้วกด Ctrl+A และ Ctrl+C เพื่อคัดลอกได้ทันที')
st.text_area('คำสั่งพร้อมใช้ (คัดลอกได้)',value=prompt,height=260,key=f'prompt_display_{hash(prompt)}')

# Additional mobile-friendly copy button; original buttons remain unchanged.
safe_mobile_prompt=html.escape(prompt,quote=True)
components.html(f'''
<button id="mobile_copy" style="width:100%;padding:11px;border-radius:9px;border:1px solid #1965cf;background:#176ce7;color:white;font-weight:800;font-size:15px;cursor:pointer">📋 คัดลอกคำสั่ง (มือถือ)</button>
<div id="mobile_status" role="status" style="font:12px Arial;margin-top:6px;color:#234"></div>
<textarea id="mobile_source" style="position:absolute;left:-9999px">{safe_mobile_prompt}</textarea>
<script>
document.getElementById('mobile_copy').onclick=async()=>{{
 const el=document.getElementById('mobile_source'); let copied=false;
 try{{await navigator.clipboard.writeText(el.value);copied=true}}catch(e){{}}
 if(!copied){{try{{el.style.left='0px';el.select();el.setSelectionRange(0,el.value.length);copied=document.execCommand('copy');el.style.left='-9999px'}}catch(e){{}}}}
 document.getElementById('mobile_status').innerText=copied?'✅ คัดลอกแล้ว นำไปวางใน ChatGPT หรือ Gemini ได้เลย':'คัดลอกอัตโนมัติไม่สำเร็จ กรุณาคัดลอกข้อความจากช่องด้านบน';
}};
</script>
''',height=78)

col_gpt,col_gemini=st.columns(2)
with col_gpt:
    gpt_url='https://chatgpt.com/?q='+quote(prompt,safe='')
    if len(gpt_url)<=25000:
        st.link_button('🚀 ส่งคำสั่งไป ChatGPT',gpt_url,use_container_width=True)
        st.caption('เปิด ChatGPT พร้อมใส่ข้อความในช่องแชท (ขึ้นอยู่กับการรองรับของ ChatGPT)')
    else:
        st.warning('ข้อความยาวเกินกว่าจะส่งผ่านลิงก์อย่างปลอดภัย')
        st.link_button('🚀 เปิด ChatGPT', 'https://chatgpt.com/', use_container_width=True)
        st.caption('คัดลอกข้อความในช่องด้านบน (Ctrl+A → Ctrl+C) แล้ววางใน ChatGPT (Ctrl+V)')
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

st.info('วิธีใช้: **ChatGPT** กดส่งคำสั่งโดยตรง (ถ้าเบราว์เซอร์รองรับ) แล้วกดส่งในแชท • **Gemini** กดคัดลอก+เปิด → Ctrl+V → กดส่ง')
st.caption('เว็บไซต์นี้สร้างคำสั่งเท่านั้น ไม่ส่งไฟล์เข้าห้องแชทอัตโนมัติ และไม่ใช้ OpenAI API')


st.markdown("""<div class="th-foot"><span>✦ งานออกแบบระดับมืออาชีพ</span><span>✓ รองรับงานหลายประเภท</span><span>🚚 จัดส่งทั่วไทย</span><span>☎ 091-367-5929</span></div>""",unsafe_allow_html=True)
