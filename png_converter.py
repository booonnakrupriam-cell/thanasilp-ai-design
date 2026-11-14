"""Convert uploaded images to true PNG without resizing or lossy re-encoding."""
from io import BytesIO
import streamlit as st
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 40 * 1024 * 1024
MAX_PIXELS = 80_000_000

def render_png_converter():
    st.title("🖼️ แปลงภาพล่าสุดเป็นไฟล์ PNG จริง")
    st.write("อัปโหลดภาพที่บันทึกจาก ChatGPT, Gemini หรือแหล่งอื่น แล้วดาวน์โหลดเป็น .png โดยไม่ย่อหรือขยายจำนวนพิกเซล")
    st.info("หมายเหตุ: เว็บไม่สามารถดึงภาพล่าสุดจากแชท ChatGPT โดยอัตโนมัติได้ กรุณาบันทึกภาพลงเครื่องก่อนแล้วอัปโหลดที่นี่")
    uploaded = st.file_uploader(
        "เลือกภาพต้นฉบับ (WEBP, JPG, JPEG, PNG, BMP, TIFF)",
        type=["webp", "jpg", "jpeg", "png", "bmp", "tif", "tiff"],
        key="png_converter_upload",
    )
    if uploaded is None:
        return
    if uploaded.size > MAX_BYTES:
        st.error("ภาพใหญ่เกิน 40 MB")
        return
    try:
        content = uploaded.getvalue()
        with Image.open(BytesIO(content)) as im:
            width, height = im.size
            if width * height > MAX_PIXELS:
                st.error("ภาพใหญ่เกิน 80 ล้านพิกเซล ไม่สามารถแปลงได้ในระบบนี้")
                return
            im.load()
            original_format = im.format or "ไม่ทราบ"
            icc = im.info.get("icc_profile")
            # Preserve original pixel matrix and transparency; never resize,
            # sharpen, upsample, or alter aspect ratio.
            if im.mode == "P":
                converted = im.copy() if "transparency" not in im.info else im.convert("RGBA")
            elif im.mode in ("RGB", "RGBA", "L", "LA", "1", "I", "I;16"):
                converted = im.copy()
            else:
                converted = im.convert("RGBA" if "A" in im.getbands() else "RGB")
            out = BytesIO()
            save_kwargs = {"format": "PNG", "compress_level": 6}
            if icc:
                save_kwargs["icc_profile"] = icc
            converted.save(out, **save_kwargs)
            png_bytes = out.getvalue()
        st.success("แปลงเป็น PNG จริงเรียบร้อย")
        st.write(f"ต้นฉบับ: {original_format} | ขนาด: {width:,} × {height:,} พิกเซล | ไฟล์ PNG: {len(png_bytes)/1024/1024:.2f} MB")
        st.image(png_bytes, caption="ตัวอย่างภาพ PNG (การแสดงผลอาจถูกย่อบนหน้าจอเท่านั้น)", use_container_width=True)
        st.download_button(
            "⬇️ ดาวน์โหลด PNG จริง (.png)",
            data=png_bytes,
            file_name="thanasilp_image_original_pixels.png",
            mime="image/png",
            use_container_width=True,
            type="primary",
        )
        st.caption("PNG บันทึกโดยไม่สูญเสียข้อมูลเพิ่มเติมจากภาพที่อัปโหลด แต่ไม่สามารถคืนรายละเอียดที่หายไปจาก JPG/WEBP แบบบีบอัด หรือสร้างพิกเซล 16K เพิ่มขึ้นเองได้")
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        st.error("ไม่สามารถอ่านภาพได้ กรุณาเลือกไฟล์ภาพที่สมบูรณ์")
