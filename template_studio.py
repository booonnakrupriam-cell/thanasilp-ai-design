"""Interactive Thai sign templates: click a sample, type text, export a real print image."""
from __future__ import annotations

import glob
import hashlib
import math
from io import BytesIO

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

PRESETS = {
    # รูปแบบอ้างอิงจากงานที่เคยร่วมออกแบบกัน: วาดใหม่ ไม่ใช้รูปบุคคลจริงของลูกค้า
    "history_kathin": dict(
        name="✨ งานเก่า • กฐินฟ้าสดลายทอง", cat="งานวัด / งานบุญ",
        inspiration="ฟ้าสดใส • กรอบทอง • เครื่องกฐิน • วัด • ดอกบัว",
        history="kathin_sky",
        colors=("#038ED9", "#FFFFFF", "#1138A2", "#FFFFFF", "#F4BF35"),
        header="วันที่ ๒๑ พฤศจิกายน ๒๕๖๙", title="กฐินสามัคคี",
        sub="ทอดถวาย ณ วัดตัวอย่าง",
        detail="ตำบลตัวอย่าง อำเภอตัวอย่าง จังหวัดมุกดาหาร",
        footer="ขอเชิญร่วมอนุโมทนาบุญกฐิน", photo=False,
        serif=True, w=300., h=100.),
    "history_scholarship": dict(
        name="✨ งานเก่า • มอบทุนทองหรู", cat="ราชการ / โรงเรียน",
        inspiration="ม่านทอง • หัวเรื่องแดงทอง • แผ่นป้ายวันที่ • ดอกบัว",
        history="scholarship_gold",
        colors=("#FFF0BD", "#F1D9B1", "#9B1730", "#102A76", "#D8A23C"),
        header="ลูกหลานชาวตำบลตัวอย่าง", title="พิธีมอบทุนการศึกษา",
        sub="วันที่ ๙ พฤศจิกายน ๒๕๖๙",
        detail="ณ สถานที่จัดงาน ตำบลตัวอย่าง จังหวัดมุกดาหาร",
        footer="โดยคณะผู้จัดงานและภาคีเครือข่าย", photo=False,
        serif=True, w=300., h=130.),
    "history_memorial": dict(
        name="✨ งานเก่า • อาลัยงาช้างทอง", cat="ป้ายอาลัย / งานศพ",
        inspiration="ฉากงาช้าง • ซุ้มภาพสีทอง • ดอกไม้ขาว • ชื่อเด่น",
        history="memorial_ivory",
        colors=("#FFF8EC", "#E6CFA7", "#613D29", "#FFFFFF", "#D9AE4D"),
        header="ด้วยรักและอาลัย", title="คุณแม่ชื่อ นามสกุล",
        sub="ชาตะ ๑ มกราคม ๒๔๙๐",
        detail="มรณะ ๑ พฤศจิกายน ๒๕๖๙\nสิริอายุ ๗๙ ปี",
        footer="จากครอบครัวและญาติมิตร", photo=True,
        serif=True, w=150., h=100.),
    "history_sports": dict(
        name="✨ งานเก่า • กีฬาสีสดสนามฟ้า", cat="กีฬา / กิจกรรม",
        inspiration="ริบบิ้นธงชาติ • ป้ายหัวเรื่องสีม่วงทอง • สนาม • ถ้วยรางวัล",
        history="sports_festival",
        colors=("#068BD2", "#D6EFFF", "#F9D451", "#FFFFFF", "#F3CB4A"),
        header="การแข่งขันกีฬาภายในโรงเรียน", title="กีฬาสีสามัคคี",
        sub="ร่วมแรง ร่วมใจ สร้างสุขภาพ",
        detail="ณ สนามกีฬาโรงเรียนตัวอย่าง",
        footer="อำเภอตัวอย่าง จังหวัดมุกดาหาร", photo=True,
        serif=False, w=300., h=150.),
    "temple_gold": dict(name="กฐินน้ำเงินทอง", cat="งานวัด / งานบุญ", colors=("#082C76","#0741A5","#FFE39B","#FFFFFF","#F4BA3D"),
                        header="ขอเชิญร่วมงานบุญ", title="ทอดกฐินสามัคคี", sub="ประจำปี ๒๕๖๙", detail="ณ วัดศรีนาราม\nอำเภอนิคมคำสร้อย จังหวัดมุกดาหาร",
                        footer="ร่วมสืบสานงานบุญประเพณีไทย", photo=False, serif=True, w=300.,h=100.),
    "temple_red": dict(name="งานวัดแดงทอง",cat="งานวัด / งานบุญ",colors=("#64142C","#A22C30","#FFE2A2","#FFF6DC","#F3BC42"),
                      header="ขอเชิญพุทธศาสนิกชน",title="งานบุญประเพณี",sub="ร่วมทำบุญและอนุโมทนา",detail="วันอาทิตย์ที่ ๒๑ พฤศจิกายน ๒๕๖๙",footer="ณ วัดและชุมชนของเรา",photo=False,serif=True,w=300.,h=100.),
    "memorial_black": dict(name="อาลัยดำทอง",cat="ป้ายอาลัย / งานศพ",colors=("#121017","#29232D","#F4D99E","#FFF8E8","#C39A4A"),
                         header="ด้วยความอาลัย",title="คุณแม่ตัวอย่าง นามสกุล",sub="ชาตะ ๑ มกราคม ๒๔๙๐",detail="มรณะ ๑ พฤศจิกายน ๒๕๖๙\nสิริอายุ ๗๙ ปี",footer="จากครอบครัวและญาติมิตร",photo=True,serif=True,w=150.,h=100.),
    "memorial_sky": dict(name="อาลัยฟ้าขาว",cat="ป้ายอาลัย / งานศพ",colors=("#DFEFFC","#FFFFFF","#154C86","#27588A","#A4CDEB"),
                       header="ด้วยรักและอาลัย",title="คุณพ่อชื่อ นามสกุล",sub="ชาตะ ๑ มกราคม ๒๔๙๐",detail="มรณะ ๑ พฤศจิกายน ๒๕๖๙\nสิริอายุ ๗๙ ปี",footer="ระลึกถึงเสมอ",photo=True,serif=True,w=150.,h=100.),
    "official_blue": dict(name="ราชการฟ้าขาว",cat="ราชการ / โรงเรียน",colors=("#EAF5FC","#FFFFFF","#123A76","#1B61A1","#D6A744"),
                        header="องค์การบริหารส่วนตำบล",title="ยินดีต้อนรับ",sub="คณะผู้บริหารและแขกผู้มีเกียรติ",detail="ณ ห้องประชุมอเนกประสงค์",footer="ด้วยความยินดียิ่ง",photo=False,serif=False,w=300.,h=100.),
    "school_yellow": dict(name="โรงเรียนเหลืองน้ำเงิน",cat="ราชการ / โรงเรียน",colors=("#073C94","#1972BD","#FFE342","#FFFFFF","#F4C642"),
                         header="โรงเรียนชุมชนบ้านตัวอย่าง",title="กีฬาสีภายใน",sub="สามัคคี มีน้ำใจ รู้แพ้ รู้ชนะ",detail="ประจำปีการศึกษา ๒๕๖๙",footer="ร่วมสร้างสุขภาพที่ดีด้วยกีฬา",photo=False,serif=False,w=300.,h=120.),
    "retail_red": dict(name="ร้านค้าแดงขาว",cat="ร้านค้า / อาหาร",colors=("#B90C26","#F33E36","#FFF2D5","#FFFFFF","#FFD33D"),
                      header="เปิดให้บริการทุกวัน",title="ร้านค้าของเรา",sub="ราคาดี คุณภาพเยี่ยม",detail="จำหน่ายสินค้าและบริการครบวงจร",footer="โทร. ๐๘๐-๐๐๐-๐๐๐๐",photo=False,serif=False,w=300.,h=100.),
    "food_green": dict(name="ร้านอาหารเขียวแดง",cat="ร้านค้า / อาหาร",colors=("#105835","#238B55","#FFE9A0","#FFFFFF","#F9C848"),
                       header="อร่อย สด ใหม่ ทุกวัน",title="ร้านอาหารตามสั่ง",sub="อาหารไทยรสเด็ด",detail="สั่งกลับบ้านได้ • รับจัดเลี้ยง",footer="โทร. ๐๘๐-๐๐๐-๐๐๐๐",photo=False,serif=False,w=300.,h=100.),
    "sports_blue": dict(name="กีฬาน้ำเงินทอง",cat="กีฬา / กิจกรรม",colors=("#12236C","#253EAC","#FFE176","#FFFFFF","#E7B83C"),
                       header="การแข่งขันกีฬาประจำปี",title="ฟุตบอลอาวุโส",sub="ชิงถ้วยรางวัลเกียรติยศ",detail="ณ สนามกีฬากลางจังหวัดมุกดาหาร",footer="ร่วมเชียร์และเป็นกำลังใจให้นักกีฬา",photo=False,serif=False,w=300.,h=120.),
    "ceremony_pink": dict(name="มุทิตาชมพูทอง",cat="กีฬา / กิจกรรม",colors=("#8C2867","#D46D9A","#FFF1CF","#FFFFFF","#EFC469"),
                         header="ด้วยรักและผูกพัน",title="งานมุทิตาจิต",sub="แด่ผู้เกษียณอายุราชการ",detail="ขอบคุณทุกความทุ่มเทและความดีงาม",footer="จากคณะครูและบุคลากร",photo=True,serif=True,w=200.,h=100.),
}
CATEGORIES = ["ทั้งหมด", "งานวัด / งานบุญ", "ป้ายอาลัย / งานศพ", "ราชการ / โรงเรียน", "ร้านค้า / อาหาร", "กีฬา / กิจกรรม"]

