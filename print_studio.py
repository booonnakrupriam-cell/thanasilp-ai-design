"""ธนศิลป์ AI Design: เครื่องมือทำงานพิมพ์พื้นฐานที่ประมวลผลไฟล์จริง"""
from __future__ import annotations

import glob
import hashlib
import math
from datetime import date
from io import BytesIO
from pathlib import Path

import streamlit as st

from print_preview import prepare_quality_previews, render_quality_preview, render_quality_from_images, make_quality_demo_previews
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


@st.cache_data(show_spinner=False)
def _available_thai_fonts():
    fonts = {}
    for pattern in (
        "/usr/share/fonts/truetype/tlwg/*.ttf",
        "/usr/share/fonts/truetype/tlwg/*.otf",
        "/usr/share/fonts/**/*NotoSansThai*.ttf",
        "/usr/share/fonts/**/*NotoSerifThai*.ttf",
        "/usr/share/fonts/**/*Sarabun*.ttf",
    ):
        for path in sorted(glob.glob(pattern, recursive=True)):
            if Path(path).is_file():
                label = Path(path).stem.replace("_", " ")
                fonts.setdefault(label, path)
    return fonts


def _font(size, font_upload=None, font_choice=None):
    try:
        if font_upload is not None:
            return ImageFont.truetype(BytesIO(font_upload.getvalue()), size)
        path = _available_thai_fonts().get(font_choice) or _system_thai_font()
        return ImageFont.truetype(path, size) if path else None
    except Exception:
        return None


def _auto_temple_font_choice():
    """เลือกฟอนต์ไทยแนวงานวัดแบบอัตโนมัติ โดยเน้นลายไทยสุภาพและอ่านง่าย"""
    fonts = _available_thai_fonts()
    for family in ("Norasi", "Kinnari", "NotoSerifThai", "Sarabun", "Garuda"):
        variants = [name for name in fonts if name.lower().startswith(family.lower())]
        regular = [name for name in variants if not any(
            word in name.lower() for word in ("italic", "oblique", "bold")
        )]
        if regular:
            return regular[0]
        if variants:
            return variants[0]
    return next(iter(fonts), None)


def _draw_smooth_font_outline(canvas, content, xy, font, fill, stroke, stroke_fill, shadow):
    """วาดขอบตามเส้นฟอนต์จริง และลดรอยหยักด้วย supersampling เฉพาะตัวอักษร"""
    if not content or font is None:
        return
    # ป้องกันชั้นข้อความใหญ่มากจนกินหน่วยความจำของเซิร์ฟเวอร์
    scale = 2
    try:
        hf = font.font_variant(size=max(1, font.size * scale))
        spacing = 12 * scale
        w_stroke = int(stroke) * scale
        measure = ImageDraw.Draw(Image.new("L", (1, 1)))
        bbox = measure.multiline_textbbox((0, 0), content, font=hf, spacing=spacing, stroke_width=w_stroke)
        pad = (max(int(stroke), int(shadow)) + 6) * scale
        width = max(1, bbox[2] - bbox[0] + 2 * pad)
        height = max(1, bbox[3] - bbox[1] + 2 * pad)
        if width * height > 18_000_000:
            # หากข้อความยาวมาก ให้ใช้เส้นฟอนต์จริงที่ความละเอียดต้นฉบับ
            d = ImageDraw.Draw(canvas)
            if shadow:
                d.multiline_text((xy[0] + shadow, xy[1] + shadow),
                                 content, font=font, fill="#303030", spacing=12,
                                 stroke_width=int(stroke), stroke_fill="#303030")
            d.multiline_text(xy, content, font=font, fill=fill, spacing=12,
                             stroke_width=int(stroke), stroke_fill=stroke_fill)
            return
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        pos = (pad - bbox[0], pad - bbox[1])
        if shadow:
            draw.multiline_text((pos[0] + shadow * scale, pos[1] + shadow * scale),
                                content, font=hf, fill="#303030", spacing=spacing,
                                stroke_width=w_stroke, stroke_fill="#303030")
        draw.multiline_text(pos, content, font=hf, fill=fill, spacing=spacing,
                            stroke_width=w_stroke, stroke_fill=stroke_fill)
        layer = layer.resize((max(1, round(width / scale)),
                              max(1, round(height / scale))), Image.Resampling.LANCZOS)
        x = int(xy[0]) + math.floor((bbox[0] - pad) / scale)
        y = int(xy[1]) + math.floor((bbox[1] - pad) / scale)
        left, top = max(0, x), max(0, y)
        right = min(canvas.width, x + layer.width)
        bottom = min(canvas.height, y + layer.height)
        if right > left and bottom > top:
            crop = layer.crop((left - x, top - y, right - x, bottom - y))
            canvas.alpha_composite(crop, (left, top))
    except (OSError, ValueError):
        # กลับไปวาดแบบปกติโดยไม่ยืดหรือบิดตัวอักษร
        ImageDraw.Draw(canvas).multiline_text(xy, content, font=font, fill=fill,
                                              spacing=12, stroke_width=int(stroke),
                                              stroke_fill=stroke_fill)


def _small_preview(img):
    result = img.copy()
    result.thumbnail((1100, 800), Image.Resampling.LANCZOS)
    return result


def _preview(img, label=None):
    st.image(_small_preview(img), caption=label, use_container_width=True)


