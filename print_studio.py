"""ธนศิลป์ AI Design: เครื่องมือทำงานพิมพ์พื้นฐานที่ประมวลผลไฟล์จริง"""
from __future__ import annotations

import glob
import math
from datetime import date
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import (
    Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter,
    ImageFont, ImageOps,
)

MAX_UPLOAD_MB = 30
MAX_SOURCE_PIXELS = 35_000_000
MAX_OUTPUT_PIXELS = 18_000_000


def _open_image(upload, max_pixels=MAX_SOURCE_PIXELS):
    if upload is None:
        return None
    if upload.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.error("ไฟล์ใหญ่เกิน 30 MB กรุณาลดขนาดไฟล์ก่อน")
        return None
    try:
        with Image.open(BytesIO(upload.getvalue())) as source:
            if source.width * source.height > max_pixels:
                st.error("ภาพต้นฉบับใหญ่เกินขีดจำกัดสำหรับเซิร์ฟเวอร์ กรุณาลดขนาดภาพก่อน")
                return None
            image = ImageOps.exif_transpose(source)
            return image.convert("RGBA")
    except Exception:
        st.error("ไม่สามารถเปิดภาพนี้ได้ กรุณาใช้ไฟล์ PNG, JPG หรือ TIFF ที่สมบูรณ์")
        return None


def _target_pixels(width_cm, height_cm, requested_dpi, max_pixels=MAX_OUTPUT_PIXELS):
    width = max(1, round(width_cm / 2.54 * requested_dpi))
    height = max(1, round(height_cm / 2.54 * requested_dpi))
    dpi = float(requested_dpi)
    if width * height > max_pixels:
        scale = math.sqrt(max_pixels / (width * height))
        width = max(1, int(width * scale))
        height = max(1, int(height * scale))
        dpi *= scale
    return width, height, round(dpi, 1)


def _image_bytes(image, fmt="PNG", dpi=150, cmyk=False):
    out = BytesIO()
    if fmt == "TIFF":
        img = image.convert("CMYK" if cmyk else "RGB")
        img.save(out, format="TIFF", compression="tiff_lzw", dpi=(dpi, dpi))
    else:
        image.save(out, format="PNG", optimize=False, dpi=(dpi, dpi))
    return out.getvalue()


def _download(label, data, filename, mime):
    st.download_button(label, data=data, file_name=filename, mime=mime,
                       use_container_width=True)


@st.cache_data(show_spinner=False)
def _system_thai_font():
    paths = [
        "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
        "/usr/share/fonts/truetype/tlwg/Kinnari.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifThai-Regular.ttf",
    ]
    for pattern in (
        "/usr/share/fonts/**/*Sarabun*.ttf",
        "/usr/share/fonts/**/*Garuda*.ttf",
        "/usr/share/fonts/**/*Loma*.ttf",
        "/usr/share/fonts/**/*NotoSansThai*.ttf",
    ):
        paths.extend(glob.glob(pattern, recursive=True))
    return next((p for p in paths if Path(p).is_file()), None)


def _font(size, font_upload=None):
    try:
        if font_upload is not None:
            return ImageFont.truetype(BytesIO(font_upload.getvalue()), size)
        path = _system_thai_font()
        return ImageFont.truetype(path, size) if path else None
    except Exception:
        return None


def _preview(img, label=None):
    img_copy = img.copy()
    img_copy.thumbnail((1100, 800), Image.Resampling.LANCZOS)
    st.image(img_copy, caption=label, use_container_width=True)