def _hexrgb(x):
    return tuple(int(x[j:j+2],16) for j in (1,3,5))

def _get_font(size, serif=False, heavy=True):
    size=max(10,int(size))
    patterns = (
        (["/usr/share/fonts/truetype/noto/NotoSerifThai-Bold.ttf",
          "/usr/share/fonts/truetype/noto/NotoSerifThai-SemiBold.ttf",
          "/usr/share/fonts/truetype/tlwg/Kinnari-Bold.ttf",
          "/usr/share/fonts/opentype/tlwg/Kinnari-Bold.otf"] if serif else
         ["/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
          "/usr/share/fonts/truetype/noto/NotoSansThai-SemiBold.ttf",
          "/usr/share/fonts/opentype/tlwg/Garuda-Bold.otf"])
    )
    patterns += ["/usr/share/fonts/**/*Noto*Thai*Bold*.ttf",
                 "/usr/share/fonts/**/*Sarabun*.ttf",
                 "/usr/share/fonts/**/*Waree*.otf",
                 "/usr/share/fonts/**/*Garuda*.otf",
                 "/usr/share/fonts/**/*Kinnari*.otf"]
    for pattern in patterns:
        for path in glob.glob(pattern,recursive=True):
            try:
                return ImageFont.truetype(path,size)
            except (OSError,ValueError):
                pass
    try:
        return ImageFont.truetype("DejaVuSans.ttf",size)
    except OSError:
        return ImageFont.load_default()