def _resize_print_image(image, dest_size, framing, resample,
                        bg_color="#FFFFFF", align_x=50, align_y=50):
    """Fit/extend/crop without changing the shapes of people, Thai glyphs or ornaments.

    Never scale x/y independently except in the explicitly warned stretch mode.
    """
    width, height = dest_size
    ax = max(0, min(100, int(align_x))) / 100
    ay = max(0, min(100, int(align_y))) / 100
    if framing == "ยืดให้เต็มกรอบ (อาจทำให้ตัวหนังสือเบี้ยว)":
        return image.resize(dest_size, resample)
    if framing == "เต็มกรอบแบบครอป (ไม่บิดอักษร)":
        return ImageOps.fit(image, dest_size, method=resample, centering=(ax, ay))

    # Contain always uses a SINGLE scale factor (width and height scale together).
    fitted = ImageOps.contain(image.convert("RGBA"), dest_size, method=resample)
    if framing == "คงภาพครบ • เติมฉากหลังเบลอ":
        # The blurred background is a new background; it does not synthesize
        # missing details or preserve the original design outside its bounds.
        ratio = min(1.0, 760 / max(1, width), 760 / max(1, height))
        small_size = (max(1, round(width * ratio)), max(1, round(height * ratio)))
        original_rgb = Image.new("RGBA", image.size, "#FFFFFF")
        original_rgb.alpha_composite(image.convert("RGBA"))
        blurred = ImageOps.fit(original_rgb.convert("RGB"), small_size,
                              method=Image.Resampling.LANCZOS, centering=(ax, ay))
        blurred = blurred.filter(
            ImageFilter.GaussianBlur(radius=max(4, min(small_size) / 22))
        )
        blurred = ImageEnhance.Brightness(blurred).enhance(0.76)
        canvas = blurred.resize(dest_size, Image.Resampling.BILINEAR).convert("RGBA")
    else:
        canvas = Image.new("RGBA", dest_size, bg_color)
    x = round((width - fitted.width) * ax)
    y = round((height - fitted.height) * ay)
    canvas.alpha_composite(fitted, (x, y))
    return canvas

def _apply_print_edge_mode(image, mode, strength, curve_smooth):
    """Enhance existing raster contours, preserving the original alpha and color balance.

    This does not reconstruct true glyph outlines or genuine missing image details.
    """
    if mode == "ไม่ปรับความคม" or strength <= 0:
        return image
    original_alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    if mode == "🔤 ตัวหนังสือและลายเส้นคม":
        radius, percent, threshold = 0.95, int(100 + strength * 88), 2
    elif mode == "🧩 โลโก้และเส้นเล็กคม":
        radius, percent, threshold = 0.7, int(110 + strength * 90), 1
    elif mode == "🎨 สีสดงานป้าย":
        rgb = ImageEnhance.Color(rgb).enhance(1.08 + strength * .11)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.02 + strength * .05)
        radius, percent, threshold = 1.0, int(65 + strength * 65), 2
    elif mode == "🌀 ส่วนโค้งฟอนต์เนียน คมขอบ":
        # Very light antialias-like smoothing BEFORE edge emphasis.
        if curve_smooth:
            softened = rgb.filter(ImageFilter.GaussianBlur(radius=.3 + .14 * curve_smooth))
            rgb = Image.blend(rgb, softened, min(.38, .09 * curve_smooth))
        radius, percent, threshold = .8, int(105 + strength * 76), 2
    else:
        radius, percent, threshold = 1.25, int(65 + strength * 65), 3
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=radius,
                                             percent=min(330, percent),
                                             threshold=threshold))
    result = rgb.convert("RGBA")
    result.putalpha(original_alpha)
    return result


def _live_resize_comparison(image, target_size, framing, mode, strength, smooth,
                            bg_color="#FFFFFF", align_x=50, align_y=50):
    """Preview a non-distorting original arrangement against the selected new layout."""
    tw, th = target_size
    ratio = min(1, 1700 / max(1, tw), 1050 / max(1, th),
                math.sqrt(1_550_000 / max(1, tw * th)))
    size = (max(1, int(tw * ratio)), max(1, int(th * ratio)))
    before = _resize_print_image(
        image, size, "คงสัดส่วนภาพเดิม (ไม่ยืดตัวหนังสือ)",
        Image.Resampling.BILINEAR, bg_color, 50, 50)
    after = _resize_print_image(
        image, size, framing, Image.Resampling.LANCZOS, bg_color, align_x, align_y)
    after = _apply_print_edge_mode(after, mode, strength, smooth)
    return prepare_quality_previews(before, after)


# รูปแบบการปรับคมที่ผู้ใช้เลือกจากภาพตัวอย่าง
RESIZE_PRESETS = {
    "🪧 ป้ายตัวหนังสือคม": (
        "🔤 ตัวหนังสือและลายเส้นคม", .9, 0,
        "เพิ่มความคมขอบตัวใหญ่และเส้นป้าย"),
    "🌀 ฟอนต์โค้งเนียน": (
        "🌀 ส่วนโค้งฟอนต์เนียน คมขอบ", .85, 2,
        "ลดรอยหยักบริเวณส่วนโค้ง โดยไม่ยืดรูปทรง"),
    "🧩 โลโก้ / เส้นเล็ก": (
        "🧩 โลโก้และเส้นเล็กคม", 1.0, 0,
        "เน้นเส้นย่อย ขอบโลโก้ และลายละเอียด"),
    "📷 ภาพบุคคลธรรมชาติ": (
        "📷 ความคมชัดธรรมชาติ", .45, 0,
        "ปรับภาพคนอย่างนุ่มนวล ไม่เร่งขอบมาก"),
    "🎨 สีสดงานป้าย": (
        "🎨 สีสดงานป้าย", .55, 0,
        "เพิ่มความสดของสีและคมชัดพอเหมาะ"),
    "⚪ รักษาภาพต้นฉบับ": (
        "ไม่ปรับความคม", 0.0, 0,
        "ขยายด้วย LANCZOS ไม่เร่งสีและขอบ"),
}


