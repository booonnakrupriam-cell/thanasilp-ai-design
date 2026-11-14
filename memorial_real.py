"""Photorealistic memorial studio built around background artwork supplied in a ZIP.

Unlike flat Pillow drawings, this loads actual artwork with rendered gold
filigree and realistic flowers, and overlays editable Thai text and the
user's own portrait in a precisely clipped oval. The background ZIP is
required; this app intentionally does NOT claim that basic vector placeholders
are photo-real memorial posters.
"""
from __future__ import annotations

from datetime import date
from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import Path
from zipfile import ZipFile, BadZipFile

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from memorial_pro import _age_on, _date_th, _size_px, THAI_DIGITS, SIZES, CSS
from memorial_pro_art import THEMES, THEME_BY_ID, _font

MAX_ARCHIVE_BYTES = 22 * 1024 * 1024
MAX_FILE_PIXELS = 9_000_000
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
# Exact names are allowlisted; paths/unknown filenames in a ZIP are never trusted.
THEME_IDS = tuple(p["id"] for p in THEMES)

CSS_REAL = """
<style>
 .real-hero {border-radius:19px;padding:25px 31px;color:#fff6df;
   background:linear-gradient(110deg,#24152b,#562b61 67%,#1e1723);
   border:2px solid #d6af60;box-shadow:0 8px 30px #3d243320;}
 .real-hero h2 {font-size:clamp(24px,3.1vw,42px);color:#ffedbd;margin:8px 0;}
 .real-hero p {max-width:850px;color:#f4e9f7;font-size:15px;line-height:1.7;margin:0;}
 .real-title {border-left:5px solid #c59c52;padding-left:12px;
   font-size:21px;font-weight:800;color:#3d2244;margin:16px 0 11px;}
 .real-note {border:1px solid #dfbd81;padding:13px;border-radius:10px;
    background:#fff9eb;color:#513c26;font-size:14px}
</style>
"""