def _paint_text(d, val, x, y, max_w, max_h, font_px, col, outline, serif=False, stroke=0):
    if not val.strip():
        return
    val=val.strip()[:500]
    # Font fitting uses the actual Thai font shape and does not stretch or scale individual glyphs.
    lines=val.splitlines()[:4]
    val="\n".join(lines)
    stroke=min(max(0,stroke),6)
    size=max(10,int(font_px))
    while size >= 10:
        font=_get_font(size,serif)
        gap=max(2,int(size*.12))
        bb=d.multiline_textbbox((0,0),val,font=font,spacing=gap,align="center",stroke_width=stroke)
        if bb[2]-bb[0] <= max_w and bb[3]-bb[1] <= max_h:
            break
        size -= max(1,int(size*.045))
    x0=int(x-(bb[0]+bb[2])/2)
    y0=int(y-(bb[1]+bb[3])/2)
    d.multiline_text((x0,y0),val,font=font,fill=col,spacing=gap,align="center",
                     stroke_width=stroke,stroke_fill=outline)

def _flower(d,cx,cy,r,petal,core):
    # Print-safe floral vector-like ornament, drawn directly as sharp curves.
    for i in range(8):
        angle=math.pi*i/4
        px=cx+math.cos(angle)*r*.6
        py=cy+math.sin(angle)*r*.6
        rw=r*.4
        d.ellipse((px-rw,py-rw,px+rw,py+rw),fill=petal)
    d.ellipse((cx-r*.24,cy-r*.24,cx+r*.24,cy+r*.24),fill=core)

def _gradient(w,h,start,end):
    row=Image.linear_gradient("L").resize((w,h))
    return ImageOps.colorize(row,start,end).convert("RGBA")

def _poster(pre,values,w,h,photo=None,show_photo=None):
    """Render a prior-work-inspired composition or one of the established designs."""
    if pre.get("history"):
        from historical_sign_styles import render_historical
        return render_historical(pre,values,w,h,photo,show_photo)
    from template_art import render_poster
    return render_poster(pre,values,w,h,photo,show_photo)


import math