SIGN_SIZE_PRESETS = {
    "200 × 100 ซม.": (200.0, 100.0),
    "240 × 120 ซม.": (240.0, 120.0),
    "300 × 100 ซม.": (300.0, 100.0),
    "300 × 150 ซม.": (300.0, 150.0),
    "X-Stand 60 × 160": (60.0, 160.0),
    "Roll-up 80 × 200": (80.0, 200.0),
}


def _set_resize_size_preset(label):
    width, height = SIGN_SIZE_PRESETS[label]
    st.session_state["studio_resize_width"] = width
    st.session_state["studio_resize_height"] = height


def _set_resize_150x200_to_100x200():
    """Example layout: target aspect differs, so use fitting rather than distortion."""
    st.session_state["studio_resize_source_width_v4"] = 150.0
    st.session_state["studio_resize_source_height_v4"] = 200.0
    st.session_state["studio_resize_width"] = 100.0
    st.session_state["studio_resize_height"] = 200.0
    st.session_state["studio_resize_framing_v2"] = "คงสัดส่วนภาพเดิม (ไม่ยืดตัวหนังสือ)"
    st.session_state["studio_resize_manual_source_v4"] = True
    st.session_state["studio_resize_align_x_v4"] = 50
    st.session_state["studio_resize_align_y_v4"] = 50


def _apply_resize_dropdown_choice():
    _set_resize_preset(st.session_state["studio_resize_preset_dropdown_v4"])


def _set_resize_preset(name):
    mode, strength, smooth, _ = RESIZE_PRESETS[name]
    st.session_state["studio_resize_preset_v3"] = name
    st.session_state["studio_resize_preset_dropdown_v4"] = name
    st.session_state["studio_resize_edge_mode_v2"] = mode
    st.session_state["studio_resize_edge_strength_v2"] = strength
    st.session_state["studio_resize_curve_v2"] = smooth


def _resize_preset_preview(image, preset):
    """Small real preview, not an unrelated decorative illustration."""
    mode, strength, smooth, _ = RESIZE_PRESETS[preset]
    thumb = image.copy()
    thumb.thumbnail((440, 205), Image.Resampling.LANCZOS)
    if thumb.mode != "RGBA":
        thumb = thumb.convert("RGBA")
    return _apply_print_edge_mode(thumb, mode, strength, smooth)


