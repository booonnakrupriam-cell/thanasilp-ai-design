"""Browser-based editable text and cover layers for sign images.
Client-side editor: no paid API and no OCR claims. Uploaded images pass through
the Streamlit server; finished PNG and editable project JSON download in browser.
"""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

HTML = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Chonburi&family=Kanit:wght@400;700&family=Mitr:wght@400;700&family=Noto+Serif+Thai:wght@400;700&family=Prompt:wght@400;700&family=Sarabun:wght@400;700&family=Sriracha&display=swap" rel="stylesheet">
<div class="thanasilp-editor">
  <div class="te-toolbar" aria-label="เครื่องมือแก้ไขภาพ">
    <button type="button" data-editor-mode="select" class="active">🖱️ เลือก / ลากย้าย</button>
    <button type="button" data-editor-mode="add">🔤 วางข้อความใหม่</button>
    <button type="button" data-editor-mode="cover">🧽 ลากกรอบทับคำผิด</button>
    <button type="button" data-editor-mode="sample">🎨 ดูดสีพื้น</button>
    <button type="button" data-editor-mode="pan">✋ เลื่อนภาพ</button>
  </div>
  <div class="te-grid">
    <section class="te-workarea">
      <canvas id="te-canvas" width="1050" height="630" aria-label="ภาพที่กำลังแก้ไข รองรับการคลิกและลาก"></canvas>
      <div class="te-zoomrow">
        <label for="te-zoom">ซูม</label>
        <input id="te-zoom" type="range" min="25" max="1200" step="25" value="100">
        <strong id="te-zlabel">100%</strong>
        <button type="button" id="te-resetzoom">พอดีหน้าจอ</button>
      </div>
      <div class="te-message" id="te-status" role="status">กำลังเปิดภาพ…</div>
      <div class="te-note">ข้อความเดิมในภาพ JPG/PNG ยังเป็นพิกเซล: ใช้ “ดูดสีพื้น” และ “ลากกรอบทับคำผิด” ก่อนวางตัวอักษรใหม่ หากพื้นหลังมีลายซับซ้อน สีปิดทับอาจไม่เนียน</div>
    </section>
    <aside class="te-controls">
      <div class="te-panel">
        <strong>✏️ แก้ / เพิ่มข้อความไทย</strong>
        <label for="te-text">ข้อความ (หลายบรรทัดได้)</label>
        <textarea id="te-text" rows="3" maxlength="3000" placeholder="พิมพ์ชื่อวัด วันที่ หรือข้อความใหม่"></textarea>
        <label for="te-font">ฟอนต์ไทย</label>
        <select id="te-font">
          <option value="Sarabun">Sarabun — ทางการ อ่านง่าย</option>
          <option value="Kanit">Kanit — ตัวหนา อ่านไกล</option>
          <option value="Mitr">Mitr — โค้งมน</option>
          <option value="Prompt">Prompt — ทันสมัย</option>
          <option value="Chonburi">Chonburi — หัวเรื่องงานวัด</option>
          <option value="Sriracha">Sriracha — ลายมือ</option>
          <option value="Noto Serif Thai">Noto Serif Thai — สุภาพมีเชิง</option>
          <option value="Tahoma">Tahoma — ฟอนต์เครื่อง</option>
          <option value="ThanasilpCustom">ฟอนต์ที่อัปโหลด</option>
        </select>
        <label for="te-custom-font">เพิ่มฟอนต์ของคุณเอง (.TTF/.OTF)</label>
        <input type="file" id="te-custom-font" accept=".ttf,.otf">
        <div class="te-two">
          <div><label for="te-size">ขนาดตัวอักษร (px)</label><input id="te-size" type="number" min="8" max="360" value="68"></div>
          <div><label for="te-weight">น้ำหนัก</label><select id="te-weight"><option value="bold">หนา</option><option value="normal">ปกติ</option></select></div>
          <div><label for="te-color">สีตัวอักษร</label><input type="color" id="te-color" value="#fff200"></div>
          <div><label for="te-outline">สีเส้นขอบ</label><input type="color" id="te-outline" value="#173f9e"></div>
          <div><label for="te-stroke">หนาขอบ (px)</label><input id="te-stroke" type="number" min="0" max="40" value="4"></div>
          <div><label for="te-shadow">เงา (px)</label><input id="te-shadow" type="number" min="0" max="40" value="3"></div>
        </div>
        <button type="button" class="te-danger" id="te-delete" disabled>🗑️ ลบข้อความ / กรอบที่เลือก</button>
        <small>เส้นขอบใช้เส้นโค้งตามรูปทรงจริงของฟอนต์ ไม่ยืดตัวอักษร และใช้ได้กับสระ/วรรณยุกต์ตามการแสดงผลของเบราว์เซอร์</small>
      </div>
      <div class="te-panel">
        <strong>🧽 ปิดทับข้อความเก่า</strong>
        <label for="te-cover">สีสำหรับปิดพื้น</label>
        <input type="color" id="te-cover" value="#ffffff">
        <small>คลิก “ดูดสีพื้น” จากภาพก่อน แล้วลากกรอบปิดคำเดิม วิธีนี้เหมาะกับพื้นหลังสีเรียบ ไม่ใช่ AI ลบวัตถุ</small>
      </div>
      <div class="te-panel">
        <strong>🖨️ ตรวจขนาดและสี</strong>
        <label for="te-preset">ขนาดป้ายยอดนิยม (ซม.)</label>
        <select id="te-preset">
          <option value="">กำหนดเอง</option>
          <option value="200x100">200 × 100</option>
          <option value="240x120">240 × 120</option>
          <option value="300x100">300 × 100</option>
          <option value="300x150">300 × 150</option>
          <option value="60x160">X-Stand 60 × 160</option>
          <option value="80x200">Roll-up 80 × 200</option>
          <option value="120x80">120 × 80</option>
          <option value="100x100">100 × 100</option>
        </select>
        <div class="te-two">
          <div><label for="te-wcm">กว้าง ซม.</label><input id="te-wcm" type="number" min="1" max="900" value="200"></div>
          <div><label for="te-hcm">สูง ซม.</label><input id="te-hcm" type="number" min="1" max="900" value="100"></div>
        </div>
        <div class="te-dpi" id="te-dpi"></div>
        <div class="te-three">
          <div><label for="te-bright">ความสว่าง %</label><input id="te-bright" type="range" min="50" max="150" value="100"></div>
          <div><label for="te-saturate">สีสด %</label><input id="te-saturate" type="range" min="50" max="150" value="100"></div>
          <div><label for="te-contrast">คอนทราสต์ %</label><input id="te-contrast" type="range" min="50" max="150" value="100"></div>
        </div>
        <small>ค่าขนาดในส่วนนี้ใช้ตรวจ DPI และอัตราส่วน ไม่ได้แปลงขนาด PNG โดยอัตโนมัติ • สีเป็นภาพตัวอย่าง sRGB ไม่ใช่ผลพิสูจน์สี CMYK/ICC</small>
      </div>
    </aside>
  </div>
  <div class="te-actions">
    <button type="button" id="te-undo">↶ ย้อนกลับ</button>
    <button type="button" id="te-redo">↷ ทำซ้ำ</button>
    <button type="button" class="te-primary" id="te-export">⬇️ ดาวน์โหลดภาพ PNG</button>
    <button type="button" id="te-save">💾 บันทึกไฟล์แก้ไข .json</button>
    <label class="te-import" for="te-load">📂 เปิดงานเก่า .json</label>
    <input type="file" id="te-load" accept=".json,application/json" hidden>
  </div>
  <p class="te-footnote">งานแก้ไขเกิดบนอุปกรณ์ของคุณหลังโหลดภาพเข้าตัวแก้ แต่ภาพอัปโหลดเริ่มต้นผ่านเซิร์ฟเวอร์ Streamlit; ไฟล์โครงการ .json เก็บข้อมูลรูปภาพและข้อความ โปรดรักษาความเป็นส่วนตัว</p>