def _tool_resize():
    st.markdown("#### 1. ขยายภาพ / กำหนดขนาดจริงและ DPI")
    st.caption("ขยายภาพและปรับความคมด้วยการประมวลผลภาพพื้นฐาน ไม่ใช่ AI สร้างรายละเอียดที่หายไป")
    up = st.file_uploader("อัปโหลดภาพสำหรับขยาย", type=["jpg", "jpeg", "png", "tif", "tiff"], key="studio_resize_upload")
    c1, c2, c3 = st.columns(3)
    with c1:
        width_cm = st.number_input("กว้าง (ซม.)", 1.0, 600.0, 100.0, 1.0, key="studio_resize_width")
    with c2:
        height_cm = st.number_input("สูง (ซม.)", 1.0, 600.0, 60.0, 1.0, key="studio_resize_height")
    with c3:
        dpi = st.number_input("DPI ที่ต้องการ", 30, 600, 150, 10, key="studio_resize_dpi")
    col_a, col_b = st.columns(2)
    with col_a:
        sharpen = st.slider("เพิ่มความคมชัด", 0.0, 2.0, 0.3, 0.1, key="studio_resize_sharp")
    with col_b:
        fmt = st.selectbox("รูปแบบไฟล์", ["PNG", "TIFF"], key="studio_resize_format")
    cmyk = st.checkbox("ส่งออก TIFF แบบ CMYK (ไม่มี ICC โปรไฟล์เฉพาะเครื่องพิมพ์)",
                       value=False, disabled=(fmt != "TIFF"), key="studio_resize_cmyk")
    wpx, hpx, effective_dpi = _target_pixels(width_cm, height_cm, dpi)
    st.caption(f"ขนาดส่งออก {wpx:,} × {hpx:,} พิกเซล • DPI ใช้ได้จริงประมาณ {effective_dpi:g}")
    if effective_dpi < dpi:
        st.warning("ภาพขนาดนี้ใหญ่เกินกำลังประมวลผลของเว็บ จึงลดจำนวนพิกเซลและ DPI ลงเพื่อป้องกันเว็บค้าง")
    if st.button("🖨️ สร้างไฟล์ขยายภาพ", use_container_width=True, key="studio_resize_generate"):
        image = _open_image(up)
        if image is not None:
            with st.spinner("กำลังสร้างไฟล์..."):
                out = image.resize((wpx, hpx), Image.Resampling.LANCZOS)
                if sharpen:
                    out = ImageEnhance.Sharpness(out).enhance(1 + sharpen)
                binary = _image_bytes(out, fmt, effective_dpi, cmyk)
                st.session_state["studio_resize_result"] = (binary, fmt, wpx, hpx)
    result = st.session_state.get("studio_resize_result")
    if result:
        binary, format_name, ww, hh = result
        st.success(f"ไฟล์ล่าสุด: {ww:,} × {hh:,} พิกเซล")
        _download("⬇️ ดาวน์โหลดไฟล์สำหรับงานพิมพ์",
                  binary, "thanasilp_resized." + ("tif" if format_name == "TIFF" else "png"),
                  "image/tiff" if format_name == "TIFF" else "image/png")
    st.caption("หมายเหตุ: การเพิ่ม DPI/พิกเซลไม่ได้ทำให้ภาพต้นฉบับที่เบลอมีรายละเอียดจริงเพิ่มขึ้น และงาน CMYK ควรตรวจสีด้วยโปรไฟล์ ICC ของร้านพิมพ์")


