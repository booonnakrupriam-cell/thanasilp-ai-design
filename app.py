import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
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


# ========================================================
# ฟรี: สร้างภาพจำลอง PNG ด้วย Pillow (ไม่เรียก API)
# ========================================================
st.divider()
st.subheader('10. สร้างภาพป้ายจำลองฟรี (ไม่ใช้ API)')
st.caption('จัดวางรูป ข้อความ โลโก้ และกรอบลง PNG ในขนาดสัดส่วนป้ายโดยตรง ไม่ใช่ AI สร้างภาพหรือไฟล์เวกเตอร์แท้')
use_border = st.checkbox('ตีเส้นกรอบป้าย', value=True)
use_shadow = st.checkbox('ใส่เงาตัวอักษร', value=True)
font_upload = st.file_uploader('อัปโหลดฟอนต์ไทย .ttf/.otf (แนะนำเพื่อให้ตัวหนังสือไทยอ่านชัด)', type=['ttf','otf'], key='thaifont')
sub_text = st.text_input('ข้อความรอง (ถ้ามี)', value='')
size_level = st.selectbox('ความละเอียด PNG จำลอง', ['ทั่วไป (ยาว 1200 พิกเซล)', 'สูง (ยาว 2400 พิกเซล)'], index=0)
st.caption('สำหรับงานพิมพ์ขนาดใหญ่ โปรดตรวจ DPI และพิกเซลจริงก่อนส่งพิมพ์ การขยาย PNG ไม่ได้สร้างรายละเอียด 16K อัตโนมัติ')

def pick_font(px):
    if font_upload is not None:
        try:
            return ImageFont.truetype(BytesIO(font_upload.getvalue()), px), True
        except Exception:
            pass
    import os
    candidates = [
        '/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf',
        '/usr/share/fonts/truetype/thai/Garuda.ttf',
        '/usr/share/fonts/truetype/tlwg/Garuda.ttf',
        '/usr/share/fonts/truetype/tlwg/Loma.ttf',
        '/usr/share/fonts/truetype/tlwg/Kinnari.ttf',
        'C:/Windows/Fonts/tahoma.ttf',
        'C:/Windows/Fonts/LeelawUI.ttf',
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, px), True
            except Exception:
                pass
    return ImageFont.load_default(), False

def fit_image(im, bounds, fill=False):
    src = im.convert('RGBA')
    target = (max(1,int(bounds[0])), max(1,int(bounds[1])))
    if fill:
        return ImageOps.fit(src, target, method=Image.Resampling.LANCZOS)
    src.thumbnail(target, Image.Resampling.LANCZOS)
    return src