def _open_pack(pack):
    """Return (metadata, thumbnails). Never extract ZIP paths on disk."""
    if len(pack) > MAX_ARCHIVE_BYTES:
        raise ValueError("ZIP ขนาดเกิน 22 MB")
    try:
        with ZipFile(BytesIO(pack)) as archive:
            entries = archive.namelist()
            if len(entries) > 45:
                raise ValueError("จำนวนไฟล์ ZIP มากเกินไป")
            if not any(name == "manifest.json" for name in entries):
                raise ValueError("ZIP ไม่มี manifest.json")
            if sum(z.file_size for z in archive.infolist()) > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("ZIP มีข้อมูลมากเกินที่รองรับ")
            metadata = json.loads(archive.read("manifest.json").decode("utf-8"))
            if metadata.get("pack_version") != 2:
                raise ValueError("กรุณาใช้ชุดแม่แบบธนศิลป์รุ่น 2")
            listing = metadata.get("templates", {})
            if any(key not in listing for key in THEME_IDS):
                raise ValueError("ชุดภาพมีไม่ครบทั้ง 13 แบบ")
            cards = {}
            for key in THEME_IDS:
                record = listing[key]
                filename = record.get("file")
                if filename != key + ".png" or filename not in entries:
                    raise ValueError("ชื่อไฟล์ภาพแม่แบบไม่ตรงตามรายการ")
                info = archive.getinfo(filename)
                if info.file_size > 12 * 1024 * 1024:
                    raise ValueError("ภาพแม่แบบใหญ่เกินที่รองรับ")
                with Image.open(BytesIO(archive.read(filename))) as im:
                    if im.width * im.height > MAX_FILE_PIXELS:
                        raise ValueError("พิกเซลภาพแม่แบบใหญ่เกินไป")
                    preview_name = "preview_" + key + ".jpg"
                    if preview_name in entries:
                        thumb_bytes=archive.read(preview_name)
                        # Validate thumbnails before displaying submitted ZIP bytes.
                        with Image.open(BytesIO(thumb_bytes)) as thumb_source:
                            if thumb_source.width*thumb_source.height>1_200_000:
                                raise ValueError("ภาพตัวอย่างมีขนาดใหญ่เกินไป")
                            thumb_source.verify()
                        cards[key]=thumb_bytes
                    else:
                        thumb = im.copy().convert("RGB")
                        thumb.thumbnail((680, 450), Image.Resampling.LANCZOS)
                        out = BytesIO()
                        thumb.save(out, format="JPEG", quality=86)
                        cards[key] = out.getvalue()
            return metadata, cards
    except (BadZipFile, KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
        raise ValueError("เปิดไฟล์ ZIP ไม่สำเร็จ กรุณาใช้ไฟล์แม่แบบธนศิลป์ที่ดาวน์โหลดไว้") from exc

def _pack_from_repository():
    """Prefer an installed permanent template pack, if present in the repository.

    A user can later copy the 13 PNG files plus manifest.json into
    assets/memorial_real/; no app-code changes are needed after that.
    """
    folder=Path(__file__).resolve().parent/"assets"/"memorial_real"
    if not (folder/"manifest.json").is_file():
        return None
    files=["manifest.json"]+[key+".png" for key in THEME_IDS]
    if not all((folder/name).is_file() for name in files):
        return None
    data=BytesIO()
    from zipfile import ZIP_STORED
    with ZipFile(data,"w",compression=ZIP_STORED) as z:
        for name in files:
            p=folder/name
            if p.stat().st_size>12*1024*1024:
                return None
            z.write(p,arcname=name)
    return data.getvalue()


@st.cache_data(show_spinner=False,max_entries=4)
def _cached_pack(pack):
    return _open_pack(pack)

def _get_image(pack, key):
    with ZipFile(BytesIO(pack)) as archive:
        with Image.open(BytesIO(archive.read(key + ".png"))) as img:
            return img.copy().convert("RGBA")

def _text_fit(d, value, center, maxbox, size, fill, stroke_color, formal=False):
    val = str(value or "").strip()[:300]
    if not val:
        return
    val = "\n".join(val.splitlines()[:3])
    size=max(12,int(size))
    maxw,maxh=maxbox
    border=max(0,round(size*.022))
    while size > 12:
        font=_font(size,formal)
        spacing=max(2,round(size*.10))
        bounds=d.multiline_textbbox((0,0),val,font=font,spacing=spacing,
                                     align="center",stroke_width=border)
        if bounds[2]-bounds[0] <= maxw and bounds[3]-bounds[1] <= maxh:
            break
        size=max(12,int(size*.94))
        border=max(0,round(size*.022))
    cx,cy=center
    x=int(cx-(bounds[0]+bounds[2])/2);y=int(cy-(bounds[1]+bounds[3])/2)
    shadow=max(1,int(size*.02))
    d.multiline_text((x+shadow,y+shadow),val,font=font,spacing=spacing,
                     fill=stroke_color,stroke_width=border+shadow,
                     stroke_fill=stroke_color,align="center")
    d.multiline_text((x,y),val,font=font,spacing=spacing,
                     fill=fill,stroke_width=border,stroke_fill=stroke_color,
                     align="center")

def _add_portrait(canvas, photograph, oval):
    if photograph is None:
        return canvas
    w,h=canvas.size
    # Oval coordinates name the photo interior, not its outer gold frame.
    x1,y1,x2,y2=oval
    pad=.009
    x1=int((x1+pad)*w);x2=int((x2-pad)*w)
    y1=int((y1+pad)*h);y2=int((y2-pad)*h)
    rectw=max(8,x2-x1);recth=max(8,y2-y1)
    rgb=photograph.convert("RGB")
    # ImageOps.fit crops to the oval's ratio; face geometry is never stretched.
    fitted=ImageOps.fit(rgb,(rectw,recth),Image.Resampling.LANCZOS,
                        centering=(.5,.31))
    mask=Image.new("L",(rectw,recth),0)
    draw=ImageDraw.Draw(mask)
    px=max(2,round(min(rectw,recth)*.013))
    draw.ellipse((px,px,rectw-px-1,recth-px-1),fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(max(1,round(min(rectw,recth)*.008))))
    canvas.paste(fitted,(x1,y1),mask)
    return canvas

def _draw_sign(background, key, record, values, size, portrait_photo):
    target=(int(size[0]),int(size[1]))
    original_ratio=background.width/background.height
    target_ratio=target[0]/target[1]
    # No anisotropic image scaling. Cover to prevent empty grey/white margins.
    # Cropping may remove ornaments for non-native proportions (warn in UI).
    base=ImageOps.fit(background,target,Image.Resampling.LANCZOS)
    # Photo mask is based on SOURCE geometry; map via cover crop to destination.
    oval=record.get("photo_oval",[.1,.2,.37,.7])
    if len(oval)!=4 or not (0<=oval[0]<oval[2]<=1 and 0<=oval[1]<oval[3]<=1):
        oval=[.1,.2,.37,.7]
    scale=max(target[0]/background.width,target[1]/background.height)
    offset_x=(target[0]-background.width*scale)/2
    offset_y=(target[1]-background.height*scale)/2
    mapped=[(oval[0]*background.width*scale+offset_x)/target[0],
            (oval[1]*background.height*scale+offset_y)/target[1],
            (oval[2]*background.width*scale+offset_x)/target[0],
            (oval[3]*background.height*scale+offset_y)/target[1]]
    mapped=[max(0.0,min(1.0,x)) for x in mapped]
    if mapped[0] < mapped[2] and mapped[1] < mapped[3]:
        _add_portrait(base,portrait_photo,mapped)
    d=ImageDraw.Draw(base)
    ink=record.get("ink","#4D345B")
    landscape=background.width>=background.height
    w,h=base.size
    u=min(w,h)
    if landscape:
        rx=.70
        fullplaque=(key in ("royal_violet","silk_gold"))
        # Keep text inside the right clear area; never cover portrait / flowers.
        _text_fit(d,values["heading"],(w*rx,h*.20),(w*.46,h*.090),u*.075,ink,"#FFF3D5",formal=True)
        _text_fit(d,values["name"],(w*rx,h*.348),(w*.51,h*.18),u*.112,ink,"#FFEDD0",formal=True)
        _text_fit(d,values["born"],(w*rx,h*.50),(w*.48,h*.080),u*.059,ink,"#FAF2E3")
        _text_fit(d,values["died"],(w*rx,h*.594),(w*.48,h*.080),u*.059,ink,"#FAF2E3")
        _text_fit(d,values["age"],(w*rx,h*.694),(w*.46,h*.080),u*.071,ink,"#FFF2D4",formal=True)
        _text_fit(d,values["closing"],(w*rx,h*.795),(w*.47,h*.068),u*.055,ink,"#FFF4E0",formal=True)
    else:
        rx=.50
        _text_fit(d,values["heading"],(w*rx,h*.661),(w*.68,h*.051),u*.058,ink,"#FAE9C6",formal=True)
        _text_fit(d,values["name"],(w*rx,h*.72),(w*.72,h*.080),u*.102,ink,"#FAE7C0",formal=True)
        _text_fit(d,values["born"],(w*rx,h*.792),(w*.70,h*.051),u*.051,ink,"#FFF4D8")
        _text_fit(d,values["died"],(w*rx,h*.846),(w*.70,h*.051),u*.051,ink,"#FFF4D8")
        _text_fit(d,values["age"],(w*rx,h*.902),(w*.69,h*.048),u*.061,ink,"#FFECBE",formal=True)
        _text_fit(d,values["closing"],(w*rx,h*.965),(w*.60,h*.035),u*.038,ink,"#FFF4DC")
    return base

def _maybe_photo(uploaded):
    if uploaded is None:
        return None
    if uploaded.size > 22*1024*1024:
        st.error("รูปผู้ล่วงลับใหญ่เกิน 22 MB")
        return None
    try:
        with Image.open(BytesIO(uploaded.getvalue())) as source:
            if source.width*source.height > 30_000_000:
                st.error("รูปผู้ล่วงลับใหญ่เกิน 30 ล้านพิกเซล")
                return None
            return ImageOps.exif_transpose(source).convert("RGB")
    except (OSError,ValueError,Image.DecompressionBombError):
        st.error("เปิดรูปผู้ล่วงลับไม่ได้ กรุณาใช้ PNG หรือ JPG")
        return None

def _choose_real(theme_id):
    shape=THEME_BY_ID[theme_id]["shape"]
    st.session_state["rmp_selected"]=theme_id
    if shape=="portrait":
        st.session_state["rmp_width"],st.session_state["rmp_height"]=100.,150.
        st.session_state["rmp_size_choice"]="100 × 150 ซม. แนวตั้ง"
    else:
        st.session_state["rmp_width"],st.session_state["rmp_height"]=150.,100.
        st.session_state["rmp_size_choice"]="150 × 100 ซม. แนวนอน"
    st.session_state.pop("rmp_export",None)

def _choose_size():
    selected=st.session_state["rmp_size_choice"]
    spec=SIZES.get(selected)
    if spec is not None:
        st.session_state["rmp_width"],st.session_state["rmp_height"]=spec

def render_memorial_real():
    st.markdown(CSS+CSS_REAL,unsafe_allow_html=True)
    st.markdown("""<section class="real-hero">
      <div style="font-size:13px;color:#f5d89b;letter-spacing:2px">THANASILP MEMORIAL DESIGN STUDIO</div>
      <h2>ป้ายไว้อาลัย กรอบทองและดอกไม้สมจริง</h2>
      <p>เลือกแบบสำเร็จรูป 13 แบบ • ใส่ภาพบุคคลจริง • พิมพ์ชื่อ วันชาตะ มรณะ
      และสิริอายุ • ตรวจพรีวิว • ดาวน์โหลด PNG หรือ TIFF</p></section>""",
      unsafe_allow_html=True)
    st.link_button("🏠 กลับหน้าหลัก","https://thanasin-ai-design.streamlit.app/")
    st.markdown('<div class="real-title">ขั้นตอนที่ 1 · เปิดชุดแม่แบบสมจริง</div>',unsafe_allow_html=True)
    installed_pack=_pack_from_repository()
    if installed_pack is not None:
        st.success("ใช้แม่แบบสมจริง 13 แบบที่ติดตั้งไว้บนเว็บไซต์แล้ว")
        pack=installed_pack
    else:
        st.markdown("""<div class="real-note">ดาวน์โหลดไฟล์
          <b>thanasilp_memorial_real_pack_13.zip</b> จากคำตอบ ChatGPT นี้
          แล้วอัปโหลดทั้ง ZIP ที่นี่ <b>ครั้งเดียวต่อเซสชัน</b>
          เพื่อเปิดกรอบทองและดอกไม้สมจริงทั้ง 13 แบบ
          รูปผู้ล่วงลับให้แนบแยกในขั้นตอนที่ 3
          </div>""",unsafe_allow_html=True)
        uploaded_pack=st.file_uploader("📦 อัปโหลด ZIP แม่แบบจริงทั้ง 13 แบบ",
            type=["zip"],key="rmp_pack_v1",
            help="รองรับชุดแม่แบบธนศิลป์ที่สร้างให้ในบทสนทนานี้")
        if uploaded_pack is None:
            st.warning("ยังไม่พบไฟล์ภาพสมจริงบนเว็บไซต์ จึงซ่อนภาพตัวอย่างกรอบแบบเดิม "
                       "กรุณาอัปโหลด ZIP แม่แบบเพื่อเริ่มออกแบบ")
            return
        pack=uploaded_pack.getvalue()
    try:
        manifest,cards=_cached_pack(pack)
    except (ValueError,RuntimeError) as exc:
        st.error(str(exc))
        return
    st.success("โหลดแม่แบบกรอบทองและดอกไม้สมจริงครบ 13 แบบแล้ว")
    if "rmp_selected" not in st.session_state:
        _choose_real("ivory_gold")
    current=st.session_state["rmp_selected"]
    st.markdown('<div class="real-title">ขั้นตอนที่ 2 · คลิกเลือกแบบ</div>',unsafe_allow_html=True)
    st.caption("ภาพบุคคลในตัวอย่างเป็นภาพจำลองที่สร้างด้วย AI สำหรับดูดีไซน์เท่านั้น "
               "ไม่ใช่รูปของลูกค้า และไม่ถูกนำไปใส่ในไฟล์ส่งออกของคุณ")
    group=st.radio("เลือกดู",["ทั้งหมด 13 แบบ","แนวนอน 9 แบบ","แนวตั้ง 4 แบบ"],
        key="rmp_view_mode",horizontal=True)
    options=(THEMES if group.startswith("ทั้งหมด") else
             [t for t in THEMES if t["shape"]==("landscape" if group.startswith("แนวนอน") else "portrait")])
    for index in range(0,len(options),3):
        cols=st.columns(3)
        for i,t in enumerate(options[index:index+3]):
            with cols[i]:
                with st.container(border=True):
                    st.image(cards[t["id"]],use_container_width=True)
                    st.caption(manifest["templates"][t["id"]]["title"])
                    selected=current==t["id"]
                    st.button("✓ แบบที่เลือกอยู่" if selected else "เลือกใช้แบบนี้",
                        key="rmp_pick_"+t["id"],use_container_width=True,
                        disabled=selected,on_click=_choose_real,args=(t["id"],))
    st.markdown('<div class="real-title">ขั้นตอนที่ 3 · ใส่รูปและกรอกข้อความ</div>',unsafe_allow_html=True)
    left,right=st.columns([.88,1.12],gap="large")
    with left:
        heading=st.text_input("หัวป้าย",value="ด้วยรักและอาลัย",key="rmp_heading")
        name=st.text_input("ชื่อผู้ล่วงลับ",value="คุณแม่ชื่อ นามสกุล",key="rmp_name")
        c1,c2=st.columns(2)
        with c1:
            born=st.date_input("ชาตะ",value=date(1956,11,5),min_value=date(1850,1,1),
                               max_value=date(2100,12,31),format="DD/MM/YYYY",key="rmp_birth")
        with c2:
            died=st.date_input("มรณะ",value=date(2026,11,8),min_value=date(1850,1,1),
                               max_value=date(2100,12,31),format="DD/MM/YYYY",key="rmp_death")
        invalid=died<born
        if invalid:
            st.error("วันมรณะต้องไม่ก่อนวันชาตะ")
        computed=max(0,_age_on(born,died))
        manual_age=st.checkbox("ระบุสิริอายุเอง",key="rmp_custom_age")
        age=(st.number_input("สิริอายุ (ปี)",0,130,computed,key="rmp_age_val")
             if manual_age else computed)
        if not manual_age:
            st.caption(f"สิริอายุคำนวณอัตโนมัติ: {computed} ปีเต็ม")
        closing=st.text_input("ข้อความด้านล่าง",value="ด้วยรักและคิดถึงเสมอ",key="rmp_closing")
        thaifont=st.checkbox("ใช้เลขไทย",value=True,key="rmp_thai")
        upl=st.file_uploader("📷 ใส่ภาพบุคคล JPG / PNG",type=["jpg","jpeg","png"],key="rmp_photo")
        photo=_maybe_photo(upl)
        st.caption("รูปจะถูกครอปเข้าในวงรีโดยรักษาสัดส่วนใบหน้า ไม่มีการแต่งใบหน้าด้วย AI")
        st.selectbox("ขนาดป้าย",list(SIZES),key="rmp_size_choice",on_change=_choose_size)
        c1,c2,c3=st.columns(3)
        with c1:
            width=st.number_input("กว้าง (ซม.)",20.,600.,step=5.,key="rmp_width")
        with c2:
            height=st.number_input("สูง (ซม.)",20.,600.,step=5.,key="rmp_height")
        with c3:
            dpi=st.number_input("DPI",30,300,150,step=10,key="rmp_dpi")
        fmt=st.selectbox("ดาวน์โหลดไฟล์",["PNG","TIFF"],key="rmp_fmt")
    values={
        "heading":heading,"name":name,
        "born":"ชาตะ  "+_date_th(born,thaifont),
        "died":"มรณะ  "+_date_th(died,thaifont),
        "age":"สิริอายุ  "+(str(age).translate(THAI_DIGITS) if thaifont else str(age))+" ปี",
        "closing":closing,
    }
    source=_get_image(pack,current)
    info=manifest["templates"][current]
    preview_w=1050 if width>=height else 620
    preview_h=max(200,int(preview_w*height/width))
    ratio=min(1,math.sqrt(1_300_000/max(1,preview_w*preview_h)))
    preview_size=(max(150,int(preview_w*ratio)),max(150,int(preview_h*ratio)))
    with right:
        st.markdown("**👁️ ภาพตัวอย่างของแบบที่เลือก**")
        preview=_draw_sign(source,current,info,values,preview_size,photo)
        st.image(preview,use_container_width=True)
        st.caption("ภาพนี้ใช้แม่แบบภาพสมจริงและข้อความที่กรอก ไม่ใช่กราฟิกกรอบง่ายแบบเดิม")
        source_dpi=source.width/(width/2.54)
        st.caption(f"พื้นหลังต้นทาง {source.width:,} × {source.height:,} พิกเซล"
                   f" • ถ้าพิมพ์กว้าง {width:g} ซม. รายละเอียดพื้นหลังจริงประมาณ {source_dpi:.1f} DPI")
        if abs((width/height)/(source.width/source.height)-1)>.06:
            st.warning("สัดส่วนป้ายใหม่ไม่ตรงกับแม่แบบ อาจครอปลายกรอบ/ดอกไม้บางส่วน "
                       "แนะนำเลือกขนาดเดียวกับแนวของแม่แบบ")
        if source_dpi<70:
            st.warning("ภาพพื้นหลังจากรุ่นทดลองยังมีความละเอียดต้นทางจำกัด "
                       "การปรับ DPI ส่งออกสูงไม่ได้สร้างรายละเอียดใหม่ โปรดตรวจภาพเต็มขนาดก่อนพิมพ์ป้ายใหญ่")
        px,py,actual=_size_px(width,height,dpi)
        st.caption(f"ไฟล์ที่จะสร้าง: {px:,} × {py:,} พิกเซล • DPI ฝังในไฟล์ ~{actual:g}")
        if actual<dpi:
            st.warning("ไฟล์เกินข้อจำกัดหน่วยความจำ ลด DPI ส่งออกจริงอัตโนมัติ")
        photo_sig=sha256(upl.getvalue()).hexdigest() if photo is not None else ""
        setting_sig=(sha256(pack).hexdigest(),current,tuple(sorted(values.items())),photo_sig,
                     px,py,actual,fmt)
        if st.button("🖨️ สร้างไฟล์งานพิมพ์จากแม่แบบจริง",
            key="rmp_make",use_container_width=True,type="primary",disabled=invalid):
            try:
                with st.spinner("กำลังวางชื่อและรูปบนแม่แบบจริงในขนาดพิมพ์..."):
                    result=_draw_sign(source,current,info,values,(px,py),photo)
                    buffer=BytesIO()
                    if fmt=="TIFF":
                        result.convert("RGB").save(buffer,format="TIFF",
                                    compression="tiff_lzw",dpi=(actual,actual))
                    else:
                        result.save(buffer,format="PNG",dpi=(actual,actual))
                    st.session_state["rmp_export"]=(setting_sig,buffer.getvalue())
            except (MemoryError,OSError,ValueError) as exc:
                st.error("สร้างไฟล์ไม่ได้: "+type(exc).__name__)
        out=st.session_state.get("rmp_export")
        if out and out[0]==setting_sig:
            st.download_button("⬇️ ดาวน์โหลดไฟล์ "+fmt,out[1],
                file_name="thanasilp_real_"+current+("_print.tif" if fmt=="TIFF" else "_print.png"),
                mime="image/tiff" if fmt=="TIFF" else "image/png",
                use_container_width=True,type="primary")
        elif out:
            st.caption("มีการแก้ไขข้อมูล กรุณากดสร้างไฟล์ใหม่ให้ตรงกับพรีวิว")
        st.caption("รูปบุคคลและข้อความมีความเป็นส่วนตัวในเซสชันปัจจุบัน ไม่ฝังลงในชุดแม่แบบกลาง")