def _tool_text():
    st.markdown("#### 2. เพิ่มและแก้ข้อความบนภาพ")
    st.caption("ใส่ข้อความใหม่ พร้อมสี ขอบ เงา และตำแหน่งได้ • การปิดข้อความเดิมใช้สี่เหลี่ยมสีพื้น ไม่ใช่การลบเนียนด้วย AI")
    up = st.file_uploader("อัปโหลดภาพป้าย", type=["jpg", "jpeg", "png"], key="studio_text_upload")
    image = _open_image(up)
    if image is not None:
        st.caption(f"ภาพต้นฉบับ {image.width:,} × {image.height:,} พิกเซล")
    content = st.text_area("ข้อความใหม่ (ภาษาไทยได้)", value="", height=80, key="studio_text_content")
    font_upload = st.file_uploader("ฟอนต์ TTF/OTF ของคุณ (ไม่บังคับ)", type=["ttf", "otf"], key="studio_text_font")
    if not _system_thai_font() and font_upload is None:
        st.warning("เซิร์ฟเวอร์ยังไม่พบฟอนต์ไทย กรุณาอัปโหลดไฟล์ TTF/OTF เพื่อให้ข้อความภาษาไทยแสดงถูกต้อง")
    c1, c2, c3 = st.columns(3)
    with c1:
        size = st.number_input("ขนาดฟอนต์ (px)", 10, 500, 80, 5, key="studio_text_size")
        x_pct = st.slider("ตำแหน่งซ้าย (%)", 0, 100, 10, key="studio_text_x")
    with c2:
        color = st.color_picker("สีตัวอักษร", "#FFFFFF", key="studio_text_color")
        y_pct = st.slider("ตำแหน่งบน (%)", 0, 100, 40, key="studio_text_y")
    with c3:
        stroke = st.slider("ความหนาขอบ (px)", 0, 20, 3, key="studio_text_stroke")
        stroke_color = st.color_picker("สีขอบตัวอักษร", "#14284D", key="studio_text_stroke_color")
    shadow = st.slider("เงาตัวอักษร (px)", 0, 20, 3, key="studio_text_shadow")
    cover = st.checkbox("ปิดทับข้อความเดิมด้วยสี่เหลี่ยมสีพื้น", value=False, key="studio_text_cover")
    if cover:
        cc1, cc2 = st.columns(2)
        with cc1:
            cx = st.slider("มุมซ้ายของพื้นที่ปิดทับ (%)", 0, 100, 15, key="studio_text_cover_x")
            cy = st.slider("มุมบนของพื้นที่ปิดทับ (%)", 0, 100, 35, key="studio_text_cover_y")
            cover_color = st.color_picker("สีพื้นปิดทับ", "#FFFFFF", key="studio_text_cover_color")
        with cc2:
            cw = st.slider("ความกว้างพื้นที่ปิดทับ (%)", 1, 100, 65, key="studio_text_cover_w")
            ch = st.slider("ความสูงพื้นที่ปิดทับ (%)", 1, 100, 20, key="studio_text_cover_h")
    if st.button("✏️ สร้างภาพแก้ข้อความ", use_container_width=True, key="studio_text_generate"):
        if image is None:
            st.error("กรุณาอัปโหลดภาพก่อน")
        elif not content.strip():
            st.error("กรุณากรอกข้อความใหม่")
        else:
            font = _font(size, font_upload)
            if font is None:
                st.error("ไม่มีฟอนต์ที่ใช้ได้ กรุณาอัปโหลดฟอนต์ TTF/OTF")
            else:
                with st.spinner("กำลังจัดข้อความบนภาพ..."):
                    out = image.copy()
                    d = ImageDraw.Draw(out)
                    if cover:
                        x1, y1 = int(out.width * cx / 100), int(out.height * cy / 100)
                        x2, y2 = min(out.width, x1 + int(out.width * cw / 100)), min(out.height, y1 + int(out.height * ch / 100))
                        d.rectangle((x1, y1, x2, y2), fill=cover_color)
                    x, y = int(out.width * x_pct / 100), int(out.height * y_pct / 100)
                    if shadow:
                        d.multiline_text((x + shadow, y + shadow), content, font=font,
                                         fill="#303030", spacing=12, stroke_width=stroke, stroke_fill="#303030")
                    d.multiline_text((x, y), content, font=font, fill=color,
                                     spacing=12, stroke_width=stroke, stroke_fill=stroke_color)
                    st.session_state["studio_text_result"] = _image_bytes(out)
                    st.session_state["studio_text_preview"] = out.copy()
    if "studio_text_result" in st.session_state:
        if "studio_text_preview" in st.session_state:
            _preview(st.session_state["studio_text_preview"], "ตัวอย่างภาพล่าสุด")
        _download("⬇️ ดาวน์โหลดภาพ PNG ที่แก้ข้อความแล้ว",
                  st.session_state["studio_text_result"], "thanasilp_text_edited.png", "image/png")


def _flat_bg_transparency(image, tolerance, bg_choice):
    rgb = image.convert("RGB")
    if bg_choice == "ขาว":
        bg = (255, 255, 255)
    elif bg_choice == "ดำ":
        bg = (0, 0, 0)
    else:
        # สีมุมซ้ายบนเหมาะกับงานพื้นหลังสีเรียบ ไม่ใช่ฉากถ่ายภาพที่ซับซ้อน
        bg = rgb.getpixel((0, 0))
    difference = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg))
    r, g, b = difference.split()
    diff = ImageChops.lighter(ImageChops.lighter(r, g), b)
    feather = 15
    new_alpha = diff.point(lambda v: max(0, min(255, int((v - tolerance) * 255 / feather))))
    original_alpha = image.getchannel("A")
    out = image.copy()
    out.putalpha(ImageChops.darker(original_alpha, new_alpha))
    return out


def _sticker_with_outline(image, outline_px):
    padding = max(6, outline_px + 6)
    size = (image.width + 2 * padding, image.height + 2 * padding)
    src = Image.new("RGBA", size, (0, 0, 0, 0))
    src.alpha_composite(image, (padding, padding))
    if not outline_px:
        return src
    a = src.getchannel("A")
    radius = min(int(outline_px), 30)
    dilated = a.filter(ImageFilter.MaxFilter(radius * 2 + 1))
    white = Image.new("RGBA", size, (255, 255, 255, 0))
    white.putalpha(dilated)
    return Image.alpha_composite(white, src)


