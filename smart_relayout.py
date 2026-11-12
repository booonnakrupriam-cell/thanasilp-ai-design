"""Thanasilp: honest, non-distorting raster-block re-layout and AI rebuild handoff.

The input is a FLATTENED raster. Grouped horizontal strips can be arranged
without distorting glyphs or round objects, but cannot semantically isolate
text, people or decorative objects. The UI makes this distinction explicit.
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
    actual = float(dpi)
    if w * h > MAX_OUTPUT_PIXELS:
        reduction = math.sqrt(MAX_OUTPUT_PIXELS / (w * h))
        w, h = max(1, int(w * reduction)), max(1, int(h * reduction))
        actual *= reduction
    return w, h, round(actual, 2)


def _suggest_cuts(image: Image.Image, parts: int):
    """Look for relatively quiet horizontal lines near equal-height splits."""
    reduced = image.convert("RGB")
    reduced.thumbnail((460, 720), Image.Resampling.BILINEAR)
    gray = ImageOps.grayscale(reduced).filter(ImageFilter.FIND_EDGES)
    w, h = gray.size
    row_energy = [sum(gray.crop((0, y, w, y + 1)).getdata()) / w for y in range(h)]
    result = []
    for index in range(1, parts):
        center = round(h * index / parts)
        margin = max(2, round(h * .055))
        lo = max(2, center - margin)
        hi = min(h - 2, center + margin)
        best = min(range(lo, hi + 1), key=lambda y: row_energy[y])
        result.append(best / h)
    return result


def _background(source: Image.Image, size: tuple[int, int], style: str, color: str):
    if style == "สีพื้นเลือกเอง":
        return Image.new("RGBA", size, color)
    if style == "สีเฉลี่ยจากภาพต้นฉบับ":
        im = source.convert("RGB").resize((1, 1), Image.Resampling.BOX)
        return Image.new("RGBA", size, im.getpixel((0, 0)) + (255,))
    # A blurred copy fills the new canvas without white margins.
    sw, sh = size
    factor = min(1.0, 850 / sw, 850 / sh)
    small = (max(1, round(sw * factor)), max(1, round(sh * factor)))
    back = ImageOps.fit(source.convert("RGB"), small, method=Image.Resampling.BILINEAR)
    back = back.filter(ImageFilter.GaussianBlur(max(8, min(small) // 18)))
    back = ImageEnhance.Brightness(back).enhance(0.72)
    return back.resize(size, Image.Resampling.BILINEAR).convert("RGBA")


def _safe_contain(source, size, background, color):
    out = _background(source, size, background, color)
    fitted = ImageOps.contain(source.convert("RGBA"), size, method=Image.Resampling.LANCZOS)
    out.alpha_composite(fitted, ((size[0] - fitted.width) // 2,
                                 (size[1] - fitted.height) // 2))
    return out


def relayout_bands(source: Image.Image, size: tuple[int, int], cuts: list[float],
                   background: str, color: str, spacing: int = 100,
                   top_offset: int = 50, margin_pct: int = 2):
    """Uniformly scale separate horizontal regions, then redistribute them.

    A circular ornament fully inside any band stays circular; if a cut crosses
    an ornament or glyph, that ornament will be split. User can adjust cuts.
    """
    sw, sh = source.size
    tw, th = size
    norm = sorted({max(.02, min(.98, float(v))) for v in cuts})
    bounds = [0] + [min(sh - 1, max(1, round(v * sh))) for v in norm] + [sh]
    bounds = list(dict.fromkeys(bounds))
    if len(bounds) < 2:
        return _safe_contain(source, size, background, color)
    margin = max(0, int(tw * margin_pct / 100))
    scale = min((tw - 2 * margin) / sw, (th - 2 * margin) / sh) * .99
    resized = []
    for y1, y2 in zip(bounds[:-1], bounds[1:]):
        if y2 <= y1:
            continue
        region = source.crop((0, y1, sw, y2)).convert("RGBA")
        resized.append(region.resize((max(1, int(sw * scale)),
                                      max(1, int((y2 - y1) * scale))),
                                     Image.Resampling.LANCZOS))
    out = _background(source, size, background, color)
    if not resized:
        return out
    used = sum(img.height for img in resized)
    remain = max(0, th - used)
    # spacing=0: gaps around outer edges; 100: distribute into inner gaps.
    internal = remain * spacing / 100
    outer = remain - internal
    start_y = int(outer * top_offset / 100)
    gap = internal / max(1, len(resized) - 1) if len(resized) > 1 else 0
    y = float(start_y)
    for index, obj in enumerate(resized):
        x = (tw - obj.width) // 2
        out.alpha_composite(obj, (x, int(round(y))))
        y += obj.height + gap
    return out


def _png_or_tiff(image, fmt, dpi, cmyk):
    buf = BytesIO()
    if fmt == "TIFF":
        image.convert("CMYK" if cmyk else "RGB").save(
            buf, format="TIFF", compression="tiff_lzw", dpi=(dpi, dpi))
    else:
        image.save(buf, format="PNG", dpi=(dpi, dpi))
    return buf.getvalue()


def _ai_prompt(width_cm, height_cm, additional):
    return (f"สร้างแบบป้ายใหม่จากภาพตัวอย่างที่แนบมา ให้มีขนาด {width_cm:g} × "
            f"{height_cm:g} เซนติเมตร โดยจัดองค์ประกอบใหม่ทุกส่วนตามต้นฉบับ "
            " (true redesign / smart re-layout) ไม่ใช่การยืดภาพ ไม่ใช่การครอป "
            "และไม่ใช่การเติมกรอบขาวรอบภาพ ให้จัดวางพื้นหลัง ลายไทย รูปคน "
            "โลโก้ กรอบข้อความ และเครื่องประดับให้เหมาะกับสัดส่วนป้ายใหม่อย่างสมดุล "
            "วงกลมทุกวงต้องยังเป็นวงกลม วัตถุไม่เสียสัดส่วน รูปคนคงใบหน้าจริง "
            "จัดข้อความใหม่ด้วยตัวอักษรไทยที่ถูกต้อง สระ วรรณยุกต์ไม่ทับกัน "
            "ขอบอักษรและเส้นโค้งเรียบคม รักษาคำ ชื่อ วันที่ เบอร์โทร เลขไทย "
            "และเจตนาของข้อความต้นฉบับอย่างเคร่งครัด ไม่แต่งข้อความใหม่เอง "
            "คงโทนสี อัตลักษณ์และลวดลายสำคัญของต้นฉบับ พร้อมงานพิมพ์ "
            "หากอ่านข้อความต้นฉบับไม่ชัดให้ถามเพื่อยืนยัน ห้ามเดา "
            f"รายละเอียดเพิ่มเติม: {additional.strip() or 'ไม่มี'}")


def render_smart_relayout(source: Image.Image | None):
    st.markdown("### 🧩 จัดองค์ประกอบใหม่โดยไม่ทำให้รูปทรงเบี้ยว")
    st.caption("ตัวอย่าง 150×200 → 100×200 ซม.: ลดขนาดองค์ประกอบเป็นส่วน ๆ และกระจายตำแหน่งใหม่แทนการยืดภาพ")
    option = st.radio(
        "เลือกวิธีสร้างงานใหม่",
        ["🧩 จัดบล็อกภาพใหม่ (ทำได้ทันทีบนเว็บ)",
         "✨ สร้างใหม่ทั้งงานด้วย AI (รักษาคน โลโก้ วงกลม และข้อความ)"],
        key="smart_method", horizontal=False)
    a, b, c = st.columns(3)
    with a:
        width_cm = st.number_input("กว้างใหม่ (ซม.)", 10., 600., 100., step=10., key="smart_width")
    with b:
        height_cm = st.number_input("สูงใหม่ (ซม.)", 10., 600., 200., step=10., key="smart_height")
    with c:
        dpi = st.number_input("DPI เป้าหมาย", 30, 600, 150, step=10, key="smart_dpi")
    wpx, hpx, dpi_effective = _pixel_dimensions(width_cm, height_cm, dpi)
    st.caption(f"ไฟล์จริงที่สร้างได้: {wpx:,} × {hpx:,} พิกเซล (DPI ประมาณ {dpi_effective:g})")
    if dpi_effective < dpi:
        st.warning("เกินขีดจำกัดหน่วยความจำของเว็บ จึงลดพิกเซล/DPI ที่สร้างจริงให้เหมาะสม")
    if option.startswith("✨"):
        st.info("การสร้างใหม่ทั้งงานให้เข้าใจข้อความ วงกลม รูปคนและลายกรอบอย่างถูกต้อง "
                "ต้องให้ AI สร้างภาพใหม่จากต้นฉบับ เว็บไซต์นี้ยังไม่มี AI สร้างภาพอัตโนมัติในตัว")
        details = st.text_area("รายละเอียดเพิ่มเติม / สิ่งที่ต้องคงเดิม", key="smart_ai_details",
                               placeholder="เช่น เก็บข้อความและรูปคนครบ ย้ายรูปไปด้านขวา ไม่เพิ่มขอบขาว")
        prompt = _ai_prompt(width_cm, height_cm, details)
        st.text_area("คำสั่งสร้างใหม่จากภาพแนบ (คัดลอกได้)", value=prompt,
                     height=220, key=f"smart_ai_prompt_{width_cm:g}_{height_cm:g}_{hash(details)}")
        st.link_button("🚀 เปิด ChatGPT เพื่อสร้างภาพใหม่", "https://chatgpt.com/?q=" + quote(prompt, safe=""), use_container_width=True)
        ai_left, ai_right = st.columns(2)
        with ai_left:
            st.link_button("✨ เปิด Gemini", "https://gemini.google.com/app", use_container_width=True)
        with ai_right:
            st.link_button("🌐 เปิด Meta AI", "https://www.meta.ai/", use_container_width=True)
        st.caption("ต้องแนบภาพต้นฉบับเข้าแชท AI ด้วย เว็บไซต์ไม่สามารถส่งไฟล์ที่อัปโหลดไปโดยอัตโนมัติ "
                   "สำหรับ Gemini และ Meta AI ให้คัดลอกข้อความด้านบนไปวางในแชท")
        return

    st.info("โหมดนี้จัดส่วนภาพเป็นบล็อกใหม่จริง ไม่ใช่เพิ่มกรอบขาว แต่ไม่สามารถแยกข้อความ/คน/วงกลมทุกชิ้นจากรูป JPG/PNG ที่รวมชั้นแล้วได้อย่างสมบูรณ์ "
            "ควรตรวจจุดแบ่งบล็อกไม่ให้ผ่านหน้าคน ตัวอักษร หรือวงกลม")
    if source is None:
        st.info("อัปโหลดภาพในช่องด้านบนก่อน แล้วจะเห็นการจัดวางอัตโนมัติพร้อมพรีวิวลากก่อน–หลัง")
        return
    if source.width * source.height > 35_000_000:
        st.error("ไฟล์ต้นฉบับใหญ่เกิน 35 ล้านพิกเซล กรุณาลดขนาดก่อน")
        return
    count = st.slider("จำนวนบล็อกแนวนอน", 2, 6, 3, key="smart_blocks")
    background = st.selectbox("พื้นหลังของป้ายใหม่", ["เบลอจากภาพต้นฉบับ", "สีเฉลี่ยจากภาพต้นฉบับ", "สีพื้นเลือกเอง"], key="smart_background")
    color = st.color_picker("สีพื้นกรณีเลือกสีเอง", "#F5F0E6", key="smart_bg_color", disabled=background != "สีพื้นเลือกเอง")
    st.caption("เมื่อป้ายใหม่แคบลง ระบบจะลดขนาดทุกบล็อกในสัดส่วนเดียวกัน แล้วจัดระยะห่างใหม่ ไม่ทำให้วงกลมกลายเป็นวงรี")
    auto_cuts = _suggest_cuts(source, count)
    manual = st.checkbox("ปรับแนวแบ่งบล็อกด้วยตัวเองเพื่อไม่ตัดผ่านตัวหนังสือ", key="smart_manual_cuts")
    if manual:
        cut_values = []
        for i, fraction in enumerate(auto_cuts):
            val = st.slider(f"แนวแบ่งที่ {i + 1} จากด้านบน (%)", 2, 98, int(fraction * 100), key=f"smart_cut_{i+1}")
            cut_values.append(val / 100)
    else:
        cut_values = auto_cuts
    col1, col2 = st.columns(2)
    with col1:
        spacing = st.slider("กระจายพื้นที่แนวตั้งระหว่างบล็อก (%)", 0, 100, 85, 5, key="smart_spacing")
    with col2:
        top_offset = st.slider("ตำแหน่งเริ่มต้นจากด้านบน (%)", 0, 100, 50, 5, key="smart_top_offset")
    if manual and cut_values != sorted(cut_values):
        st.warning("จุดแบ่งต้องเรียงจากบนลงล่าง ระบบจะจัดลำดับอัตโนมัติ")
    pw, ph, _ = _pixel_dimensions(width_cm, height_cm, 65)
    ratio = min(1, 1150 / pw, 1150 / ph, math.sqrt(1_600_000 / (pw * ph)))
    preview_size = (max(1, round(pw * ratio)), max(1, round(ph * ratio)))
    with st.spinner("กำลังจัดบล็อกและสร้างภาพตัวอย่าง..."):
        before = _safe_contain(source, preview_size, background, color)
        after = relayout_bands(source, preview_size, cut_values, background, color,
                               spacing=spacing, top_offset=top_offset)
        p_before, p_after = prepare_quality_previews(before, after)
    st.markdown("#### 🔍 พรีวิวลากดู ก่อน–หลังที่จัดใหม่")
    render_quality_preview(p_before, p_after,
                           title="ก่อน: คงภาพทั้งแผ่น ↔ หลัง: จัดกลุ่มบล็อกใหม่",
                           before_label="ก่อน • คงภาพเต็มแผ่น",
                           after_label="หลัง • จัดบล็อกโดยไม่บีบ/ยืด")
    st.caption("พรีวิวปรับรูปทรงจากกลุ่มภาพ ไม่ได้ทำให้ข้อความที่อยู่ในบล็อกแก้ไขแยกได้; ตรวจภาพและข้อความก่อนพิมพ์")
    fmt = st.selectbox("รูปแบบไฟล์", ["PNG", "TIFF"], key="smart_format")
    cmyk = st.checkbox("TIFF แบบ CMYK เบื้องต้น (ยังไม่ฝัง ICC ของเครื่องพิมพ์)", value=False,
                       disabled=fmt != "TIFF", key="smart_cmyk")
    source_digest = hashlib.sha256(source.resize((64, 64), Image.Resampling.BILINEAR).tobytes()).hexdigest()
    fingerprint = (source_digest, source.width, source.height, width_cm, height_cm, dpi_effective,
                   tuple(cut_values), background, color, spacing, top_offset, fmt, cmyk)
    if st.button("🖨️ สร้างไฟล์จัดวางใหม่พร้อมพิมพ์", type="primary", use_container_width=True,
                 key="smart_make_file"):
        with st.spinner("กำลังสร้างไฟล์ขนาดจริง..."):
            target = relayout_bands(source, (wpx, hpx), cut_values, background, color,
                                    spacing=spacing, top_offset=top_offset)
            binary = _png_or_tiff(target, fmt, dpi_effective, cmyk)
            st.session_state["smart_export"] = (fingerprint, binary)
    if "smart_export" in st.session_state:
        key, data = st.session_state["smart_export"]
        if key == fingerprint:
            st.download_button("⬇️ ดาวน์โหลดป้ายจัดวางใหม่ " + fmt, data=data,
                               file_name="thanasilp_smart_relayout." + ("tif" if fmt == "TIFF" else "png"),
                               mime="image/tiff" if fmt == "TIFF" else "image/png", use_container_width=True)
        else:
            st.caption("เปลี่ยนการตั้งค่าแล้ว กรุณากดสร้างไฟล์ใหม่เพื่อให้ตรงกับพรีวิว")