def _tool_resize():
    st.markdown("#### 1. อัพสเกลภาพ / ปรับเส้นคมสำหรับพิมพ์ + ลากก่อน–หลัง")
    st.caption("อัปโหลดรูป → เลือกแบบปรับคม → ลากเส้น ↔ ดูก่อน–หลังจริง → สร้างไฟล์พร้อมพิมพ์ ไม่ต้องออกจากโหมดนี้")
    up = st.file_uploader("อัปโหลดภาพสำหรับขยาย", type=["jpg", "jpeg", "png", "tif", "tiff"],
                          key="studio_resize_upload")

    image = _open_image(up) if up is not None else None
    if image is not None:
        st.caption(f"ภาพต้นฉบับ {image.width:,} × {image.height:,} พิกเซล")
    if "studio_resize_preset_v3" not in st.session_state:
        _set_resize_preset("🪧 ป้ายตัวหนังสือคม")
    elif "studio_resize_preset_dropdown_v4" not in st.session_state:
        st.session_state["studio_resize_preset_dropdown_v4"] = st.session_state["studio_resize_preset_v3"]
    st.markdown("**🎨 เลือกรูปแบบเพิ่มความคม**")
    st.selectbox(
        "รูปแบบปรับคมสำเร็จรูป (เลือกแล้วอัปเดตตัวเลื่อนอัตโนมัติ)",
        options=list(RESIZE_PRESETS),
        key="studio_resize_preset_dropdown_v4",
        on_change=_apply_resize_dropdown_choice,
    )
    with st.expander("🖼️ ดูภาพตัวอย่างปรับคม 6 แบบ แล้วกดเลือกได้", expanded=False):
        st.markdown("#### 🎨 เลือกรูปแบบเพิ่มความคมจากตัวอย่าง")
        st.caption("เลือกรูปแบบที่ต้องการด้วยปุ่มใต้ภาพ โปรแกรมจะตั้งโหมด ความคม และส่วนโค้งให้ทันที และยังปรับละเอียดเองได้ด้านล่าง")
        if image is not None:
            preset_src = image.copy()
            preset_src.thumbnail((520, 260), Image.Resampling.LANCZOS)
        else:
            _, demo_jpg = make_quality_demo_previews()
            preset_src = Image.open(BytesIO(demo_jpg)).convert("RGBA")
            preset_src.thumbnail((520, 260), Image.Resampling.LANCZOS)
        all_presets = list(RESIZE_PRESETS)
        for start_index in range(0, len(all_presets), 2):
            preset_cols = st.columns(2)
            for j, preset_name in enumerate(all_presets[start_index:start_index+2]):
                with preset_cols[j]:
                    with st.container(border=True):
                        st.markdown("**" + preset_name + "**")
                        st.image(_resize_preset_preview(preset_src, preset_name),
                                 use_container_width=True)
                        st.caption(RESIZE_PRESETS[preset_name][3])
                        active = st.session_state.get("studio_resize_preset_v3") == preset_name
                        st.button(
                            "✅ เลือกอยู่" if active else "เลือกแบบนี้",
                            key="studio_resize_choose_preset_" + str(start_index + j),
                            disabled=active, use_container_width=True,
                            on_click=_set_resize_preset, args=(preset_name,))
        st.caption("รูปตัวอย่างนี้ใช้ภาพที่อัปโหลด หรือใช้ภาพสาธิตถ้ายังไม่อัปโหลด")

    with st.expander("📐 เลือกขนาดป้ายยอดนิยม (กดเลือกได้) — หรือกรอกขนาดเอง", expanded=False):
        size_cols = st.columns(3)
        for size_index, (size_label, (size_w, size_h)) in enumerate(SIGN_SIZE_PRESETS.items()):
            with size_cols[size_index % 3]:
                st.button(size_label,
                          key="studio_resize_size_choice_" + str(size_index),
                          use_container_width=True,
                          on_click=_set_resize_size_preset, args=(size_label,))
    st.markdown("#### 📐 เปลี่ยนขนาดป้ายโดยไม่เสียรูปทรง")
    st.caption("ตัวอย่าง: จากป้าย 150 × 200 ซม. → 100 × 200 ซม. สามารถคงคนและตัวหนังสือไม่ให้บีบ/ยืด โดยเลือกเติมพื้นที่ว่างหรือครอป")
    st.button("✅ ลองตัวอย่าง 150 × 200 → 100 × 200 ซม.",
              key="studio_resize_example_ratio_v4", use_container_width=True,
              on_click=_set_resize_150x200_to_100x200)
    check_original = st.checkbox("ระบุขนาดป้ายต้นฉบับ (ไม่บังคับ)",
                                 value=False, key="studio_resize_manual_source_v4")
    source_width_cm = source_height_cm = None
    if check_original:
        origin_col1, origin_col2 = st.columns(2)
        with origin_col1:
            source_width_cm = st.number_input("กว้างต้นฉบับ (ซม.)", 1.0, 600.0, 150.0, 1.0,
                                             key="studio_resize_source_width_v4")
        with origin_col2:
            source_height_cm = st.number_input("สูงต้นฉบับ (ซม.)", 1.0, 600.0, 200.0, 1.0,
                                              key="studio_resize_source_height_v4")
    st.caption("อัตราส่วนที่ใช้วางจริงอ้างอิงพิกเซลจากไฟล์ต้นฉบับ ไม่บีบหรือยืดตามขนาดที่กรอก")

    c1, c2, c3 = st.columns(3)
    with c1:
        width_cm = st.number_input("กว้าง (ซม.)", 1.0, 600.0, 100.0, 1.0, key="studio_resize_width")
    with c2:
        height_cm = st.number_input("สูง (ซม.)", 1.0, 600.0, 60.0, 1.0, key="studio_resize_height")
    with c3:
        dpi = st.number_input("DPI ที่ต้องการ", 30, 600, 150, 10, key="studio_resize_dpi")

    st.markdown("**🔤 โหมดปรับเส้นคม / ตัวหนังสือ / ส่วนโค้ง**")
    p1, p2 = st.columns(2)
    with p1:
        mode = st.selectbox("เลือกรูปแบบเพิ่มความคม", [
            "🔤 ตัวหนังสือและลายเส้นคม",
            "🌀 ส่วนโค้งฟอนต์เนียน คมขอบ",
            "🧩 โลโก้และเส้นเล็กคม",
            "📷 ความคมชัดธรรมชาติ",
            "🎨 สีสดงานป้าย",
            "ไม่ปรับความคม",
        ], key="studio_resize_edge_mode_v2")
        sharpen = st.slider("เพิ่มความคมชัด", 0.0, 2.0, 0.6, 0.1,
                            key="studio_resize_edge_strength_v2")
    with p2:
        framing = st.selectbox("วิธีวางภาพใหม่ (รักษารูปทรงเดิม)", [
            "คงสัดส่วนภาพเดิม (ไม่ยืดตัวหนังสือ)",
            "คงภาพครบ • เติมฉากหลังเบลอ",
            "เต็มกรอบแบบครอป (ไม่บิดอักษร)",
            "ยืดให้เต็มกรอบ (อาจทำให้ตัวหนังสือเบี้ยว)",
        ], key="studio_resize_framing_v2")
        smooth = st.slider("ปรับความเนียนของส่วนโค้ง", 0, 3, 1, 1,
                           key="studio_resize_curve_v2",
                           disabled=mode != "🌀 ส่วนโค้งฟอนต์เนียน คมขอบ")

    col_a, col_b = st.columns(2)
    with col_a:
        fmt = st.selectbox("รูปแบบไฟล์", ["PNG", "TIFF"], key="studio_resize_format")
    with col_b:
        cmyk = st.checkbox("ส่งออก TIFF แบบ CMYK (ไม่มี ICC โปรไฟล์เฉพาะเครื่องพิมพ์)",
                           value=False, disabled=(fmt != "TIFF"), key="studio_resize_cmyk")

    placement_c1, placement_c2, placement_c3 = st.columns(3)
    with placement_c1:
        align_x = st.slider("จัดวางซ้าย–ขวา (%)", 0, 100, 50, 5,
                            key="studio_resize_align_x_v4")
    with placement_c2:
        align_y = st.slider("จัดวางบน–ล่าง (%)", 0, 100, 50, 5,
                            key="studio_resize_align_y_v4")
    with placement_c3:
        bg_color = st.color_picker("สีพื้นส่วนที่เติม", "#FFFFFF",
                                   key="studio_resize_bg_color_v4",
                                   disabled=framing != "คงสัดส่วนภาพเดิม (ไม่ยืดตัวหนังสือ)")
    if framing == "ยืดให้เต็มกรอบ (อาจทำให้ตัวหนังสือเบี้ยว)":
        st.error("โหมดนี้ยืดภาพคนและตัวอักษรได้ ไม่แนะนำสำหรับงานที่ต้องรักษาสัดส่วนเดิม")
    elif framing == "เต็มกรอบแบบครอป (ไม่บิดอักษร)":
        st.warning("โหมดครอปไม่บิดภาพ แต่บางส่วนริมภาพจะถูกตัดออก โปรดตรวจชื่อและลายกรอบก่อนพิมพ์")
    elif framing == "คงภาพครบ • เติมฉากหลังเบลอ":
        st.info("ภาพต้นฉบับยังอยู่ครบ ระบบเติมพื้นที่นอกกรอบด้วยสำเนาฉากหลังที่เบลอ ไม่ใช่ AI สร้างส่วนที่ขาด")
    else:
        st.info("คงภาพต้นฉบับทั้งหมดแบบไม่บีบ/ยืด หากอัตราส่วนต่างกันจะมีพื้นที่สีพื้นเพิ่มรอบภาพ")

    if image is not None:
        actual_ratio = image.width / max(1, image.height)
        target_ratio = width_cm / height_cm
        if check_original and abs(actual_ratio / (source_width_cm / source_height_cm) - 1) > .03:
            st.warning(
                "ขนาดต้นฉบับที่กรอกไม่ตรงกับอัตราส่วนพิกเซลของไฟล์ที่อัปโหลด "
                "ระบบจะรักษาสัดส่วนตามภาพจริง ไม่ยืดตามตัวเลขที่กรอก"
            )
        if abs(actual_ratio / target_ratio - 1) > .001:
            if framing in ("คงสัดส่วนภาพเดิม (ไม่ยืดตัวหนังสือ)", "คงภาพครบ • เติมฉากหลังเบลอ"):
                placed_w_cm = min(width_cm, height_cm * actual_ratio)
                placed_h_cm = placed_w_cm / actual_ratio
                st.caption(
                    f"เมื่อใส่รูปครบในป้ายใหม่ ขนาดส่วนภาพประมาณ {placed_w_cm:.1f} × {placed_h_cm:.1f} ซม. "
                    "โดยไม่เสียรูปทรง ส่วนพื้นที่ที่เหลือจะเป็นพื้นเสริมหรือฉากเบลอ"
                )
            elif framing == "เต็มกรอบแบบครอป (ไม่บิดอักษร)":
                lost = ((1 - target_ratio / actual_ratio) * 100
                        if actual_ratio > target_ratio
                        else (1 - actual_ratio / target_ratio) * 100)
                where = "ด้านซ้าย–ขวา" if actual_ratio > target_ratio else "ด้านบน–ล่าง"
                st.caption(f"ต้องครอปพื้นที่ต้นฉบับรวมประมาณ {max(0, lost):.1f}% จาก{where} เพื่อเต็มป้ายใหม่")

    wpx, hpx, effective_dpi = _target_pixels(width_cm, height_cm, dpi)
    st.caption(f"ขนาดส่งออก {wpx:,} × {hpx:,} พิกเซล • DPI ใช้ได้จริงประมาณ {effective_dpi:g}")
    if effective_dpi < dpi:
        st.warning("ขนาดงานเกินกำลังประมวลผลของเว็บ ระบบลดจำนวนพิกเซล/DPI เพื่อป้องกันเว็บค้าง")
    st.caption("ฟอนต์ที่เป็นภาพพิกเซลสามารถปรับขอบให้ดูเรียบขึ้นได้ แต่ไม่ได้กลายเป็นเวกเตอร์หรือแก้คำในภาพด้วยฟอนต์จริง")

    st.markdown("### 🔍 ลากเส้น ↔ ดูภาพก่อน–หลัง (อยู่ในโหมดอัพสเกล)")
    if image is not None:
        st.caption("👇 **ลากปุ่ม ↔ บนเส้นสีขาว** เพื่อเทียบภาพวางแบบเดิมกับการจัดวางใหม่ตามขนาดและวิธีที่เลือก")
        with st.spinner("กำลังประมวลผลภาพก่อน–หลังขนาดพรีวิว..."):
            before_preview, after_preview = _live_resize_comparison(
                image, (wpx, hpx), framing, mode, sharpen, smooth,
                bg_color, align_x, align_y)
        render_quality_preview(
            before_preview, after_preview,
            title="ก่อน ↔ หลัง • ปรับเส้นคมและส่วนโค้งตัวหนังสือ",
            before_label="ก่อน • วางภาพเดิมคงสัดส่วน",
            after_label="หลัง • ปรับขนาด/จัดวางใหม่ไม่บิดรูป",
        )
    else:
        st.info("อัปโหลดภาพด้านบนเพื่อดูพรีวิวก่อน–หลังของงานจริง ระบบจะแสดงเส้นลาก ↔ เมื่อมีภาพแล้ว")

    fingerprint = (hashlib.sha256(up.getvalue()).hexdigest() if up is not None else "")
    settings = (fingerprint, wpx, hpx, effective_dpi, framing, mode, sharpen,
                smooth, fmt, cmyk, bg_color, align_x, align_y)
    if st.button("🚀 สร้างไฟล์อัพสเกล / ปรับคม พร้อมพิมพ์", use_container_width=True,
                 key="studio_resize_generate"):
        if image is None:
            st.error("กรุณาอัปโหลดภาพก่อนสร้างไฟล์")
        else:
            with st.spinner("กำลังขยายภาพและปรับขอบตัวอักษรสำหรับดาวน์โหลด..."):
                out = _resize_print_image(
                    image, (wpx, hpx), framing, Image.Resampling.LANCZOS,
                    bg_color, align_x, align_y)
                out = _apply_print_edge_mode(out, mode, sharpen, smooth)
                binary = _image_bytes(out, fmt, effective_dpi, cmyk)
                st.session_state["studio_resize_result_v2"] = {
                    "data": binary, "format": fmt, "width": wpx, "height": hpx,
                    "settings": settings,
                }
                del out
    result = st.session_state.get("studio_resize_result_v2")
    if result and result.get("settings") == settings:
        st.success(f"สร้างไฟล์แล้ว: {result['width']:,} × {result['height']:,} พิกเซล")
        _download("⬇️ ดาวน์โหลดไฟล์สำหรับงานพิมพ์",
                  result["data"],
                  "thanasilp_resized." + ("tif" if result["format"] == "TIFF" else "png"),
                  "image/tiff" if result["format"] == "TIFF" else "image/png")
    elif result:
        st.caption("มีการเปลี่ยนภาพหรือค่าปรับแต่ง กรุณากดสร้างไฟล์อีกครั้งเพื่อให้ตรงกับพรีวิวล่าสุด")

    st.caption("พรีวิวเป็นการประมวลผลจริงบนภาพย่อ เพื่อให้ลากได้ลื่นไหล ไม่ใช่การซูมไฟล์เต็มความละเอียด • DPI และขนาดพิมพ์จริงใช้ค่าตามไฟล์ที่ดาวน์โหลด")
    st.caption("การขยายภาพไม่สามารถสร้างรายละเอียดที่หายไปจริงด้วย AI และการส่งออก CMYK ควรตรวจโปรไฟล์ ICC กับโรงพิมพ์")


    st.caption("การขยายภาพไม่สามารถสร้างรายละเอียดที่หายไปจริงด้วย AI และการส่งออก CMYK ควรตรวจโปรไฟล์ ICC กับโรงพิมพ์")


