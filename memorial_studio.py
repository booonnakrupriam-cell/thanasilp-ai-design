"""One focused memorial-sign prototype for Thanasilp AI Design.

Premium heaven-sky / gold memorial print sign. The user's text is typeset by
Pillow and the customer's photograph stays private in the current session.
No previous customer's photos or memorial data are built into this template.
"""
from __future__ import annotations

from io import BytesIO
import glob
import hashlib
import math
from functools import lru_cache

import streamlit as st
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

MAX_OUTPUT_PIXELS = 14_000_000
THAI_NUMERALS = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")


@lru_cache(maxsize=220)
def _thai_font(size: int, formal: bool = False):
    size = max(12, int(size))
    preferred = (
        [
            "/usr/share/fonts/truetype/noto/NotoSerifThai-Bold.ttf",
            "/usr/share/fonts/opentype/tlwg/Kinnari-Bold.otf",
            "/usr/share/fonts/truetype/tlwg/Kinnari-Bold.ttf",
        ] if formal else [
            "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
            "/usr/share/fonts/opentype/tlwg/Garuda-Bold.otf",
            "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf",
        ]
    )
    matches = (
        glob.glob("/usr/share/fonts/**/*Thai*Bold*.ttf", recursive=True)
        + glob.glob("/usr/share/fonts/**/*Kinnari*Bold*.otf", recursive=True)
        + glob.glob("/usr/share/fonts/**/*Garuda*Bold*.otf", recursive=True)
    )
    for name in preferred + matches:
        try:
            if hasattr(ImageFont, "Layout") and hasattr(ImageFont.Layout, "RAQM"):
                return ImageFont.truetype(name, size, layout_engine=ImageFont.Layout.RAQM)
            return ImageFont.truetype(name, size)
        except (OSError, ValueError):
            pass
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _fit_text(draw, value, cx, cy, max_width, max_height, start_px, color,
              outline=None, formal=False, weight=1, shadow=True):
    """Center and fit real Thai glyphs without anisotropic resizing."""
    value = str(value or "").strip()[:240]
    if not value:
        return
    value = "\n".join(value.splitlines()[:3])
    size = max(12, round(start_px))
    stroke = max(0, int(weight))
    while size > 12:
        font = _thai_font(size, formal)
        gap = max(1, int(size * .12))
        bounds = draw.multiline_textbbox(
            (0, 0), value, font=font, spacing=gap, align="center",
            stroke_width=stroke
        )
        if bounds[2] - bounds[0] <= max_width and bounds[3] - bounds[1] <= max_height:
            break
        size = max(12, int(size * .94))
    xx = round(cx - (bounds[0] + bounds[2]) / 2)
    yy = round(cy - (bounds[1] + bounds[3]) / 2)
    if shadow:
        shift = max(1, size // 24)
        draw.multiline_text(
            (xx + shift, yy + shift), value, font=font, spacing=gap,
            align="center", fill="#667B88", stroke_width=stroke + 1,
            stroke_fill="#667B88"
        )
    draw.multiline_text(
        (xx, yy), value, font=font, spacing=gap, align="center",
        fill=color, stroke_width=stroke, stroke_fill=outline or color
    )


def _sky_canvas(w, h):
    # Gradient and cloud effects are rendered on a reduced backing image,
    # then scaled to avoid allocating numerous full-print-size layers.
    small_w = min(w, 1100)
    small_h = max(150, round(small_w * h / w))
    small_h = min(small_h, 1100)
    base = Image.new("RGB", (small_w, small_h), "#E8F4FF")
    d = ImageDraw.Draw(base)
    for yy in range(small_h):
        t = yy / max(1, small_h - 1)
        top = (35, 85, 149)
        mid = (135, 195, 235)
        bottom = (247, 251, 255)
        if t <= .46:
            tt = t / .46
            rgb = tuple(round(top[i] * (1 - tt) + mid[i] * tt) for i in range(3))
        else:
            tt = (t - .46) / .54
            rgb = tuple(round(mid[i] * (1 - tt) + bottom[i] * tt) for i in range(3))
        d.line((0, yy, small_w, yy), fill=rgb)
    # Diffuse light behind the centre, restrained and print-friendly.
    light = Image.new("RGBA", (small_w, small_h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    cx, cy = int(small_w * .49), int(small_h * .48)
    for radius, opacity in [
        (.48, 13), (.39, 19), (.30, 24), (.22, 28), (.13, 35),
    ]:
        rx = int(small_w * radius)
        ry = int(small_h * radius)
        ld.ellipse((cx - rx, cy - ry, cx + rx, cy + ry),
                   fill=(255, 252, 236, opacity))
    # Soft white cloud banks near lower corners; no hard bars or cuts.
    cloud = Image.new("RGBA", (small_w, small_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud)
    for x, y, rx, ry, alpha in [
        (.10, .79, .18, .11, 155), (.29, .87, .22, .13, 150),
        (.70, .85, .21, .12, 145), (.92, .75, .17, .10, 150),
        (.40, .92, .30, .13, 175), (.63, .95, .25, .14, 165),
    ]:
        cd.ellipse(((x-rx)*small_w,(y-ry)*small_h,
                    (x+rx)*small_w,(y+ry)*small_h),
                   fill=(255, 255, 255, alpha))
    cloud = cloud.filter(ImageFilter.GaussianBlur(max(8, small_h//36)))
    return Image.alpha_composite(Image.alpha_composite(base.convert("RGBA"), light), cloud).resize(
        (w, h), Image.Resampling.BICUBIC
    )


def _gold_ornaments(d, w, h):
    u = min(w, h)
    thick = max(2, int(u * .006))
    border = int(u * .026)
    d.rounded_rectangle(
        (border, border, w-border, h-border), radius=int(u*.045),
        outline="#D29F39", width=thick
    )
    d.rounded_rectangle(
        (border+thick*2, border+thick*2, w-border-thick*2, h-border-thick*2),
        radius=int(u*.037), outline="#FFF9D2", width=max(1, thick//3)
    )
    # Curved gilded flourishes; keep main text and portrait uncluttered.
    for flip_x in (False, True):
        for flip_y in (False, True):
            points = []
            for step in range(80):
                t = step / 79
                x = w * (.04 + .15*t)
                y = h * (.048 + .09*math.sin(math.pi*t/2)**2)
                if flip_x: x = w-x
                if flip_y: y = h-y
                points.append((x,y))
            d.line(points, fill="#DDAE50", width=max(2,thick//2), joint="curve")
            x = points[-1][0]
            y = points[-1][1]
            rr = u*.011
            d.ellipse((x-rr,y-rr,x+rr,y+rr), fill="#EAC87D")
    # Tiny rays and gold accents, well away from key text.
    for xx, yy in [(.18,.16),(.83,.16),(.17,.78),(.88,.77)]:
        x=xx*w;y=yy*h
        r=u*.017
        d.line((x-r,y,x+r,y),fill="#FFF4C8",width=max(2,thick//2))
        d.line((x,y-r,x,y+r),fill="#F6D078",width=max(2,thick//2))


def _lily(d, cx, cy, size):
    # Layered white, ivory and green flower arrangement derived from
    # familiar memorial-sign visual language, without copying client art.
    for j in range(7):
        ang = j * 2*math.pi/7 - math.pi/2
        ox = cx + math.cos(ang)*size*.85
        oy = cy + math.sin(ang)*size*.63
        d.ellipse((ox-size*.35,oy-size*.19,
                   ox+size*.35,oy+size*.19),
                  fill="#2B8456",outline="#1E6F53",
                  width=max(1,int(size*.035)))
    for j in range(6):
        ang = j*2*math.pi/6
        px = cx + size*.46*math.cos(ang)
        py = cy + size*.45*math.sin(ang)
        d.ellipse((px-size*.33,py-size*.32,
                   px+size*.33,py+size*.32),
                  fill="#FFFDF2",outline="#E7DEBF",
                  width=max(1,int(size*.04)))
    d.ellipse((cx-size*.17,cy-size*.17,
               cx+size*.17,cy+size*.17),
              fill="#E6B757",outline="#FFE7A6",
              width=max(1,int(size*.034)))


def _portrait(can, photo, cx, cy, width, height):
    """One non-retouched photograph. Whole source is fitted, not stretched."""
    w,h=can.size
    u=min(w,h)
    pw,ph=max(5,int(width)),max(5,int(height))
    x1=int(cx-pw/2);y1=int(cy-ph/2)
    x2=x1+pw;y2=y1+ph
    d=ImageDraw.Draw(can)
    # Double gold and cream oval surround.
    d.ellipse((x1-u*.022,y1-u*.015,
               x2+u*.022,y2+u*.015),
              fill="#BC8D33",outline="#FFF8E2",width=max(2,int(u*.010)))
    d.ellipse((x1,y1,x2,y2),fill="#FBF5E8",
              outline="#EAC16B",width=max(2,int(u*.006)))
    if photo is not None:
        # Preserve aspect ratio and face. Centre a full image in the oval,
        # rather than stretching the face to match dimensions.
        fitted = ImageOps.contain(photo.convert("RGB"), (pw,ph),
                                  method=Image.Resampling.LANCZOS)
        base = Image.new("RGB", (pw,ph), "#E6EEF1")
        base.paste(fitted, ((pw-fitted.width)//2,(ph-fitted.height)//2))
        mask = Image.new("L", (pw,ph), 0)
        ImageDraw.Draw(mask).ellipse((0,0,pw-1,ph-1),fill=255)
        can.paste(base,(x1,y1),mask)
    else:
        # Reserved portrait placeholder: no fictional customer photo.
        hx = (x1+x2)/2
        hy = y1+ph*.43
        r=min(pw,ph)*.17
        d.ellipse((hx-r,hy-r,hx+r,hy+r),fill="#AFC4D1")
        d.ellipse((hx-pw*.28,hy+ph*.18,
                   hx+pw*.28,hy+ph*.58),fill="#AFC4D1")
    d=ImageDraw.Draw(can)
    d.ellipse((x1,y1,x2,y2),outline="#FCDF9D",
              width=max(2,int(u*.005)))


def _safe_text(val, thai_digits):
    value = str(val or "").strip()
    return value.translate(THAI_NUMERALS) if thai_digits else value


def render_memorial(values, width, height, photograph=None):
    """Full-resolution layout, landscape or portrait, with live editable fields."""
    w,h=int(width),int(height)
    if min(w,h)<180 or w*h>MAX_OUTPUT_PIXELS:
        raise ValueError("ขนาดพิกเซลเกินขอบเขตที่รองรับ")
    landscape = w>=h
    u=min(w,h)
    img = _sky_canvas(w,h)
    d = ImageDraw.Draw(img)
    _gold_ornaments(d,w,h)
    if landscape:
        # Subtle ivory name panel: no heavy rectangular box.
        d.rounded_rectangle((w*.445,h*.255,w*.915,h*.806),
                            radius=u*.035,fill="#F9FCF7",
                            outline="#E0C27D",width=max(2,int(u*.004)))
        d.rounded_rectangle((w*.456,h*.267,w*.903,h*.791),
                            radius=u*.029,outline="#FFF1C8",
                            width=max(1,int(u*.003)))
        _portrait(img,photograph,w*.253,h*.495,w*.286,h*.555)
        d=ImageDraw.Draw(img)
        _lily(d,w*.093,h*.817,u*.106)
        _lily(d,w*.388,h*.825,u*.083)
        _lily(d,w*.930,h*.827,u*.080)
        _fit_text(d,values.get("heading"),w*.5,h*.125,w*.73,h*.115,
                  u*.096,"#FFF8EA","#31527F",formal=True,weight=max(1,int(u*.004)))
        _fit_text(d,values.get("name"),w*.68,h*.365,w*.43,h*.145,
                  u*.118,"#164275","#FFF5D7",formal=True,weight=max(1,int(u*.004)))
        d.line((w*.49,h*.472,w*.866,h*.472),
               fill="#C4A057",width=max(1,int(u*.003)))
        _fit_text(d,"ชาตะ  "+values.get("born",""),w*.68,h*.544,
                  w*.405,h*.080,u*.063,"#344A63",formal=False,shadow=False)
        _fit_text(d,"มรณะ  "+values.get("died",""),w*.68,h*.636,
                  w*.405,h*.080,u*.063,"#344A63",formal=False,shadow=False)
        _fit_text(d,"สิริอายุ  "+values.get("age",""),w*.68,h*.726,
                  w*.39,h*.078,u*.069,"#9A722B","#FFFFFF",formal=True,shadow=False)
        # Bottom satin gold/navy ribbon.
        d.rounded_rectangle((w*.22,h*.873,w*.83,h*.954),
                            radius=u*.020,fill="#17477C",outline="#D8AE55",
                            width=max(2,int(u*.005)))
        _fit_text(d,values.get("closing"),w*.52,h*.916,w*.56,h*.055,
                  u*.052,"#FFF5DF","#173B6A",formal=True,shadow=False)
    else:
        d.rounded_rectangle((w*.087,h*.638,w*.913,h*.890),
                            radius=u*.040,fill="#FAFBF5",
                            outline="#DAB661",width=max(2,int(u*.005)))
        _portrait(img,photograph,w*.5,h*.405,w*.55,h*.405)
        d=ImageDraw.Draw(img)
        _lily(d,w*.113,h*.665,u*.110)
        _lily(d,w*.895,h*.665,u*.108)
        _lily(d,w*.126,h*.897,u*.075)
        _lily(d,w*.874,h*.897,u*.075)
        _fit_text(d,values.get("heading"),w*.5,h*.118,
                  w*.82,h*.090,u*.095,"#FFF8EA","#31527F",
                  formal=True,weight=max(1,int(u*.003)))
        _fit_text(d,values.get("name"),w*.5,h*.699,w*.76,h*.092,
                  u*.095,"#184578","#FFF4DD",formal=True,weight=max(1,int(u*.003)))
        d.line((w*.20,h*.755,w*.80,h*.755),fill="#D3AD65",
               width=max(1,int(u*.003)))
        _fit_text(d,"ชาตะ  "+values.get("born",""),w*.5,h*.789,w*.73,h*.043,
                  u*.051,"#334966",shadow=False)
        _fit_text(d,"มรณะ  "+values.get("died",""),w*.5,h*.832,w*.73,h*.043,
                  u*.051,"#334966",shadow=False)
        _fit_text(d,"สิริอายุ  "+values.get("age",""),w*.5,h*.872,
                  w*.70,h*.040,u*.054,"#9A722B",formal=True,shadow=False)
        d.rounded_rectangle((w*.155,h*.933,w*.845,h*.977),
                            radius=u*.018,fill="#164577",
                            outline="#D6AF62",width=max(2,int(u*.005)))
        _fit_text(d,values.get("closing"),w*.5,h*.953,w*.64,h*.029,
                  u*.041,"#FFF2D5",formal=True,shadow=False)
    return img


def _output_size(width_cm, height_cm, dpi):
    px = max(1,round(width_cm / 2.54 * dpi))
    py = max(1,round(height_cm / 2.54 * dpi))
    rate = min(1.0, math.sqrt(MAX_OUTPUT_PIXELS / max(1,px*py)))
    return max(1,int(px*rate)), max(1,int(py*rate)), round(dpi*rate,2)


def _size_choice():
    selected = st.session_state["mem_size_select"]
    sizes = {
        "150 × 100 ซม. แนวนอน": (150.0,100.0),
        "100 × 150 ซม. แนวตั้ง": (100.0,150.0),
        "200 × 100 ซม. แนวนอน": (200.0,100.0),
    }
    if selected in sizes:
        st.session_state["mem_width"],st.session_state["mem_height"] = sizes[selected]


def render_memorial_studio():
    st.markdown("### 🕊️ ต้นแบบป้ายไว้อาลัย • ฟ้าสวรรค์ ขาวทอง")
    st.caption(
        "โฟกัสแบบอาลัยจากแนวงานเก่าของร้านก่อน • เมฆนุ่ม แสงหลัง "
        "กรอบทองสุภาพ ดอกไม้ขาว และชื่อเด่น • พอใจแบบนี้แล้วค่อยเพิ่มแบบอื่น"
    )
    st.info("ต้นแบบนี้เป็นแบบใหม่สำหรับทดลอง ไม่ใส่รูปผู้ล่วงลับของลูกค้าเก่า "
            "ให้แนบรูปจากเครื่องของคุณเองเพื่อใช้งานจริง")
    st.markdown("#### 1. ใส่รูปผู้ล่วงลับ")
    upload = st.file_uploader(
        "อัปโหลดรูปบุคคล JPG / PNG (ไม่บังคับสำหรับดูแบบ)",
        type=["jpg","jpeg","png"], key="mem_photo_v1"
    )
    photo=None
    if upload is not None:
        if upload.size > 20*1024*1024:
            st.error("รูปใหญ่เกิน 20 MB กรุณาลดขนาดไฟล์ก่อน")
        else:
            try:
                with Image.open(BytesIO(upload.getvalue())) as original:
                    if original.width*original.height > 30_000_000:
                        st.error("รูปใหญ่เกิน 30 ล้านพิกเซล กรุณาลดขนาดก่อน")
                    else:
                        photo=ImageOps.exif_transpose(original).convert("RGB")
            except (OSError,ValueError,Image.DecompressionBombError):
                st.error("ไม่สามารถอ่านภาพนี้ได้ กรุณาใช้ JPG หรือ PNG")
    st.caption("ภาพบุคคลจะถูกวางโดยไม่เปลี่ยนใบหน้า ไม่รีทัชหรือสร้างหน้าขึ้นใหม่")

    st.markdown("#### 2. พิมพ์ข้อมูลบนป้าย")
    heading=st.text_input("หัวป้าย",value="ด้วยรักและอาลัย",key="mem_head_v1")
    name=st.text_input("ชื่อผู้ล่วงลับ (ตัวใหญ่)",value="คุณแม่ชื่อ นามสกุล",key="mem_name_v1")
    a,b=st.columns(2)
    with a:
        born=st.text_input("ชาตะ",value="๕ พฤศจิกายน ๒๔๙๙",key="mem_born_v1")
    with b:
        died=st.text_input("มรณะ",value="๘ พฤศจิกายน ๒๕๖๙",key="mem_died_v1")
    age=st.text_input("สิริอายุ (พิมพ์ตามที่ตรวจสอบ)",value="๗๐ ปี",key="mem_age_v1")
    closing=st.text_input("ข้อความด้านล่าง",value="จากครอบครัวและญาติมิตร",key="mem_close_v1")
    use_thai_digits=st.checkbox("แปลงตัวเลขเป็นเลขไทยอัตโนมัติ",value=True,key="mem_digits_v1")
    texts={
        "heading":_safe_text(heading,use_thai_digits),
        "name":_safe_text(name,use_thai_digits),
        "born":_safe_text(born,use_thai_digits),
        "died":_safe_text(died,use_thai_digits),
        "age":_safe_text(age,use_thai_digits),
        "closing":_safe_text(closing,use_thai_digits),
    }
    st.markdown("#### 3. ขนาดงาน")
    st.selectbox(
        "เลือกขนาดยอดนิยม",[
            "150 × 100 ซม. แนวนอน",
            "100 × 150 ซม. แนวตั้ง",
            "200 × 100 ซม. แนวนอน",
            "กำหนดขนาดเอง",
        ],key="mem_size_select",on_change=_size_choice
    )
    if "mem_width" not in st.session_state:
        st.session_state["mem_width"]=150.0
    if "mem_height" not in st.session_state:
        st.session_state["mem_height"]=100.0
    c1,c2,c3=st.columns(3)
    with c1:
        width=st.number_input("กว้าง (ซม.)",min_value=20.0,max_value=600.0,
                              step=5.0,key="mem_width")
    with c2:
        height=st.number_input("สูง (ซม.)",min_value=20.0,max_value=600.0,
                               step=5.0,key="mem_height")
    with c3:
        dpi=st.number_input("DPI ที่ต้องการ",min_value=30,max_value=300,
                            value=150,step=10,key="mem_dpi_v1")
    fmt=st.selectbox("รูปแบบไฟล์",["PNG","TIFF"],key="mem_format_v1")
    # Preview keeps the real aspect ratio and is rendered anew on each edit.
    ratio=width/height
    pw=1050 if ratio>=1 else 650
    ph=max(240,int(pw/ratio))
    limit=1_600_000
    factor=min(1.0,math.sqrt(limit/max(1,pw*ph)))
    pw=max(180,int(pw*factor));ph=max(180,int(ph*factor))
    try:
        preview=render_memorial(texts,pw,ph,photo)
        st.markdown("#### 👀 พรีวิวป้ายไว้อาลัย")
        st.image(preview,use_container_width=True)
    except Exception as exc:
        st.error("พรีวิวทำงานไม่ได้: "+type(exc).__name__)
        return
    st.caption("ชื่อ สระ และวรรณยุกต์ต้องตรวจด้วยตาก่อนพิมพ์ โดยเฉพาะชื่อบุคคลและวันที่")
    x,y,real_dpi=_output_size(width,height,dpi)
    st.caption(f"ขนาดไฟล์ส่งออก {x:,} × {y:,} พิกเซล • DPI จริงประมาณ {real_dpi:g}")
    if real_dpi < dpi:
        st.warning("ขนาดป้ายเกินกำลังประมวลผลของเว็บ ระบบลด DPI จริงเพื่อป้องกันเว็บค้าง")
    sig=hashlib.sha256(upload.getvalue()).hexdigest() if photo is not None else ""
    settings=(tuple(sorted(texts.items())),sig,x,y,real_dpi,fmt)
    if photo is None:
        st.warning("ยังไม่ได้แนบรูปผู้ล่วงลับ: ตัวอย่างแสดงเพียงช่องแทนรูป ควรแนบรูปจริงก่อนสร้างไฟล์พิมพ์")
    if st.button("🖨️ สร้างไฟล์ป้ายอาลัย",type="primary",
                 use_container_width=True,key="mem_generate_v1"):
        try:
            with st.spinner("กำลังจัดข้อความและสร้างภาพขนาดจริง..."):
                artwork=render_memorial(texts,x,y,photo)
                buffer=BytesIO()
                if fmt=="TIFF":
                    artwork.convert("RGB").save(buffer,format="TIFF",
                       compression="tiff_lzw",dpi=(real_dpi,real_dpi))
                else:
                    artwork.save(buffer,format="PNG",dpi=(real_dpi,real_dpi))
                st.session_state["mem_result_v1"]=(settings,buffer.getvalue())
        except (MemoryError,OSError,ValueError) as exc:
            st.error("สร้างไฟล์ไม่สำเร็จ: "+type(exc).__name__)
    previous=st.session_state.get("mem_result_v1")
    if previous and previous[0]==settings:
        st.download_button(
            "⬇️ ดาวน์โหลดป้ายไว้อาลัย "+fmt,
            previous[1],
            file_name="thanasilp_memorial." + ("tif" if fmt=="TIFF" else "png"),
            mime="image/tiff" if fmt=="TIFF" else "image/png",
            use_container_width=True
        )
    elif previous:
        st.caption("มีการเปลี่ยนข้อมูล กรุณากดสร้างไฟล์ใหม่เพื่อให้ตรงกับพรีวิวล่าสุด")
    st.caption("นี่คือแม่แบบแก้ข้อความและใส่รูปจริงบนเว็บไซต์ ไม่ใช่ AI สร้างฉากภาพถ่ายใหม่หรือแก้ข้อความในไฟล์ JPG เดิม")
