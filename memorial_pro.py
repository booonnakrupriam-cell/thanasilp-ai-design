"""Thanasilp premium memorial page: choose 13 original designs, type, preview, export."""
from __future__ import annotations
from datetime import date
from hashlib import sha256
from io import BytesIO
import math

import streamlit as st
from PIL import Image, ImageOps
from memorial_pro_art import THEMES, THEME_BY_ID, render_memorial_premium

THAI_DIGITS = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
MONTHS = ("", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
          "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
          "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม")
MAX_PIXELS = 14_000_000
SIZES = {
    "150 × 100 ซม. แนวนอน": (150.0,100.0),
    "200 × 100 ซม. แนวนอน": (200.0,100.0),
    "120 × 80 ซม. แนวนอน": (120.0,80.0),
    "100 × 150 ซม. แนวตั้ง": (100.0,150.0),
    "80 × 120 ซม. แนวตั้ง": (80.0,120.0),
    "กำหนดเอง": None,
}

CSS = """
<style>
  .stApp {background:linear-gradient(160deg,#fcf9f8 0%,#f6f0f6 70%,#fffdfa 100%)}
  .block-container {max-width:1480px;padding-top:1.35rem}
  .mem-hero {border-radius:25px;padding:34px 38px 29px;
    background:radial-gradient(circle at 90% 5%,#765377,transparent 32%),
               linear-gradient(115deg,#19101f 0%,#391f42 62%,#211329 100%);
    border:2px solid #d0a861;box-shadow:0 18px 35px #311a3024;
    color:white;position:relative;overflow:hidden}
  .mem-hero::before {content:"";position:absolute;inset:8px;
    border:1px solid #f2d89c86;border-radius:18px;pointer-events:none}
  .mem-hero .mem-kicker {font-size:13px;letter-spacing:2px;color:#f9dfa0;
    font-weight:750;margin-bottom:13px}
  .mem-hero h1 {font-size:clamp(26px,4vw,50px);line-height:1.25;
    margin:0 0 12px!important;color:#fff1ca;font-weight:900;
    text-shadow:0 2px 0 #5b2e4d}
  .mem-hero p {font-size:17px;color:#f3e8f3;max-width:740px;line-height:1.8;margin:0}
  .mem-hero .mem-count {display:inline-block;color:#331639;
    background:linear-gradient(120deg,#ffedb8,#d6ac5e);
    border-radius:999px;padding:7px 18px;margin-top:18px;font-weight:900}
  .mem-feature {border:1px solid #e8d3b3;border-radius:16px;
    background:linear-gradient(145deg,#fffefb,#fff7e9);padding:14px 16px;
    min-height:102px;box-shadow:0 5px 15px #8c657616;color:#39283c}
  .mem-feature b {display:block;font-size:16px;color:#54285a;margin-bottom:5px}
  .mem-feature span {font-size:13px;line-height:1.5;color:#695a65}
  .mem-section-title {font-size:24px;font-weight:900;color:#3c1c48;
    border-left:6px solid #d1a158;padding-left:14px;margin:18px 0 10px}
  .mem-smallnote {color:#816e7d;font-size:14px;margin:0 0 8px}
  .mem-pick-title {font-size:15px;font-weight:800;color:#442447;margin:0 0 4px}
  .mem-guide {background:#faf1e2;border:1px solid #e0c699;
    padding:13px 18px;border-radius:12px;color:#5c4730;font-size:14px}
  div[data-testid="stVerticalBlockBorderWrapper"] {border-color:#e0c8a6!important;border-radius:15px!important}
  div.stButton>button[kind="primary"],div.stDownloadButton>button[kind="primary"] {
    border:1px solid #e7c681!important;
    background:linear-gradient(110deg,#4e2458,#6a3272)!important;
    color:#fff5df!important;font-weight:800!important;border-radius:12px!important}
  div.stButton>button[kind="primary"]:hover {filter:brightness(1.10)}
  @media(max-width:650px) {
    .mem-hero {padding:23px 19px 19px;border-radius:17px}
    .mem-hero p{font-size:14px}
    .mem-feature {min-height:91px}
  }
</style>
"""

def _thai(text, enabled=True):
    return str(text).translate(THAI_DIGITS) if enabled else str(text)

def _date_th(value, use_thai=True):
    return _thai(f"{value.day} {MONTHS[value.month]} {value.year+543}", use_thai)

def _age_on(born, died):
    return died.year - born.year - ((died.month,died.day)<(born.month,born.day))