def _tool_text():
    st.markdown("#### 2. เพิ่มและแก้ข้อความบนภาพ")
    st.caption("ใส่ข้อความใหม่ พร้อมสี ขอบ เงา และตำแหน่งได้ • การปิดข้อความเดิมใช้สี่เหลี่ยมสีพื้น ไม่ใช่การลบเนียนด้วย AI")
    up = st.file_uploader("อัปโหลดภาพป้าย", type=["jpg", "jpeg", "png"], key="studio_text_upload")
    image = _open_image(up)
    if image is not None:
        st.caption(f"ภาพต้นฉบับ {image.width:,} × {image.height:,} พิกเซล")
    content = st.text_area("ข้อความใหม่ (ภาษาไทยได้)", value="", height=80, key="studio_text_content")
    font_list = _available_thai_fonts()
    font_choice = st.selectbox("เลือกฟอนต์ไทย", list(font_list) or ["อัปโหลดฟอนต์ด้านล่าง"], key="studio_text_font_choice")
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
    st.caption("เส้นขอบโค้งตามรูปทรงจริงของฟอนต์ไทยแต่ละแบบ ไม่บีบ ไม่ยืด ไม่บิดสระวรรณยุกต์ และใช้การลดรอยหยักเพื่อขอบเรียบ")
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
            font = _font(size, font_upload, font_choice)
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
                    _draw_smooth_font_outline(out, content, (x, y), font,
                                               color, stroke, stroke_color, shadow)
                    st.session_state["studio_text_result"] = _image_bytes(out)
                    st.session_state["studio_text_preview"] = _small_preview(out)
                    st.session_state["studio_text_compare"] = prepare_quality_previews(image, out)
    if "studio_text_result" in st.session_state:
        if st.session_state.get("studio_text_compare"):
            before_preview, after_preview = st.session_state["studio_text_compare"]
            render_quality_preview(before_preview, after_preview,
                                   title="ก่อน–หลังแก้ข้อความ • ลากตรวจตัวอักษรและขอบ")
        elif "studio_text_preview" in st.session_state:
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
        bg_index = 0 if im is not None and im.getchannel("A").getextrema()[0] < 255 else 1
        bg_choice = st.selectbox("พื้นหลัง", ["ใช้ความโปร่งใสเดิม", "อัตโนมัติจากมุมซ้ายบน", "ขาว", "ดำ"], index=bg_index, key="studio_sticker_bg")
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
                    # ก่อน/หลังใช้ขนาดผ้าใบเดียวกัน เพื่อให้ลากเส้นตรวจขอบได้ตรงตำแหน่ง
                    sticker_before = Image.new("RGBA", sticker.size, (0, 0, 0, 0))
                    pad = max(6, outline + 6)
                    sticker_before.alpha_composite(base, (pad, pad))
                    before_preview, after_preview = prepare_quality_previews(sticker_before, sticker)
                    st.session_state["studio_sticker_result"] = {
                        "compare": (before_preview, after_preview),
                        "single": _image_bytes(sticker),
                        "guide": _image_bytes(_sticker_guide(sticker)),
                        "sheet": _image_bytes(sheet_img, dpi=actual_dpi),
                        "preview": _small_preview(sheet_img),
                        "count": cols * rows,
                    }
    result = st.session_state.get("studio_sticker_result")
    if result:
        st.success(f"จัดเรียงได้ {result['count']} ชิ้นต่อแผ่น")
        if result.get("compare"):
            render_quality_preview(*result["compare"], title="ก่อน–หลังทำขอบสติกเกอร์ • ซูมตรวจเส้นไดคัท",
                                   before_label="ก่อน • ยังไม่มีขอบ",
                                   after_label="หลัง • ขอบขาว")
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


