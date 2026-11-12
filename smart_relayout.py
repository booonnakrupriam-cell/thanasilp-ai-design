"""Safe composition for print signs from flattened images.

No horizontal cutting, split strips, object distortion, or automatic claims
that a flattened JPG/PNG can be semantically rearranged without AI.
"""
from __future__ import annotations

import hashlib
import math
from io import BytesIO
from urllib.parse import quote

import streamlit as st
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from print_preview import prepare_quality_previews, render_quality_preview

MAX_OUTPUT_PIXELS = 18_000_000


def _pixel_dimensions(width_cm: float, height_cm: float, dpi: int):
    w = max(1, round(width_cm / 2.54 * dpi))
    h = max(1, round(height_cm / 2.54 * dpi))
    actual_dpi = float(dpi)
    if w * h > MAX_OUTPUT_PIXELS:
        factor = math.sqrt(MAX_OUTPUT_PIXELS / (w * h))
        w, h = max(1, int(w * factor)), max(1, int(h * factor))
        actual_dpi *= factor
    return w, h, round(actual_dpi, 2)


def _background(source: Image.Image, size: tuple[int, int], style: str, color: str):
    w, h = size
    if style == "สีพื้นเลือกเอง":
        return Image.new("RGBA", size, color)

    rgb = source.convert("RGB")
    if style == "ฉากหลังเบลอจากภาพต้นฉบับ":
        # Only the background is expanded; foreground remains in ONE piece.
        factor = min(1.0, 720 / max(1, w), 720 / max(1, h))
        preview_size = (max(1, round(w * factor)), max(1, round(h * factor)))
        back = ImageOps.fit(rgb, preview_size, method=Image.Resampling.BILINEAR)
        back = back.filter(ImageFilter.GaussianBlur(max(8, min(preview_size) / 15)))
        back = ImageEnhance.Brightness(back).enhance(.78)
        return back.resize(size, Image.Resampling.BILINEAR).convert("RGBA")

    # A smooth background derived from the edge colors avoids white bars.
    sample = rgb.copy()
    sample.thumbnail((360, 360), Image.Resampling.BILINEAR)
    sw, sh = sample.size
    band = max(1, sh // 18)
    top_rgb = sample.crop((0, 0, sw, band)).resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    bottom_rgb = sample.crop((0, sh - band, sw, sh)).resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    result = Image.new("RGBA", size, top_rgb + (255,))
    d = ImageDraw.Draw(result)
    for y in range(h):
        frac = y / max(1, h - 1)
        rgb_row = tuple(int(round(top_rgb[i] * (1 - frac) + bottom_rgb[i] * frac)) for i in range(3))
        d.line((0, y, w, y), fill=rgb_row + (255,))
    return result


def _compose_whole_image(source: Image.Image, size: tuple[int, int],
                         style: str, color: str,
                         scale: int = 100, x: int = 50, y: int = 50):
    """Keep every source pixel together and use ONE isotropic scale factor."""
    canvas = _background(source, size, style, color)
    width, height = size
    scale = max(25, min(100, int(scale)))
    area = (max(1, int(width * scale / 100)),
            max(1, int(height * scale / 100)))
    foreground = ImageOps.contain(source.convert("RGBA"), area, method=Image.Resampling.LANCZOS)
    px = round((width - foreground.width) * max(0, min(100, int(x))) / 100)
    py = round((height - foreground.height) * max(0, min(100, int(y))) / 100)
    canvas.alpha_composite(foreground, (px, py))
    return canvas


def _compose_full_bleed(source: Image.Image, size: tuple[int, int],
                        x: int = 50, y: int = 50):
    """Cover the entire canvas by isotropic scaling and cropping only.

    Preserves circle/face/glyph proportions but may cut away edge content.
    """
    result = ImageOps.fit(
        source.convert("RGBA"), size, method=Image.Resampling.LANCZOS,
        centering=(max(0, min(100, x)) / 100, max(0, min(100, y)) / 100))
    return result


def _make_file(image: Image.Image, fmt: str, dpi: float, cmyk: bool):
    result = BytesIO()
    if fmt == "TIFF":
        image.convert("CMYK" if cmyk else "RGB").save(
            result, format="TIFF", compression="tiff_lzw", dpi=(dpi, dpi))
    else:
        image.save(result, format="PNG", dpi=(dpi, dpi))
    return result.getvalue()


def _ai_rebuild_prompt(w_cm: float, h_cm: float, verified_text: str, details: str):
    text_rule = (
        "ข้อความที่ยืนยันจากผู้ใช้ (ต้องเขียนตามนี้เท่านั้น): " + verified_text.strip()
        if verified_text.strip()
        else "คงข้อความต้นฉบับ แต่ถ้ามีข้อความอ่านไม่ชัดต้องสอบถาม ห้ามเดาหรือเปลี่ยนคำ"
    )
    return (
        f"โปรดสร้างภาพป้ายใหม่โดยใช้ภาพต้นฉบับที่แนบเป็นภาพอ้างอิง "
        f"ขนาดงานใหม่ {w_cm:g} × {h_cm:g} ซม. "
        "ต้องออกแบบและจัดองค์ประกอบใหม่ทั้งภาพจริง (full re-composition) "
        "ไม่ใช่ตัดภาพเป็นแถบ ไม่ใช่เว้นช่องว่างระหว่างชิ้น ไม่ใช่ครอป/บีบ/ยืดภาพทั้งผืน "
        "ไม่ใช่แค่เติมขอบขาวหรือพื้นหลังเบลอ ให้สร้างพื้นหลังและขยายลายตกแต่งใหม่ "
        "ให้ครอบคลุมพื้นที่ทั้งหมดอย่างเป็นเนื้อเดียวกัน จัดวางบุคคล ภาพถ่ายย่อย "
        "ข้อความ กรอบภาพ โลโก้ หัวใจ วงกลม และดอกไม้ใหม่โดยรักษาสัดส่วนแต่ละชิ้น "
        "วงกลมต้องกลมไม่เป็นวงรี รูปคนไม่ผิดสัดส่วน รักษาใบหน้าจากภาพต้นฉบับ "
        "รูปถ่ายทุกภาพไม่ถูกตัดกลางตัว หัวใจและข้อความต้องไม่ถูกแบ่งเป็นท่อน "
        "กรอบและลวดลายเชื่อมต่ออย่างสวยงาม ไม่ปรากฏรอยต่อเป็นแถบหรือพื้นที่ว่างคั่น "
        "รักษาสไตล์ สี อารมณ์ และรายละเอียดสำคัญของภาพต้นฉบับ "
        "ฟอนต์ไทยคมชัด มีหัว/ไม่มีหัวตามลักษณะเดิม สระวรรณยุกต์ถูกต้อง "
        "ตรวจข้อความและวันที่อย่างเคร่งครัด ห้ามแต่งเติมหรือสะกดชื่อเอง "
        "ภาพสุดท้ายต้องสมบูรณ์เต็มพื้นที่ ดูเป็นงานป้ายออกแบบใหม่พร้อมตรวจงานพิมพ์ "
        + text_rule + " "
        + ("ข้อกำหนดเพิ่มเติม: " + details.strip() if details.strip() else "")
    )


def _render_ai_rebuild(w_cm: float, h_cm: float):
    st.info("วิธีนี้ตรงกับงานที่ต้องการเปลี่ยนอัตราส่วนและสร้างองค์ประกอบใหม่เต็มป้าย "
            "แต่เว็บไซต์ยังไม่ได้เชื่อม AI สร้างภาพโดยตรง: ระบบจะเตรียมพรอมป์ให้ส่งไปพร้อมภาพต้นฉบับ")
    checked_text = st.text_area(
        "ข้อความที่ต้องรักษาให้ตรง (แนะนำให้พิมพ์ข้อความต้นฉบับ)",
        key="smart_verified_text_v2", height=105,
        placeholder="ชื่อบุคคล / ชื่องาน / วันที่ / หน่วยงาน / ข้อความทั้งหมด")
    more = st.text_area(
        "รายละเอียดเพิ่มเติม", key="smart_ai_details_v2", height=90,
        placeholder="เช่น ย้ายรูปคนไว้ซ้าย กรอบหัวใจไว้ขวา เก็บภาพถ่ายย่อยครบ")
    prompt = _ai_rebuild_prompt(w_cm, h_cm, checked_text, more)
    st.markdown("**📋 คัดลอกคำสั่งนี้ พร้อมแนบภาพต้นฉบับที่ยังไม่ถูกตัดให้ AI**")
    st.code(prompt, language=None, wrap_lines=True)
    st.link_button("🚀 เปิด ChatGPT พร้อมคำสั่ง", "https://chatgpt.com/?q=" + quote(prompt, safe=""),
                   use_container_width=True)
    first, second = st.columns(2)
    with first:
        st.link_button("✨ เปิด Gemini", "https://gemini.google.com/app", use_container_width=True)
    with second:
        st.link_button("🌐 เปิด Meta AI", "https://www.meta.ai/", use_container_width=True)
    st.caption("หากลิงก์ ChatGPT ไม่แสดงคำสั่ง ให้วางจากกล่องด้านบนเอง "
               "และแนบภาพต้นฉบับด้วยทุกครั้ง ผลงาน AI ต้องตรวจใบหน้า วงกลม และตัวสะกดก่อนพิมพ์")


def render_smart_relayout(source: Image.Image | None):
    st.markdown("### 🧩 ปรับขนาดป้ายแบบไม่ตัดภาพเป็นแถบ")
    st.caption("แก้ปัญหาภาพคน กรอบหัวใจ และตัวหนังสือถูกแบ่งเป็นท่อน • ปิดวิธีตัดแถบแบบเดิมแล้ว")
    mode = st.radio(
        "เลือกวิธีจัดภาพใหม่",
        [
            "🖼️ รักษาภาพครบทั้งผืน • ไม่ตัด ไม่ยืด (มีพื้นหลังเสริม)",
            "📐 เต็มขอบ ไม่มีพื้นที่เสริม • ครอปขอบภาพบางส่วน",
            "✨ ให้ AI ออกแบบใหม่ทั้งภาพ • จัดองค์ประกอบใหม่จริง",
        ],
        key="smart_method_safe_v2",
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        width_cm = st.number_input("กว้างใหม่ (ซม.)", 10.0, 600.0, 100.0,
                                   step=10.0, key="smart_width")
    with c2:
        height_cm = st.number_input("สูงใหม่ (ซม.)", 10.0, 600.0, 200.0,
                                    step=10.0, key="smart_height")
    with c3:
        requested_dpi = st.number_input("DPI ที่ต้องการ", 30, 600, 150,
                                        step=10, key="smart_dpi")
    width_px, height_px, actual_dpi = _pixel_dimensions(width_cm, height_cm, requested_dpi)
    st.caption(f"ขนาดไฟล์ส่งออก {width_px:,} × {height_px:,} พิกเซล • DPI จริงประมาณ {actual_dpi:g}")
    if actual_dpi < requested_dpi:
        st.warning("ขนาดที่ขอใหญ่เกินข้อจำกัดของเว็บ ระบบลด DPI จริงเพื่อป้องกันเว็บค้าง")

    if mode.startswith("✨"):
        _render_ai_rebuild(width_cm, height_cm)
        return

    full_bleed = mode.startswith("📐")
    if full_bleed:
        st.warning("โหมดเต็มขอบ: ไม่มีแถบขาวหรือเทา และไม่บีบวงกลม/ใบหน้า "
                   "**แต่จะครอปขอบบางส่วน** เพื่อให้ภาพเต็มพื้นที่เมื่ออัตราส่วนต่างกัน "
                   "โปรดตรวจว่ารูปคน ตัวหนังสือ และโลโก้ไม่ถูกครอปก่อนพิมพ์")
    else:
        st.info("โหมดคงภาพครบ: ไม่ตัดหรือบิดรูปทรงเดิม "
                "แต่เมื่ออัตราส่วนต่างกัน จะต้องมีพื้นหลังเสริมด้านข้างหรือบน–ล่าง "
                "ถ้าต้องการเต็มพื้นที่และรักษาทุกอย่างครบ ให้เลือกโหมด AI")
    if source is None:
        st.info("อัปโหลดภาพ **ต้นฉบับก่อนถูกแบ่งเป็นแถบ** ในช่องด้านบนเพื่อใช้งาน")
        return
    if source.width * source.height > 35_000_000:
        st.error("ภาพต้นฉบับใหญ่เกิน 35 ล้านพิกเซล กรุณาลดขนาดก่อน")
        return

    source_ratio = source.width / source.height
    target_ratio = width_cm / height_cm
    if abs(source_ratio / target_ratio - 1) > .025:
        st.caption(f"อัตราส่วนต้นฉบับ {source_ratio:.3f}:1 และป้ายใหม่ {target_ratio:.3f}:1 ต่างกัน "
                   "จึงไม่สามารถทั้งคงภาพครบ ไม่มีพื้นที่เสริม และไม่บิดรูป ได้พร้อมกันด้วยการย่อ–ขยายธรรมดา")
        if full_bleed:
            crop_fraction = (1 - target_ratio / source_ratio
                             if source_ratio > target_ratio
                             else 1 - source_ratio / target_ratio)
            crop_axis = "ซ้าย–ขวา" if source_ratio > target_ratio else "บน–ล่าง"
            st.warning(f"ขนาดนี้ต้องครอปภาพต้นฉบับรวมประมาณ {crop_fraction * 100:.1f}% "
                       f"ของแนว{crop_axis} หากข้อความหรือคนอยู่บริเวณขอบ อาจถูกตัด! "
                       "หากต้องเก็บองค์ประกอบครบเต็มขอบ แนะนำเลือกให้ AI ออกแบบใหม่ทั้งภาพ")

    background, bg_color, scale = "ไล่สีจากขอบภาพ", "#F1EEE8", 100
    if full_bleed:
        st.caption("เลื่อนจุดครอปเพื่อให้สิ่งสำคัญอยู่กลางงาน วัตถุทุกชิ้นยังคงสัดส่วนเดิม")
        x1, x2 = st.columns(2)
        with x1:
            pos_x = st.slider("จุดครอปซ้าย–ขวา (%)", 0, 100, 50, 5,
                              key="smart_crop_pos_x_v3")
        with x2:
            pos_y = st.slider("จุดครอปบน–ล่าง (%)", 0, 100, 50, 5,
                              key="smart_crop_pos_y_v3")
    else:
        background = st.selectbox(
            "พื้นหลังสำหรับพื้นที่ที่เพิ่ม",
            ["ไล่สีจากขอบภาพ", "ฉากหลังเบลอจากภาพต้นฉบับ", "สีพื้นเลือกเอง"],
            key="smart_background_v2")
        bg_color = st.color_picker("สีพื้น", "#F1EEE8", key="smart_bg_color_v2",
                                   disabled=background != "สีพื้นเลือกเอง")
        x1, x2, x3 = st.columns(3)
        with x1:
            scale = st.slider("ขนาดส่วนภาพหลัก (%)", 25, 100, 100, 5,
                              key="smart_scale_v2")
        with x2:
            pos_x = st.slider("ตำแหน่งซ้าย–ขวา (%)", 0, 100, 50, 5,
                              key="smart_pos_x_v2")
        with x3:
            pos_y = st.slider("ตำแหน่งบน–ล่าง (%)", 0, 100, 50, 5,
                              key="smart_pos_y_v2")

    ratio = min(1.0, 1100 / max(1, width_px), 1100 / max(1, height_px),
                math.sqrt(1_600_000 / max(1, width_px * height_px)))
    size_preview = (max(1, int(width_px * ratio)), max(1, int(height_px * ratio)))
    with st.spinner("กำลังสร้างพรีวิวแบบภาพต่อเนื่อง..."):
        before = _compose_whole_image(
            source, size_preview, "สีพื้นเลือกเอง", "#F0F1F4", 100, 50, 50)
        after = (_compose_full_bleed(source, size_preview, pos_x, pos_y)
                 if full_bleed else
                 _compose_whole_image(source, size_preview, background, bg_color,
                                      scale, pos_x, pos_y))
        before_jpg, after_jpg = prepare_quality_previews(before, after)

    st.markdown("#### 🔍 ลากเปรียบเทียบก่อน–หลัง")
    render_quality_preview(before_jpg, after_jpg,
                           title="ภาพต้นฉบับครบทั้งผืน ↔ ภาพจัดลงขนาดใหม่",
                           before_label="ก่อน • ภาพต้นฉบับครบ",
                           after_label=("หลัง • เต็มขอบแบบครอป" if full_bleed
                                        else "หลัง • คงภาพครบ ไม่แยกเป็นแถบ"))
    st.caption("ภาพตัวอย่างใช้ไฟล์ย่อเพื่อดูตำแหน่ง การดาวน์โหลดจะใช้ขนาดพิกเซลที่ระบุด้านบน")

    fmt = st.selectbox("ไฟล์ส่งออก", ["PNG", "TIFF"], key="smart_format_v2")
    cmyk = st.checkbox("TIFF แบบ CMYK เบื้องต้น (ไม่มีโปรไฟล์ ICC โรงพิมพ์)",
                       value=False, disabled=fmt != "TIFF", key="smart_cmyk_v2")
    stamp = hashlib.sha256(source.resize((48, 48), Image.Resampling.BILINEAR).tobytes()).hexdigest()
    settings = (stamp, width_px, height_px, actual_dpi, full_bleed,
                background, bg_color, scale, pos_x, pos_y, fmt, cmyk)

    if st.button(("🖨️ สร้างไฟล์เต็มขอบ (มีครอป)" if full_bleed
                  else "🖨️ สร้างไฟล์ภาพครบ ไม่ตัดเป็นแถบ"),
                 type="primary", use_container_width=True, key="smart_make_safe_v2"):
        with st.spinner("กำลังทำไฟล์พร้อมพิมพ์..."):
            final = (_compose_full_bleed(source, (width_px, height_px), pos_x, pos_y)
                     if full_bleed else
                     _compose_whole_image(source, (width_px, height_px),
                                          background, bg_color, scale, pos_x, pos_y))
            binary = _make_file(final, fmt, actual_dpi, cmyk)
            st.session_state["smart_safe_output_v2"] = (settings, binary)

    result = st.session_state.get("smart_safe_output_v2")
    if result:
        old_settings, data = result
        if old_settings == settings:
            st.download_button(
                "⬇️ ดาวน์โหลดงาน " + fmt, data=data,
                file_name=("thanasilp_full_bleed" if full_bleed else "thanasilp_no_cut")
                          + ("." + ("tif" if fmt == "TIFF" else "png")),
                mime="image/tiff" if fmt == "TIFF" else "image/png",
                use_container_width=True)
        else:
            st.caption("ค่าปรับเปลี่ยนไปจากไฟล์ล่าสุด กรุณากดสร้างไฟล์ใหม่")