</div>
"""

CSS = """
.thanasilp-editor {font-family:Tahoma,'Noto Sans Thai',sans-serif;color:#142538;font-size:14px}
.thanasilp-editor *, .thanasilp-editor *:before,.thanasilp-editor *:after{box-sizing:border-box}
.thanasilp-editor button,.thanasilp-editor select,.thanasilp-editor input,.thanasilp-editor textarea{font:inherit}
.thanasilp-editor button,.thanasilp-editor .te-import{cursor:pointer;border:1px solid #c6d3e2;background:#fff;border-radius:8px;padding:9px 12px;color:#17304f;font-weight:700}
.thanasilp-editor button:disabled{cursor:not-allowed;opacity:.5}
.thanasilp-editor button:hover:not(:disabled){border-color:#1376c4}
.thanasilp-editor .te-toolbar{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 12px}
.thanasilp-editor .te-toolbar button{background:#ecf5ff}
.thanasilp-editor .te-toolbar button.active{background:#1266bd;color:#fff;border-color:#1266bd}
.thanasilp-editor .te-grid{display:grid;grid-template-columns:minmax(0,1fr) 315px;gap:14px;align-items:start}
.thanasilp-editor .te-workarea{min-width:0;background:#edf3f8;border:1px solid #cddceb;border-radius:12px;padding:10px}
.thanasilp-editor #te-canvas{display:block;width:100%;height:auto;background:#dae4ee;border-radius:7px;touch-action:none;user-select:none;cursor:move;box-shadow:0 2px 10px #344f6718}
.thanasilp-editor .te-zoomrow{display:flex;gap:8px;align-items:center;margin:12px 0;flex-wrap:wrap}
.thanasilp-editor .te-zoomrow input{flex:1;min-width:90px}
.thanasilp-editor #te-zlabel{min-width:55px}
.thanasilp-editor .te-message{background:#fff;color:#1b527f;padding:9px;border-radius:7px;font-size:13px;min-height:32px}
.thanasilp-editor .te-note,.thanasilp-editor .te-footnote{font-size:12px;line-height:1.55;color:#697785;margin-top:8px}
.thanasilp-editor .te-controls{display:grid;gap:10px;max-height:910px;overflow:auto}
.thanasilp-editor .te-panel{background:#fff;border:1px solid #d4e0ed;border-radius:10px;padding:12px;display:grid;gap:7px;min-width:0}
.thanasilp-editor .te-panel strong{color:#124b8f;font-size:16px}
.thanasilp-editor .te-panel label{font-size:12px;font-weight:700;margin-top:4px}
.thanasilp-editor .te-panel select,.thanasilp-editor .te-panel input:not([type=color]):not([type=range]):not([type=file]),.thanasilp-editor textarea{
 width:100%;border:1px solid #b9cbdc;border-radius:6px;padding:7px;background:#fff;color:#132d4a;min-width:0}
.thanasilp-editor input[type=color]{width:100%;height:38px;border:1px solid #c0d0dd;border-radius:7px;padding:2px;background:#fff}
.thanasilp-editor .te-two{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.thanasilp-editor .te-three{display:grid;grid-template-columns:1fr;gap:5px}
.thanasilp-editor .te-three input{width:100%}
.thanasilp-editor .te-two>div{min-width:0}
.thanasilp-editor .te-panel small{font-size:11px;color:#728395;line-height:1.6}
.thanasilp-editor .te-dpi{font-size:12px;color:#234e71;line-height:1.6;padding:6px;background:#f2f6fa;border-radius:7px}
.thanasilp-editor .te-danger{color:#ac2b3d!important}
.thanasilp-editor .te-actions{display:flex;gap:9px;flex-wrap:wrap;margin:13px 0}
.thanasilp-editor .te-actions .te-primary{color:white;background:#0c7e54;border-color:#0c7e54}
.thanasilp-editor .te-import{display:inline-flex;align-items:center}
@media(max-width:820px){
 .thanasilp-editor .te-grid{grid-template-columns:1fr}
 .thanasilp-editor .te-controls{max-height:none;grid-template-columns:1fr}
 .thanasilp-editor .te-toolbar button{flex:1 1 42%;font-size:12px}
 .thanasilp-editor .te-actions>*{flex:1 1 45%;text-align:center}
}
"""

_JS_PATH = Path(__file__).with_name("editor_canvas.js")
EDITOR = st.components.v2.component(
    "thanasilp_canvas_editor",
    html=HTML,
    css=CSS,
    js=_JS_PATH.read_text(encoding="utf-8"),
)


def render_interactive_editor():
    """New editing mode; all original print-studio modes remain available."""
    st.markdown("#### 🖱️ แก้ข้อความบนภาพแบบคลิก / ลาก — เวอร์ชันทดลอง")
    st.caption(
        "อัปโหลดภาพ JPG/PNG → ลากกรอบทับคำผิด → พิมพ์คำใหม่ → คลิกวาง/ลากย้าย → ดาวน์โหลด PNG "
        "หรือบันทึกโปรเจกต์ JSON เพื่อแก้ต่อ"
    )
    upload = st.file_uploader(
        "อัปโหลดภาพป้ายจาก ChatGPT / AI หรือภาพงานพิมพ์",
        type=["png", "jpg", "jpeg", "webp"],
        key="studio_interactive_image_upload",
    )
    if upload is None:
        st.info("เลือกภาพป้ายเพื่อเปิดพื้นที่แก้ไขแบบคลิกและลาก")
        return
    if upload.size > 25 * 1024 * 1024:
        st.error("รูปภาพต้องมีขนาดไม่เกิน 25 MB")
        return
    try:
        with Image.open(BytesIO(upload.getvalue())) as source:
            if source.width * source.height > 35_000_000:
                st.error("ภาพต้นฉบับใหญ่เกิน 35 ล้านพิกเซล กรุณาย่อเพื่อใช้กับตัวแก้ภาพก่อน")
                return
            im = ImageOps.exif_transpose(source)
            original_size = im.size
            im.thumbnail((2600, 2600), Image.Resampling.LANCZOS)
            has_alpha = "A" in im.getbands() or "transparency" in im.info
            im = im.convert("RGBA" if has_alpha else "RGB")
            stream = BytesIO()
            im.save(stream, format="PNG" if has_alpha else "JPEG", quality=91)
            media = "image/png" if has_alpha else "image/jpeg"
            src = "data:" + media + ";base64," + base64.b64encode(stream.getvalue()).decode("ascii")
    except (OSError, ValueError, UnidentifiedImageError):
        st.error("ไฟล์ภาพไม่สมบูรณ์หรือไม่รองรับ กรุณาเลือก JPG, PNG หรือ WEBP")
        return
    if original_size != im.size:
        st.warning(
            f"ตัวแก้ภาพใช้สำเนาขนาด {im.width:,} × {im.height:,} px "
            f"(ต้นฉบับ {original_size[0]:,} × {original_size[1]:,} px) "
            "เพื่อให้เลื่อนและวางข้อความได้ลื่นไหล ไฟล์ PNG ที่ส่งออกจากโหมดนี้จะมีขนาดเท่าภาพสำเนา "
            "หากต้องพิมพ์ใหญ่ใช้เครื่องมือขยายภาพ/DPI ต่อ"
        )
    else:
        st.caption(f"ขนาดภาพสำหรับแก้ไข {im.width:,} × {im.height:,} px")
    # Passing the image as data rather than raw HTML avoids embedding any user-controlled markup.
    EDITOR(data={"image": src}, key="studio_interactive_editor_v1")
    st.caption(
        "เวอร์ชันนี้แก้ข้อความใหม่เป็นชั้นภาพจริงและส่งออก PNG ได้ "
        "แต่ยังไม่ตรวจหาข้อความเดิมด้วย OCR อัตโนมัติ และยังไม่ลบพื้นหลังลายละเอียดด้วย AI"
    )