def _fit_font(text, target_width, desired_size, font_upload, font_choice=None, stroke=0):
    size = max(12, desired_size)
    while size >= 12:
        font = _font(size, font_upload, font_choice)
        if font is None:
            return None
        try:
            span = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)
            if span[2] - span[0] + 2 * stroke <= target_width:
                return font
        except (UnicodeError, OSError):
            return None
        size = int(size * 0.88) if size > 14 else size - 1
    return _font(12, font_upload, font_choice)


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


def _draw_center(draw, text, cx, y, max_width, size, color, font_upload,
                 font_choice=None, stroke=0, stroke_color="#000000"):
    if not text:
        return
    font = _fit_font(text, max_width, size, font_upload, font_choice, stroke)
    if font is None:
        return
    bounds = draw.textbbox((0, 0), text, font=font)
    x = round(cx - (bounds[2] - bounds[0]) / 2)
    # stroke_width follows each font glyph's true curves; never stretch the font.
    draw.text((x, y), text, font=font, fill=color,
              stroke_width=stroke, stroke_fill=stroke_color)


def _make_memorial(photo, name, born_text, died_text, age_label, subtitle,
                   heading, palette, wpx, hpx, font_upload, use_thai,
                   font_choice=None, text_stroke=0, text_stroke_color="#000000"):
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
        text_y = int(hpx * .60)
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
                     x2 - x1 - 24, int(base * .04), ink, font_upload,
                     font_choice, text_stroke, text_stroke_color)
    details = []
    if born_text.strip():
        details.append("ชาตะ " + born_text.strip())
    if died_text.strip():
        details.append("มรณะ " + died_text.strip())
    if age_label:
        details.append("สิริอายุ " + age_label + " ปี")
    if use_thai:
        details = [_thai_digits(v) for v in details]
    line_gap = int(base * (.095 if landscape else .063))
    _draw_center(d, heading, tx, text_y, tw, int(base * .055), ink, font_upload,
                     font_choice, text_stroke, text_stroke_color)
    _draw_center(d, name or "ชื่อผู้วายชนม์", tx, text_y + line_gap, tw,
                 int(base * .075), ink, font_upload,
                     font_choice, text_stroke, text_stroke_color)
    for n, detail in enumerate(details):
        _draw_center(d, detail, tx, text_y + (n + 2) * line_gap,
                     tw, int(base * .039), ink, font_upload,
                     font_choice, text_stroke, text_stroke_color)
    if subtitle.strip():
        _draw_center(d, subtitle.strip(), tx,
                     text_y + (len(details) + 2) * line_gap,
                     tw, int(base * .031), ink, font_upload,
                     font_choice, text_stroke, text_stroke_color)
    return canvas