@st.cache_data(show_spinner=False,max_entries=50)
def _card_image(preset_id, design_version=4):
    p=PRESETS[preset_id]
    vals={fld:p[fld] for fld in ("header","title","sub","detail","footer")}
    # Preview matches each source sign's true aspect ratio, not a forced 720×420.
    w,h=float(p["w"]),float(p["h"])
    if w>=h:
        pw=900
        ph=max(150,round(pw*h/w))
    else:
        ph=850
        pw=max(250,round(ph*w/h))
    im=_poster(p,vals,pw,ph)
    out=BytesIO()
    im.convert("RGB").save(out,format="JPEG",quality=88,subsampling=0)
    return out.getvalue()

def _choose(preset_id):
    p=PRESETS[preset_id]
    st.session_state["sample_sign_selected"]=preset_id
    for fld in ("header","title","sub","detail","footer"):
        st.session_state["sample_sign_"+fld]=p[fld]
    st.session_state["sample_sign_width"]=float(p["w"])
    st.session_state["sample_sign_height"]=float(p["h"])
    st.session_state["sample_sign_with_photo"]=p["photo"]
    st.session_state.pop("sample_sign_export",None)

def _actual_size(w_cm,h_cm,dpi):
    pixels_x=round(w_cm/2.54*dpi)
    pixels_y=round(h_cm/2.54*dpi)
    maxpix=16_000_000
    factor=min(1.0,math.sqrt(maxpix/max(1,pixels_x*pixels_y)))
    return (max(1,int(pixels_x*factor)), max(1,int(pixels_y*factor)), round(dpi*factor,2))

