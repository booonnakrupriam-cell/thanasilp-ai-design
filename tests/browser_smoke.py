"""End-to-end browser smoke check for Streamlit Thai image editor."""
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

target = Path("/tmp/thanasilp_ci_test_sign.png")
im = Image.new("RGB", (850, 420), (244, 248, 251))
d = ImageDraw.Draw(im)
d.rectangle((15, 15, 835, 405), outline="#1d3e7c", width=5)
d.rectangle((80, 70, 770, 150), fill="#f5eac2")
im.save(target)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(accept_downloads=True, viewport={"width": 1440, "height": 1000})
    problems = []
    page.on("pageerror", lambda err: problems.append(str(err)))
    page.goto("http://127.0.0.1:8501/", wait_until="domcontentloaded", timeout=45000)
    page.get_by_role("tab", name="🖨️ สตูดิโองานพิมพ์").click(timeout=45000)
    page.get_by_text("🖱️ ใหม่! แก้ข้อความบนภาพแบบคลิก / ลาก").first.click(timeout=45000)
    label = page.get_by_text("อัปโหลดภาพป้ายจาก ChatGPT / AI หรือภาพงานพิมพ์").first
    label.wait_for(state="visible", timeout=45000)
    file_input = page.locator('input[type="file"][accept*=".png"]').last
    file_input.set_input_files(str(target))
    canvas = page.locator("#te-canvas")
    canvas.wait_for(state="visible", timeout=45000)
    textarea = page.locator("#te-text")
    textarea.fill("วัดป่าสุวรรณาราม")
    page.get_by_role("button", name="🔤 วางข้อความใหม่").click()
    canvas.click(position={"x": 320, "y": 200})
    page.get_by_text("เพิ่มข้อความแล้ว", exact=False).wait_for(timeout=20000)
    with page.expect_download(timeout=25000) as download_info:
        page.get_by_role("button", name="⬇️ ดาวน์โหลดภาพ PNG").click()
    download = download_info.value
    assert download.suggested_filename == "thanasilp_edited_banner.png", download.suggested_filename
    saved = Path("/tmp/thanasilp_ui_export.png")
    download.save_as(saved)
    with Image.open(saved) as exported:
        assert exported.size == (850, 420), exported.size
    # Confirm all original modes still remain visible in the same selector.
    for marker in ["🔎 1. ขยายภาพ / DPI", "✏️ 2. แก้ข้อความบนภาพ (แบบเดิม)",
                   "✂️ 3. สติกเกอร์ไดคัท", "🕯️ 4. ป้ายงานศพ / ภาพอาลัย"]:
        assert page.get_by_text(marker, exact=False).count(), marker
    critical = [p for p in problems if "uncaught" in p.lower() or "typeerror" in p.lower()]
    assert not critical, critical
    browser.close()
    print("PASS: Streamlit interactive editor UI, Thai text placement, PNG download, original tools")