def _tool_memorial():
    st.markdown("#### 4. ภาพอาลัย / ป้ายงานศพแบบกรอกข้อมูล")
    st.caption("เลือกแบบ ใส่ภาพและชื่อ คำนวณอายุ และแปลงตัวเลขไทย โดยไม่ต้องใช้ AI สร้างตัวสะกด")
    photo_upload = st.file_uploader("อัปโหลดภาพบุคคล (ถ้ามี)", type=["png", "jpg", "jpeg"], key="studio_memorial_upload")
    # กลับสู่หน้าตาเรียบง่าย: เลือกฟอนต์งานวัดโดยอัตโนมัติ ไม่มีแกลเลอรีหรือเมนูเลือกฟอนต์
    font_choice = _auto_temple_font_choice()
    font_upload = None
    st.caption("ฟอนต์ไทยแนวงานวัดสุภาพ — ระบบเลือกอัตโนมัติให้เหมาะกับป้ายอาลัย")
    mem_c1, mem_c2 = st.columns(2)
    with mem_c1:
        text_stroke = st.slider("ความหนาเส้นขอบตัวหนังสือ (px)", 0, 12, 1, key="studio_memorial_stroke")
    with mem_c2:
        text_stroke_color = st.color_picker("สีขอบตัวหนังสือ", "#FFFFFF", key="studio_memorial_stroke_color")
    st.caption("ขอบเดินตามรูปทรงจริงของฟอนต์ไทย รวมถึงส่วนโค้งและวรรณยุกต์ ไม่บิดหรือยืดตัวอักษร")
    if not font_choice and not _system_thai_font():
        st.warning("ไม่พบฟอนต์ไทยบนเซิร์ฟเวอร์ กรุณาตรวจสอบการติดตั้ง fonts-thai-tlwg")
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
        elif _font(40, font_upload, font_choice) is None:
            st.error("เซิร์ฟเวอร์ยังไม่มีฟอนต์ไทยสำหรับป้ายอาลัย กรุณาตรวจการติดตั้งฟอนต์")
        else:
            photo = _open_image(photo_upload)
            with st.spinner("กำลังจัดองค์ประกอบป้าย..."):
                poster = _make_memorial(photo, name, born, died, age, subtitle,
                                        heading, template, wpx, hpx, font_upload, use_thai,
                                        font_choice, text_stroke, text_stroke_color)
                st.session_state["studio_memorial_result"] = _image_bytes(poster, dpi=effective_dpi)
                st.session_state["studio_memorial_preview"] = _small_preview(poster)
                st.session_state["studio_memorial_zoom"] = prepare_quality_previews(None, poster)[1]
    if "studio_memorial_result" in st.session_state:
        if st.session_state.get("studio_memorial_zoom"):
            render_quality_preview(None, st.session_state["studio_memorial_zoom"],
                                   title="ซูมตรวจชื่อ สระ วรรณยุกต์ และรายละเอียดป้ายอาลัย",
                                   after_label="ป้ายอาลัยที่สร้าง")
        else:
            _preview(st.session_state["studio_memorial_preview"], "ตัวอย่างป้ายล่าสุด")
        _download("⬇️ ดาวน์โหลดป้ายอาลัย PNG",
                  st.session_state["studio_memorial_result"], "thanasilp_memorial.png", "image/png")
    st.caption("โปรดตรวจสะกดชื่อ วันเดือนปี และรูปภาพก่อนพิมพ์จริง ภาพที่ส่งเข้าระบบออนไลน์จะถูกประมวลผลในเซิร์ฟเวอร์ ไม่ใช่ออฟไลน์")


