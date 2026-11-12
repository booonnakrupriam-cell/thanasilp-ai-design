"""Informational probe of the public Streamlit Community Cloud deployment."""
from playwright.sync_api import sync_playwright

url = "https://thanasin-ai-design.streamlit.app/"
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(url, wait_until="domcontentloaded", timeout=75000)
    # A sleeping Community Cloud app may show a wake-up button.
    for title in ("Yes, get this app back up!", "Wake up", "Get app back up"):
        button = page.get_by_role("button", name=title)
        if button.count() > 0 and button.first.is_visible():
            button.first.click()
            break
    page.get_by_role("tab", name="🖨️ สตูดิโองานพิมพ์").wait_for(state="visible", timeout=100000)
    page.get_by_role("tab", name="🖨️ สตูดิโองานพิมพ์").click()
    page.get_by_text("🖱️ ใหม่! แก้ข้อความบนภาพแบบคลิก / ลาก").first.wait_for(
        state="visible", timeout=45000
    )
    print("PASS: Public Streamlit deployment is online and shows the new Print Studio editing mode")
    browser.close()