def _size_px(width_cm,height_cm,dpi):
    x=max(1,int(round(width_cm/2.54*dpi)))
    y=max(1,int(round(height_cm/2.54*dpi)))
    f=min(1.0,math.sqrt(MAX_PIXELS/max(1,x*y)))
    return max(1,int(x*f)),max(1,int(y*f)),round(dpi*f,2)

def _select_theme(theme_id):
    p=THEME_BY_ID[theme_id]
    st.session_state["mp_theme"]=theme_id
    if p["shape"]=="portrait":
        st.session_state["mp_width"]=100.0
        st.session_state["mp_height"]=150.0
        st.session_state["mp_size_choice"]="100 × 150 ซม. แนวตั้ง"
    else:
        st.session_state["mp_width"]=150.0
        st.session_state["mp_height"]=100.0
        st.session_state["mp_size_choice"]="150 × 100 ซม. แนวนอน"
    st.session_state.pop("mp_export",None)

def _select_size():
    spec=SIZES[st.session_state["mp_size_choice"]]
    if spec is not None:
        st.session_state["mp_width"],st.session_state["mp_height"]=spec

@st.cache_data(show_spinner=False,max_entries=36)
def _thumb(theme_id):
    theme=THEME_BY_ID[theme_id]
    is_port=theme["shape"]=="portrait"
    w,h=(360,540) if is_port else (660,440)
    ex={
        "heading":"ด้วยรักและอาลัย",
        "name":"คุณแม่ตัวอย่าง นามสกุล",
        "born":"ชาตะ  ๕ พฤศจิกายน ๒๔๙๙",
        "died":"มรณะ  ๘ พฤศจิกายน ๒๕๖๙",
        "age":"สิริอายุ  ๗๐ ปี",
        "closing":"ด้วยรักและระลึกถึงเสมอ",
    }
    preview=render_memorial_premium(theme_id,ex,w,h)
    out=BytesIO()
    preview.convert("RGB").save(out,format="JPEG",quality=85)
    return out.getvalue()

def _portrait_file(file):
    if file is None:
        return None
    if file.size>20*1024*1024:
        st.error("รูปใหญ่กว่า 20 MB กรุณาลดขนาดไฟล์")
        return None
    try:
        with Image.open(BytesIO(file.getvalue())) as image:
            if image.width*image.height>30_000_000:
                st.error("ภาพมีพิกเซลมากเกินไป กรุณาลดขนาดภาพก่อน")
                return None
            return ImageOps.exif_transpose(image).convert("RGB")
    except (OSError,ValueError,Image.DecompressionBombError):
        st.error("อ่านรูปภาพไม่ได้ กรุณาใช้ JPG หรือ PNG")
        return None