def _sticker_guide(image):
    alpha = image.getchannel("A")
    outside = alpha.filter(ImageFilter.MaxFilter(9))
    line_alpha = ImageChops.subtract(outside, alpha)
    guide = Image.new("RGBA", image.size, (240, 28, 42, 0))
    guide.putalpha(line_alpha)
    return Image.alpha_composite(image, guide)


def _tool_sticker():
    st.markdown("#### 3. สติกเกอร์ไดคัท / ขอบขาว / จัดเต็มแผ่น")
    st.caption("เหมาะกับรูปหรือโลโก้พื้นหลังสีเรียบ • ภาพถ่ายฉากซับซ้อนอาจต้องลบพื้นหลังด้วยเครื่องมือ AI ก่อน")
    up = st.file_uploader("อัปโหลดรูปสติกเกอร์", type=["png", "jpg", "jpeg"], key="studio_sticker_upload")
    im = _open_image(up, max_pixels=16_000_000)
    c1, c2, c3 = st.columns(3)
    with c1:
        bg_choice = st.selectbox("พื้นหลัง", ["ใช้ความโปร่งใสเดิม", "อัตโนมัติจากมุมซ้ายบน", "ขาว", "ดำ"], key="studio_sticker_bg")
    with c2:
        threshold = st.slider("ความไวในการลบพื้นหลัง", 0, 100, 30, key="studio_sticker_threshold")
    with c3:
        outline = st.slider("ขอบขาว (พิกเซล)", 0, 25, 7, key="studio_sticker_outline")
    st.markdown("**การจัดเรียงสติกเกอร์ลงแผ่น**")
    col1, col2, col3 = st.columns(3)
    with col1:
        sheet = st.selectbox("ขนาดแผ่น", ["A4 (21 × 29.7)", "A3 (29.7 × 42)", "30 × 45 ซม."], key="studio_sticker_sheet")
    with col2:
        one_width = st.number_input("กว้างต่อชิ้น (ซม.)", 1.0, 25.0, 5.0, 0.5, key="studio_sticker_width")
    with col3:
        space_mm = st.number_input("ระยะห่าง (มม.)", 0, 20, 3, 1, key="studio_sticker_spacing")
    if st.button("✂️ ทำไดคัทและจัดเรียงแผ่น", use_container_width=True, key="studio_sticker_generate"):
        if im is None:
            st.error("กรุณาอัปโหลดภาพสติกเกอร์ก่อน")
        else:
            with st.spinner("กำลังทำขอบและจัดเรียง..."):
                base = im.copy()
                base.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
                if bg_choice != "ใช้ความโปร่งใสเดิม":
                    base = _flat_bg_transparency(base, threshold,
                        "อัตโนมัติ" if bg_choice == "อัตโนมัติจากมุมซ้ายบน" else bg_choice)
                sticker = _sticker_with_outline(base, outline)
                wcm, hcm = {
                    "A4 (21 × 29.7)": (21.0, 29.7),
                    "A3 (29.7 × 42)": (29.7, 42.0),
                    "30 × 45 ซม.": (30.0, 45.0),
                }[sheet]
                sheet_w_px, sheet_h_px, actual_dpi = _target_pixels(wcm, hcm, 150)
                margin_cm = 0.5
                gap_cm = space_mm / 10.0
                sticker_h_cm = one_width * sticker.height / sticker.width
                cols = int((wcm - 2 * margin_cm + gap_cm) / (one_width + gap_cm))
                rows = int((hcm - 2 * margin_cm + gap_cm) / (sticker_h_cm + gap_cm))
                if cols < 1 or rows < 1:
                    st.error("สติกเกอร์ใหญ่เกินขนาดแผ่นที่เลือก กรุณาลดความกว้างต่อชิ้น")
                else:
                    scale_px = actual_dpi / 2.54
                    sw = max(1, round(one_width * scale_px))
                    sh = max(1, round(sticker_h_cm * scale_px))
                    tile = sticker.resize((sw, sh), Image.Resampling.LANCZOS)
                    sheet_img = Image.new("RGBA", (sheet_w_px, sheet_h_px), "white")
                    margin_px = round(margin_cm * scale_px)
                    gap_px = round(gap_cm * scale_px)
                    for row in range(rows):
                        for col in range(cols):
                            x = margin_px + col * (sw + gap_px)
                            y = margin_px + row * (sh + gap_px)
                            sheet_img.alpha_composite(tile, (x, y))
                    st.session_state["studio_sticker_result"] = {
                        "single": _image_bytes(sticker),
                        "guide": _image_bytes(_sticker_guide(sticker)),
                        "sheet": _image_bytes(sheet_img, dpi=actual_dpi),
                        "preview": sheet_img.copy(),
                        "count": cols * rows,
                    }
    result = st.session_state.get("studio_sticker_result")
    if result:
        st.success(f"จัดเรียงได้ {result['count']} ชิ้นต่อแผ่น")
        _preview(result["preview"], "ตัวอย่างแผ่นสติกเกอร์")
        _download("⬇️ ดาวน์โหลดสติกเกอร์ PNG โปร่งใสพร้อมขอบขาว",
                  result["single"], "thanasilp_sticker.png", "image/png")
        _download("⬇️ ดาวน์โหลดตัวอย่างเส้นไกด์ตัด PNG",
                  result["guide"], "thanasilp_cut_guide.png", "image/png")
        _download("⬇️ ดาวน์โหลดสติกเกอร์จัดเต็มแผ่น PNG",
                  result["sheet"], "thanasilp_sticker_sheet.png", "image/png")
    st.caption("เส้นตัดสีแดงที่ดาวน์โหลดเป็นภาพไกด์ raster ไม่ใช่เส้น CutContour/SVG สำหรับเครื่องตัด ต้องแปลงและตรวจเส้นตัดจริงก่อนผลิต")