def render_template_studio():
    st.markdown("### ✨ แบบป้ายสวยพร้อมใช้ • เลือกแบบ → แก้ข้อความ → ดาวน์โหลด")
    st.caption(f"มีแบบป้ายทั้งหมด {len(PRESETS)} แบบ รวม 4 แบบอ้างอิงผลงานเก่าของร้าน • คลิกเลือกและแก้ข้อความได้ทันที ไม่ต้องใช้ AI")
    if "sample_sign_selected" not in st.session_state:
        _choose("history_kathin")
    selected=st.session_state["sample_sign_selected"]
    category=st.selectbox("เลือกหมวดแบบป้าย",CATEGORIES,key="sample_sign_category")
    visible=[k for k,v in PRESETS.items() if category=="ทั้งหมด" or v["cat"]==category]
    st.markdown("**✨ 4 แบบแรกอ้างอิงสไตล์งานเก่าที่เคยออกแบบร่วมกัน**")
    st.caption("แบบใหม่วาดจากลักษณะสี ฟอนต์ และการจัดวางของงานเก่า ไม่ได้นำภาพบุคคลหรือไฟล์ลูกค้าเก่ามาเผยแพร่")
    st.markdown("**👇 คลิกเลือกแบบที่ชอบ แล้วเปลี่ยนข้อความของคุณเอง**")
    for i in range(0,len(visible),2):
        cols=st.columns(2)
        for j,key in enumerate(visible[i:i+2]):
            p=PRESETS[key]
            with cols[j]:
                with st.container(border=True):
                    st.image(_card_image(key),use_container_width=True)
                    st.caption(p["name"]+" • "+p["cat"])
                    if p.get("inspiration"):
                        st.caption("อิงงานเก่า: "+p["inspiration"])
                    active=selected==key
                    st.button("✓ แบบที่เลือก" if active else "เลือกแบบนี้",
                              key="sample_sign_pick_"+key,
                              on_click=_choose,args=(key,),
                              disabled=active,use_container_width=True)
    st.divider()
    p=PRESETS[st.session_state["sample_sign_selected"]]
    st.markdown("#### ✏️ กรอกข้อความของคุณ")
    with st.container(border=True):
        st.text_input("หัวข้อบนป้าย",key="sample_sign_header")
        st.text_input("ข้อความใหญ่ / ชื่อหลัก",key="sample_sign_title")
        st.text_input("ข้อความรอง",key="sample_sign_sub")
        st.text_area("รายละเอียด / วัน / สถานที่",height=100,key="sample_sign_detail")
        st.text_input("ข้อความด้านล่าง / เบอร์โทร",key="sample_sign_footer")
        st.checkbox("แสดงช่องใส่รูปบุคคล / รูปประกอบ",key="sample_sign_with_photo")
        photo_up=st.file_uploader("เพิ่มภาพบุคคลหรือภาพประกอบ (ไม่บังคับ)",
                                  type=["png","jpg","jpeg"],
                                  key="sample_sign_photo")
        with st.expander("📐 ขนาดป้ายและการส่งออก",expanded=False):
            a,b,c=st.columns(3)
            with a:
                width_cm=st.number_input("กว้าง (ซม.)",min_value=15.,max_value=600.,
                                         step=5.,key="sample_sign_width")
            with b:
                height_cm=st.number_input("สูง (ซม.)",min_value=15.,max_value=600.,
                                          step=5.,key="sample_sign_height")
            with c:
                dpi=st.number_input("DPI เป้าหมาย",min_value=30,max_value=300,
                                    value=150,step=10,key="sample_sign_dpi")
            fmt=st.selectbox("ชนิดไฟล์",["PNG","TIFF"],key="sample_sign_fmt")
    # Do not silently stretch faces or photos. All output is rendered from editable text.
    photo=None
    if photo_up is not None:
        if photo_up.size>20*1024*1024:
            st.warning("รูปประกอบใหญ่เกิน 20 MB กรุณาใช้ไฟล์ที่เล็กลง")
        else:
            try:
                with Image.open(BytesIO(photo_up.getvalue())) as im:
                    if im.width*im.height<28_000_000:
                        photo=ImageOps.exif_transpose(im).convert("RGB")
                    else:
                        st.warning("รูปใหญ่เกิน 28 ล้านพิกเซล กรุณาย่อก่อน")
            except (OSError,ValueError):
                st.error("เปิดรูปไม่ได้ กรุณาใช้ PNG หรือ JPG")
    values={f:st.session_state.get("sample_sign_"+f,"") for f in ("header","title","sub","detail","footer")}
    with_photo=st.session_state["sample_sign_with_photo"]
    aspect=max(.25,min(4.0,width_cm/height_cm))
    preview_w=int(min(1150,max(430,760*max(1,aspect))))
    preview_h=max(210,round(preview_w/aspect))
    if preview_w*preview_h>1_400_000:
        v=math.sqrt(1_400_000/(preview_w*preview_h))
        preview_w=max(100,round(preview_w*v))
        preview_h=max(100,round(preview_h*v))
    preview=_poster(p,values,preview_w,preview_h,photo,with_photo)
    st.markdown("#### 👀 พรีวิวข้อความที่กรอก (เปลี่ยนทันที)")
    st.image(preview,use_container_width=True)
    st.caption("พรีวิวเป็นภาพย่อ ไฟล์สำหรับพิมพ์สร้างใหม่ตาม DPI ที่ตั้ง • ตรวจชื่อ/สระ/วรรณยุกต์ก่อนพิมพ์")
    pixels_x,pixels_y,real_dpi=_actual_size(width_cm,height_cm,dpi)
    st.caption(f"ไฟล์จริง: {pixels_x:,} × {pixels_y:,} พิกเซล • DPI ใช้ได้จริงประมาณ {real_dpi:g}")
    if real_dpi<dpi:
        st.warning("ขนาดงานเกินข้อจำกัดเว็บ ระบบปรับ DPI จริงลงเพื่อป้องกันค้าง")
    photo_signature=(hashlib.sha256(photo_up.getvalue()).hexdigest() if photo is not None else "")
    settings=(p["name"],tuple(values.items()),photo_signature,with_photo,
              pixels_x,pixels_y,real_dpi,fmt)
    if st.button("🖨️ สร้างไฟล์จากแบบที่เลือก",type="primary",
                 key="sample_sign_generate",use_container_width=True):
        with st.spinner("กำลังวาดตัวอักษรไทยและสร้างไฟล์พร้อมพิมพ์..."):
            final=_poster(p,values,pixels_x,pixels_y,photo,with_photo)
            out=BytesIO()
            if fmt=="TIFF":
                final.convert("RGB").save(out,format="TIFF",compression="tiff_lzw",
                                          dpi=(real_dpi,real_dpi))
            else:
                final.save(out,format="PNG",dpi=(real_dpi,real_dpi))
            st.session_state["sample_sign_export"]=(settings,out.getvalue())
    state=st.session_state.get("sample_sign_export")
    if state and state[0]==settings:
        st.download_button("⬇️ ดาวน์โหลดป้าย "+fmt,state[1],
                           file_name="thanasilp_template."+("tif" if fmt=="TIFF" else "png"),
                           mime="image/tiff" if fmt=="TIFF" else "image/png",
                           use_container_width=True)
    elif state:
        st.caption("มีการเปลี่ยนข้อความหรือขนาด กรุณากดสร้างไฟล์ใหม่")
    st.caption("แบบสำเร็จรูปนี้สร้างกราฟิกและวาดข้อความจริงบนเว็บ ไม่ใช่การแก้ข้อความที่ฝังอยู่ในภาพ JPG/PNG เดิม")