def _tool_quality_comparison():
    st.markdown("#### 🔍 ลากเส้นกลางภาพ ดูความคมชัดก่อน–หลัง")
    st.caption("อัปโหลดภาพก่อนแก้และหลังแก้เพื่อใช้เส้น ↔ ลากเทียบความคมชัดจริง ซูมได้ 100–1200%")
    st.markdown("**📷 เปรียบเทียบภาพงานของคุณ**")
    st.caption("อัปโหลดภาพต้นฉบับและภาพที่ปรับแล้ว 2 ไฟล์ จะมีเส้นลากแสดงใต้ช่องอัปโหลด")
    col_before, col_after = st.columns(2)
    with col_before:
        before_up = st.file_uploader(
            "ภาพก่อนแก้ (ก่อน)", type=["jpg", "jpeg", "png", "webp", "tif", "tiff"],
            key="studio_compare_before")
    with col_after:
        after_up = st.file_uploader(
            "ภาพหลังแก้ (หลัง)", type=["jpg", "jpeg", "png", "webp", "tif", "tiff"],
            key="studio_compare_after")
    if before_up and after_up:
        before_image = _open_image(before_up)
        after_image = _open_image(after_up)
        if before_image is not None and after_image is not None:
            st.caption(
                f"ก่อน {before_image.width:,} × {before_image.height:,} px"
                f" • หลัง {after_image.width:,} × {after_image.height:,} px"
            )
            a = before_image.width / max(1, before_image.height)
            b = after_image.width / max(1, after_image.height)
            if abs(a / b - 1) > .035:
                st.warning(
                    "ภาพสองไฟล์มีอัตราส่วนต่างกัน พรีวิวจะยืดภาพก่อนให้ตรงกับภาพหลัง "
                    "เส้นแบ่งจึงอาจไม่ทับตำแหน่งเดิมพอดี"
                )
            render_quality_from_images(before_image, after_image,
                                       title="ลากดูความแตกต่างและซูมตรวจคุณภาพ")
    else:
        st.info("เลือกภาพก่อนและหลังทั้งสองไฟล์ แล้วจะเห็นเส้นแบ่งลากซ้าย–ขวาทันที")
    st.caption("พรีวิวเพื่อเปรียบเทียบภาพ ไม่ใช่การประมวลผลเพิ่มความคมชัดหรือเพิ่มพิกเซลของไฟล์ต้นฉบับ")



def render_print_studio():
    """แสดงเครื่องมือแก้ภาพและพรีวิวแบบลาก รวมกับ 4 เครื่องมือเดิม"""
    st.markdown("### 🖨️ ธนศิลป์ Print Studio")
    st.caption("แก้ข้อความบนภาพแบบคลิก/ลากได้จริง พร้อมเครื่องมือขยายภาพและเตรียมงานพิมพ์เดิม")
    st.info("ภาพอัปโหลดจะผ่านเซิร์ฟเวอร์ของเว็บก่อนเปิดตัวแก้ไข กรุณาได้รับอนุญาตก่อนใช้งานภาพบุคคล")
    st.markdown("**👇 เลือกหมวดขยายภาพ / DPI เพื่อเลือกรูปแบบปรับความคมและลากเส้นก่อน–หลังได้ทันที**")
    mode = st.radio(
        "เลือกเครื่องมือในสตูดิโองานพิมพ์",
        [
            "🔎 1. อัพสเกลภาพ / DPI • ปรับคมและลากก่อน–หลัง",
            "🔍 เปรียบเทียบภาพก่อน–หลังจากสองไฟล์",
            "🖱️ แก้ข้อความบนภาพแบบคลิก / ลาก",
            "✏️ 2. แก้ข้อความบนภาพ (แบบเดิม)",
            "✂️ 3. สติกเกอร์ไดคัท",
            "🕯️ 4. ป้ายงานศพ / ภาพอาลัย",
        ],
        key="studio_mode_resize_first_v3",
        horizontal=False,
        label_visibility="collapsed",
    )
    st.divider()
    if mode.startswith("🖱️"):
        try:
            from interactive_sign_editor import render_interactive_editor
            render_interactive_editor()
        except (ImportError, AttributeError, OSError) as exc:
            st.error("ยังเปิดเครื่องมือแก้ข้อความแบบลากไม่ได้ กรุณาใช้โหมดแก้ข้อความแบบเดิมหรือพรีวิวก่อน–หลังชั่วคราว")
            st.caption("ระบบหลักและเครื่องมืออื่นยังใช้งานได้ตามปกติ")
    elif mode.startswith("🔍"):
        _tool_quality_comparison()
    elif mode.startswith("🔎"):
        _tool_resize()
    elif mode.startswith("✏️"):
        _tool_text()
    elif mode.startswith("✂️"):
        _tool_sticker()
    else:
        _tool_memorial()