def _parse_thai_date(text):
    raw = text.strip().replace("-", "/").replace(".", "/")
    if not raw:
        return None
    try:
        day, month, buddhist_year = (int(p) for p in raw.split("/"))
        if not 2400 <= buddhist_year <= 2700:
            return None
        return date(buddhist_year - 543, month, day)
    except (ValueError, TypeError):
        return None


def _thai_digits(text):
    return str(text).translate(str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙"))


def _fit_font(text, target_width, desired_size, font_upload):
    size = max(12, desired_size)
    while size >= 12:
        font = _font(size, font_upload)
        if font is None:
            return None
        try:
            span = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)
            if span[2] - span[0] <= target_width:
                return font
        except (UnicodeError, OSError):
            return None
        size = int(size * 0.88) if size > 14 else size - 1
    return _font(12, font_upload)


def _gradient(w, h, top, bottom):
    canvas = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(canvas)
    c1 = tuple(int(top[i:i + 2], 16) for i in (1, 3, 5))
    c2 = tuple(int(bottom[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(round(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        d.line((0, y, w, y), fill=col)
    return canvas


def _draw_center(draw, text, cx, y, max_width, size, color, font_upload):
    if not text:
        return
    font = _fit_font(text, max_width, size, font_upload)
    if font is None:
        return
    bounds = draw.textbbox((0, 0), text, font=font)
    x = round(cx - (bounds[2] - bounds[0]) / 2)
    draw.text((x, y), text, font=font, fill=color)


def _make_memorial(photo, name, born_text, died_text, age_label, subtitle,
                   heading, palette, wpx, hpx, font_upload, use_thai):
    themes = {
        "ฟ้าขาวสุภาพ": ("#F5FBFF", "#B6D6F5", "#173D69", "#FFFFFF"),
        "ดำทองเรียบหรู": ("#18171D", "#38303D", "#F3D7A0", "#29232D"),
        "ครีมทอง": ("#FFF8EC", "#E4D3B4", "#5A4225", "#FEFAF3"),
    }
    top, bottom, ink, panel = themes[palette]
    canvas = _gradient(wpx, hpx, top, bottom)
    d = ImageDraw.Draw(canvas)
    margin = max(8, int(min(wpx, hpx) * 0.025))
    line = max(2, int(min(wpx, hpx) * 0.004))
    d.rectangle((margin, margin, wpx - margin, hpx - margin), outline=ink, width=line)
    d.rectangle((margin * 2, margin * 2, wpx - margin * 2, hpx - margin * 2),
                outline=ink, width=max(1, line // 2))
    landscape = wpx >= hpx
    if landscape:
        box = (int(wpx * .065), int(hpx * .13), int(wpx * .43), int(hpx * .88))
        tx, tw = int(wpx * .71), int(wpx * .52)
        text_y = int(hpx * .18)
        base = min(wpx, hpx)
    else:
        box = (int(wpx * .18), int(hpx * .11), int(wpx * .82), int(hpx * .58))
        tx, tw = wpx // 2, int(wpx * .84)
        text_y = int(hpx * .62)
        base = min(wpx, hpx)
    d.rectangle(box, fill=panel, outline=ink, width=max(2, line))
    x1, y1, x2, y2 = box
    if photo is not None:
        photo_fit = ImageOps.fit(photo.convert("RGB"), (x2 - x1 - 2 * line, y2 - y1 - 2 * line),
                                 Image.Resampling.LANCZOS, centering=(0.5, 0.32))
        canvas.paste(photo_fit, (x1 + line, y1 + line))
        d = ImageDraw.Draw(canvas)
    else:
        _draw_center(d, "พื้นที่ใส่รูป", (x1 + x2) // 2, (y1 + y2) // 2,
                     x2 - x1 - 24, int(base * .04), ink, font_upload)
    details = []
    if born_text.strip():
        details.append("ชาตะ " + born_text.strip())
    if died_text.strip():
        details.append("มรณะ " + died_text.strip())
    if age_label:
        details.append("สิริอายุ " + age_label + " ปี")
    if use_thai:
        details = [_thai_digits(v) for v in details]
    line_gap = int(base * (.095 if landscape else .077))
    _draw_center(d, heading, tx, text_y, tw, int(base * .055), ink, font_upload)
    _draw_center(d, name or "ชื่อผู้วายชนม์", tx, text_y + line_gap, tw,
                 int(base * .075), ink, font_upload)
    for n, detail in enumerate(details):
        _draw_center(d, detail, tx, text_y + (n + 2) * line_gap,
                     tw, int(base * .039), ink, font_upload)
    if subtitle.strip():
        _draw_center(d, subtitle.strip(), tx,
                     text_y + (len(details) + 2) * line_gap,
                     tw, int(base * .031), ink, font_upload)
    return canvas


def _tool_memorial():
    st.markdown("#### 4. ภาพอาลัย / ป้ายงานศพแบบกรอกข้อมูล")
    st.caption("เลือกแบบ ใส่ภาพและชื่อ คำนวณอายุ และแปลงตัวเลขไทย โดยไม่ต้องใช้ AI สร้างตัวสะกด")
    photo_upload = st.file_uploader("อัปโหลดภาพบุคคล (ถ้ามี)", type=["png", "jpg", "jpeg"], key="studio_memorial_upload")
    font_upload = st.file_uploader("ฟอนต์ภาษาไทย TTF/OTF เพิ่มเติม (ไม่บังคับ)", type=["ttf", "otf"], key="studio_memorial_font")
    if not _system_thai_font() and font_upload is None:
        st.warning("หากไม่มีฟอนต์ไทยติดตั้งบนระบบ กรุณาอัปโหลดฟอนต์ไทย TTF/OTF")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("ชื่อผู้วายชนม์", key="studio_memorial_name")
        born = st.text_input("ชาตะ (วัน/เดือน/พ.ศ.) เช่น 02/07/2474", key="studio_memorial_born")
        heading = st.text_input("ข้อความหัวเรื่อง", value="ด้วยความอาลัย", key="studio_memorial_heading")
    with c2:
        died = st.text_input("มรณะ (วัน/เดือน/พ.ศ.)", key="studio_memorial_died")
        subtitle = st.text_input("ข้อความเพิ่มเติม", key="studio_memorial_subtitle")
        template = st.selectbox("รูปแบบป้าย", ["ฟ้าขาวสุภาพ", "ดำทองเรียบหรู", "ครีมทอง"], key="studio_memorial_template")
    use_thai = st.checkbox("แปลงตัวเลขเป็นเลขไทย", value=True, key="studio_memorial_thai_digits")
    count_age = st.checkbox("สิริอายุแบบนับเพิ่ม 1 ปี", value=False, key="studio_memorial_count_age")
    age_override = st.text_input("แก้สิริอายุเอง (เว้นว่างเพื่อคำนวณอัตโนมัติ)", key="studio_memorial_age_override")
    bd, dd = _parse_thai_date(born), _parse_thai_date(died)
    computed = None
    if born and bd is None:
        st.warning("รูปแบบวันชาตะไม่ถูกต้อง กรุณาใช้ วว/ดด/พ.ศ.")
    if died and dd is None:
        st.warning("รูปแบบวันมรณะไม่ถูกต้อง กรุณาใช้ วว/ดด/พ.ศ.")
    if bd and dd:
        if dd < bd:
            st.warning("วันมรณะต้องไม่ก่อนวันชาตะ")
        else:
            computed = dd.year - bd.year - ((dd.month, dd.day) < (bd.month, bd.day))
            if count_age:
                computed += 1
            st.caption(f"อายุที่คำนวณได้: {computed} ปี (ตรวจสอบวิธีนับสิริอายุของครอบครัวอีกครั้ง)")
    age = age_override.strip() or (str(computed) if computed is not None else "")
    c3, c4, c5 = st.columns(3)
    with c3:
        width_cm = st.number_input("กว้าง (ซม.)", 20.0, 400.0, 120.0, 10.0, key="studio_memorial_width")
    with c4:
        height_cm = st.number_input("สูง (ซม.)", 20.0, 400.0, 80.0, 10.0, key="studio_memorial_height")
    with c5:
        dpi = st.number_input("DPI", 50, 300, 150, 10, key="studio_memorial_dpi")
    wpx, hpx, effective_dpi = _target_pixels(width_cm, height_cm, dpi)
    st.caption(f"ไฟล์ที่ได้ {wpx:,} × {hpx:,} พิกเซล • DPI ใช้งานจริงประมาณ {effective_dpi:g}")
    if st.button("🕯️ สร้างป้ายอาลัย", use_container_width=True, key="studio_memorial_generate"):
        if not name.strip():
            st.error("กรุณากรอกชื่อผู้วายชนม์")
        elif (born and bd is None) or (died and dd is None) or (bd and dd and dd < bd):
            st.error("กรุณาตรวจสอบวันชาตะและวันมรณะ")
        elif _font(40, font_upload) is None:
            st.error("ยังไม่มีฟอนต์ไทยที่ใช้ได้ กรุณาอัปโหลดฟอนต์ TTF/OTF")
        else:
            photo = _open_image(photo_upload)
            with st.spinner("กำลังจัดองค์ประกอบป้าย..."):
                poster = _make_memorial(photo, name, born, died, age, subtitle,
                                        heading, template, wpx, hpx, font_upload, use_thai)
                st.session_state["studio_memorial_result"] = _image_bytes(poster, dpi=effective_dpi)
                st.session_state["studio_memorial_preview"] = poster.copy()
    if "studio_memorial_result" in st.session_state:
        _preview(st.session_state["studio_memorial_preview"], "ตัวอย่างป้ายล่าสุด")
        _download("⬇️ ดาวน์โหลดป้ายอาลัย PNG",
                  st.session_state["studio_memorial_result"], "thanasilp_memorial.png", "image/png")
    st.caption("โปรดตรวจสะกดชื่อ วันเดือนปี และรูปภาพก่อนพิมพ์จริง ภาพที่ส่งเข้าระบบออนไลน์จะถูกประมวลผลในเซิร์ฟเวอร์ ไม่ใช่ออฟไลน์")


def render_print_studio():
    """เครื่องมือในแท็บเดียวที่ไม่เปลี่ยนระบบสร้างคำสั่ง AI เดิม"""
    st.markdown("### 🖨️ ธนศิลป์ Print Studio")
    st.caption("เครื่องมือประมวลผลภาพเบื้องต้นบนเว็บ ไม่ต้องส่งคำสั่งไป ChatGPT สำหรับงานในแท็บนี้")
    st.info("ไฟล์ที่อัปโหลดจะถูกประมวลผลบนเซิร์ฟเวอร์ของเว็บ กรุณาได้รับอนุญาตก่อนใช้งานภาพบุคคล และอย่าอัปโหลดข้อมูลลับ")
    t1, t2, t3, t4 = st.tabs([
        "🔎 ขยายภาพ / DPI", "✏️ แก้ข้อความ", "✂️ สติกเกอร์ไดคัท", "🕯️ ป้ายงานศพ"
    ])
    with t1:
        _tool_resize()
    with t2:
        _tool_text()
    with t3:
        _tool_sticker()
    with t4:
        _tool_memorial()