def render_memorial_pro():
    st.markdown(CSS,unsafe_allow_html=True)
    st.markdown("""
    <section class="mem-hero">
      <div class="mem-kicker">✦ THANASILP AI DESIGN · MEMORIAL PRINT STUDIO ✦</div>
      <h1>พิมพ์ชื่อ ใส่รูป สร้างป้ายไว้อาลัย</h1>
      <p>เลือกแม่แบบที่ชอบแล้วกรอกข้อมูลของคุณเอง เปลี่ยนข้อความบนป้ายได้ทันที
      ด้วยกรอบทอง ดอกไม้สุภาพ และฟอนต์ไทยสำหรับงานอาลัย</p>
      <div class="mem-count">13 ดีไซน์ · แนวนอนและแนวตั้ง</div>
    </section>
    """,unsafe_allow_html=True)
    st.write("")
    features=[
        ("✍️ กรอกชื่อและวันที่","แก้ข้อความจริง ไม่ต้องสร้างภาพใหม่ทุกครั้ง"),
        ("🕊️ เลือกแบบคลิกเดียว","13 แบบในสไตล์ธนศิลป์ ไม่ใช้แบรนด์อื่น"),
        ("🧮 อายุและเลขไทย","คำนวณอายุเต็มปี และแปลงเลขไทยอัตโนมัติ"),
        ("🖨️ พร้อมทำไฟล์พิมพ์","กำหนดขนาดเซนติเมตร ดาวน์โหลด PNG หรือ TIFF"),
    ]
    slots=st.columns(4)
    for col,(head,desc) in zip(slots,features):
        with col:
            st.markdown('<div class="mem-feature"><b>'+head+'</b><span>'+desc+'</span></div>',
                        unsafe_allow_html=True)

    if "mp_theme" not in st.session_state:
        _select_theme("royal_violet")
    st.markdown('<div class="mem-section-title">เลือกแบบป้ายไว้อาลัย</div>',unsafe_allow_html=True)
    st.markdown('<p class="mem-smallnote">คลิก “ใช้แบบนี้” ใต้ภาพตัวอย่าง • 9 แบบแนวนอน / 4 แบบแนวตั้ง • ไม่มีภาพหรือข้อมูลลูกค้าจริงในตัวอย่าง</p>',
                unsafe_allow_html=True)
    group=st.radio("ดูแม่แบบ",["ทั้งหมด 13 แบบ","แนวนอน 9 แบบ","แนวตั้ง 4 แบบ"],
                   horizontal=True,key="mp_group")
    types=(
        THEMES if group.startswith("ทั้งหมด")
        else [p for p in THEMES if p["shape"]==("landscape" if group.startswith("แนวนอน") else "portrait")]
    )
    for start in range(0,len(types),4):
        cols=st.columns(4)
        for j,p in enumerate(types[start:start+4]):
            with cols[j]:
                with st.container(border=True):
                    st.image(_thumb(p["id"]),use_container_width=True)
                    st.markdown('<div class="mem-pick-title">'+p["title"]+'</div>',unsafe_allow_html=True)
                    current=st.session_state["mp_theme"]==p["id"]
                    st.button("✓ กำลังใช้แบบนี้" if current else "เลือกใช้แบบนี้",
                              key="mp_pick_"+p["id"],use_container_width=True,
                              disabled=current,on_click=_select_theme,args=(p["id"],))

    current_theme=THEME_BY_ID[st.session_state["mp_theme"]]
    st.markdown('<div class="mem-section-title">กรอกข้อมูลและดูผลงานทันที</div>',unsafe_allow_html=True)
    st.markdown('<div class="mem-guide">ขั้นตอน: ① เลือกแบบด้านบน ② พิมพ์ข้อมูล ③ ใส่ภาพบุคคล ④ ตรวจพรีวิว ⑤ สร้างและดาวน์โหลดไฟล์</div>',
                unsafe_allow_html=True)
    st.write("")

    left,right=st.columns([.90,1.1],gap="large")
    with left:
        st.markdown("**✍️ ข้อมูลป้ายไว้อาลัย**")
        st.caption("ค่าเริ่มต้นเป็นข้อมูลสมมติสำหรับทดลอง สามารถแก้ทั้งหมดได้")
        heading=st.text_input("ข้อความหัวป้าย",value="ด้วยรักและอาลัย",key="mp_heading")
        name=st.text_input("ชื่อผู้ล่วงลับ",value="คุณแม่ตัวอย่าง นามสกุล",key="mp_name")
        st.markdown("**วันที่ชาตะและวันมรณะ**")
        dt1,dt2=st.columns(2)
        with dt1:
            born=st.date_input("วันชาตะ",value=date(1956,11,5),
                               min_value=date(1850,1,1),max_value=date(2100,12,31),
                               format="DD/MM/YYYY",key="mp_born")
        with dt2:
            died=st.date_input("วันมรณะ",value=date(2026,11,8),
                               min_value=date(1850,1,1),max_value=date(2100,12,31),
                               format="DD/MM/YYYY",key="mp_died")
        invalid=died<born
        if invalid:
            st.error("วันมรณะต้องไม่อยู่ก่อนวันชาตะ")
        calculated=max(0,_age_on(born,died))
        manual_age=st.checkbox("กรอกสิริอายุเองแทนค่าคำนวณ",value=False,key="mp_age_manual")
        if manual_age:
            age=st.number_input("สิริอายุ (ปี)",min_value=0,max_value=130,
                                value=calculated,step=1,key="mp_age_override")
        else:
            age=calculated
            st.caption(f"สิริอายุคำนวณอัตโนมัติ: {age} ปีเต็ม")
        closing=st.text_input("ข้อความด้านล่าง",value="ด้วยรักและระลึกถึงเสมอ",key="mp_closing")
        thai=st.checkbox("ใช้เลขไทยบนป้าย",value=True,key="mp_thai_digits")
        st.markdown("**📷 ใส่ภาพผู้ล่วงลับ**")
        uploaded=st.file_uploader("เลือกภาพ JPG / PNG",type=["jpg","jpeg","png"],key="mp_upload")
        photo=_portrait_file(uploaded)
        st.caption("ระบบวางภาพโดยรักษาสัดส่วน ไม่เปลี่ยนใบหน้า และไม่ได้อัปโหลดรูปไปยังบริการสร้างภาพ AI")
        st.markdown("**📐 ขนาดป้ายและไฟล์พิมพ์**")
        st.selectbox("ขนาดยอดนิยม",list(SIZES),key="mp_size_choice",on_change=_select_size)
        a,b,c=st.columns(3)
        with a:
            width=st.number_input("กว้าง (ซม.)",min_value=20.,max_value=600.,
                                  step=5.,key="mp_width")
        with b:
            height=st.number_input("สูง (ซม.)",min_value=20.,max_value=600.,
                                   step=5.,key="mp_height")
        with c:
            dpi=st.number_input("DPI",min_value=30,max_value=300,
                                value=150,step=10,key="mp_dpi")
        fmt=st.selectbox("ชนิดไฟล์",["PNG","TIFF"],key="mp_fmt")

    texts={
        "heading":heading,
        "name":name,
        "born":"ชาตะ  "+_date_th(born,thai),
        "died":"มรณะ  "+_date_th(died,thai),
        "age":"สิริอายุ  "+_thai(f"{age} ปี",thai),
        "closing":closing,
    }
    is_port=height>width
    preview_w=620 if is_port else 1020
    preview_h=max(200,round(preview_w*height/width))
    f=min(1,math.sqrt(1_600_000/(preview_w*preview_h)))
    preview_w=max(180,int(preview_w*f));preview_h=max(180,int(preview_h*f))
    with right:
        st.markdown("**👁️ พรีวิวแบบที่เลือก — "+current_theme["title"]+"**")
        try:
            preview=render_memorial_premium(current_theme["id"],texts,preview_w,preview_h,photo)
            st.image(preview,use_container_width=True)
        except Exception as exc:
            st.error("สร้างภาพตัวอย่างไม่ได้: "+type(exc).__name__)
            return
        st.caption("ตัวหนังสือเปลี่ยนตามที่กรอกทันที • ตรวจคำสะกด ชื่อ วันเดือนปี และใบหน้าก่อนพิมพ์")
        st.markdown("**✅ รายละเอียดไฟล์พิมพ์**")
        x,y,actual_dpi=_size_px(width,height,dpi)
        st.caption(f"{width:g} × {height:g} ซม. | {x:,} × {y:,} พิกเซล | DPI จริง ~{actual_dpi:g}")
        if actual_dpi<dpi:
            st.warning("ไฟล์พิมพ์ขนาดนี้ใหญ่เกินงบหน่วยความจำ ระบบจะลดพิกเซลและ DPI จริงลง")
        if photo is None:
            st.info("ยังไม่ได้แนบภาพบุคคล — ในป้ายจะแสดงพื้นที่ว่างสำหรับรูป")
        signature=sha256(uploaded.getvalue()).hexdigest() if photo is not None else ""
        job=(current_theme["id"],tuple(sorted(texts.items())),signature,x,y,actual_dpi,fmt)
        if st.button("🖨️ สร้างไฟล์ป้ายพร้อมพิมพ์",type="primary",
                     disabled=invalid,use_container_width=True,key="mp_make"):
            try:
                with st.spinner("กำลังวาดภาพและตัวอักษรไทยสำหรับขนาดพิมพ์จริง..."):
                    final=render_memorial_premium(current_theme["id"],texts,x,y,photo)
                    buf=BytesIO()
                    if fmt=="TIFF":
                        final.convert("RGB").save(buf,format="TIFF",
                            compression="tiff_lzw",dpi=(actual_dpi,actual_dpi))
                    else:
                        final.save(buf,format="PNG",dpi=(actual_dpi,actual_dpi))
                    st.session_state["mp_export"]=(job,buf.getvalue())
            except (OSError,ValueError,MemoryError) as exc:
                st.error("สร้างไฟล์ไม่สำเร็จ: "+type(exc).__name__)
        stored=st.session_state.get("mp_export")
        if stored and stored[0]==job:
            st.download_button("⬇️ ดาวน์โหลดไฟล์ "+fmt,stored[1],
                               file_name="thanasilp_memorial_"+current_theme["id"]+
                                         ("_print.tif" if fmt=="TIFF" else "_print.png"),
                               mime="image/tiff" if fmt=="TIFF" else "image/png",
                               use_container_width=True,type="primary")
        elif stored:
            st.caption("แก้ข้อมูลแล้ว กรุณากดสร้างไฟล์ใหม่ให้ตรงกับพรีวิว")
        st.caption("เป็นโปรแกรมจัดแม่แบบและพิมพ์ข้อความไทยจริง ไม่ใช่ AI ที่สร้างรูปผู้ล่วงลับใหม่ "
                   "และไม่รับประกันความละเอียด 16K ทุกขนาด ควรตรวจรายละเอียดก่อนผลิตงานจริง")