def make_free_banner():
    ratio = w / h
    longest = 2400 if size_level.startswith('สูง') else 1200
    out_w = longest if ratio >= 1 else max(1,round(longest*ratio))
    out_h = longest if ratio < 1 else max(1,round(longest/ratio))
    if ratio == 1:
        out_w = out_h = longest
    out_w = max(100, out_w)
    out_h = max(100, out_h)
    palettes={
        'น้ำเงิน–ทอง':('#123968','#eed38c','#ffffff'),
        'แดง–ทอง':('#921e24','#edca76','#ffffff'),
        'เขียว–ขาว':('#176850','#ffffff','#ffffff'),
        'ชมพู–ขาว':('#a43d73','#ffffff','#ffffff'),
        'ม่วง–ทอง':('#4b2870','#e8c77a','#ffffff'),
        'ดำ–ทอง':('#202124','#ebcf85','#ffffff'),
        'ขาว–น้ำเงิน':('#f7f8fc','#21447b','#153456')
    }
    bg,accent,foreground=palettes.get(color,('#254d78','#f1d398','#ffffff'))
    im=Image.new('RGBA',(out_w,out_h),bg)
    margin=max(8,int(min(out_w,out_h)*0.045))

    if primary:
        source=Image.open(BytesIO(primary.getvalue()))
        if position=='พื้นหลังเต็มป้าย':
            background=fit_image(source,(out_w,out_h),True)
            # ลดความเข้มเพื่อข้อความไม่จม
            overlay=Image.new('RGBA',(out_w,out_h),(0,0,0,118))
            im=Image.alpha_composite(background,overlay)
        else:
            area=(int(out_w*.40),int(out_h*.65))
            obj=fit_image(source,area)
            if position=='ด้านซ้าย':
                x=margin
            elif position=='ตรงกลาง':
                x=(out_w-obj.width)//2
            else:
                x=out_w-margin-obj.width
            y=max(margin,(out_h-obj.height)//2)
            im.alpha_composite(obj,(max(0,x),max(0,y)))

    dr=ImageDraw.Draw(im)
    if use_border and out_w>margin*3 and out_h>margin*3:
        dr.rectangle((margin//2,margin//2,out_w-margin//2-1,out_h-margin//2-1),
                     outline=accent,width=max(3,margin//8))

    if logo:
        lim=fit_image(Image.open(BytesIO(logo.getvalue())),(out_w*.18,out_h*.25))
        if logo_position=='ขวาบน':
            x=out_w-margin-lim.width
        elif logo_position=='กลางบน':
            x=(out_w-lim.width)//2
        elif logo_position=='ด้านล่าง':
            x=margin
        else:
            x=margin
        y=out_h-margin-lim.height if logo_position=='ด้านล่าง' else margin
        im.alpha_composite(lim,(max(0,x),max(0,y)))

    headline='' if textless else (wording.strip() or '')
    label=headline  # ถ้าไม่ได้กรอกข้อความ ให้เว้นพื้นที่ว่าง ไม่แสดงคำหลอก
    # จำกัดพื้นที่ข้อความเพื่อไม่ให้ทับรูปและโลโก้
    text_x=margin+int(out_w*.03)
    text_w=int(out_w*.56) if primary and position!='พื้นหลังเต็มป้าย' else out_w-2*text_x
    text_top=int(out_h*.27) if logo else int(out_h*.22)
    text_max_h=int(out_h*.66)
    lines=[]
    for paragraph in label.splitlines():
        paragraph=paragraph.strip()
        if not paragraph:
            lines.append('')
        else:
            lines.append(paragraph)
    if label:
        max_font=max(16, min(int(out_h*.17),int(out_w*.075)))
        for font_size in range(max_font,13,-2):
            font,thai_supported=pick_font(font_size)
            parsed=[]
            for line in lines:
                if not line:
                    parsed.append('');continue
                current=''
                for char in line:
                    trial=current+char
                    if dr.textbbox((0,0),trial,font=font)[2]>text_w and current:
                        parsed.append(current);current=char
                    else:
                        current=trial
                if current:parsed.append(current)
            line_height=int(font_size*1.32)
            if len(parsed)*line_height<=text_max_h:break
        if not thai_supported:
            st.warning('ไม่พบฟอนต์ไทยในระบบ โปรดอัปโหลดไฟล์ .ttf เพื่อแสดงข้อความภาษาไทยให้ถูกต้อง')
        y=text_top
        for line in parsed:
            stroke=max(1,int(font_size*.035))
            dr.text((text_x,y),line,font=font,fill=accent if color!='ขาว–น้ำเงิน' else foreground,
                    stroke_width=stroke,stroke_fill=bg)
            if use_shadow:
                # เงาจางใต้บรรทัดหลัก
                pass
            y+=line_height
    if sub_text.strip():
        font,_=pick_font(max(14,int(out_h*.055)))
        dr.text((text_x,out_h-margin-int(out_h*.09)),sub_text,font=font,fill=foreground)

    output=BytesIO()
    im.convert('RGB').save(output,format='PNG')
    return output.getvalue(), (out_w,out_h)

if st.button('🖼️ สร้างตัวอย่าง PNG ฟรี',type='primary',use_container_width=True):
    try:
        result_image, result_px=make_free_banner()
        st.session_state['free_banner_png']=result_image
        st.session_state['free_banner_size']=result_px
    except Exception as exc:
        st.error(f'สร้างภาพไม่สำเร็จ: {exc}')
if st.session_state.get('free_banner_png'):
    st.image(st.session_state['free_banner_png'],caption='ตัวอย่างป้าย PNG (ภาพจัดวางอัตโนมัติ)',use_container_width=True)
    st.caption(f"ขนาดภาพ: {st.session_state.get('free_banner_size')}, สำหรับจำลอง ไม่ใช่ไฟล์ AI หรือเวกเตอร์")
    st.download_button('⬇️ ดาวน์โหลดป้าย PNG ฟรี',data=st.session_state['free_banner_png'],
                       file_name='thanasilp_banner_preview.png',mime='image/png',use_container_width=True)
