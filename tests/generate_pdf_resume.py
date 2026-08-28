import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def generate_pdf():
    html_path = Path(r"D:\招聘\个人简历\杨春_个人简历.html").resolve()
    pdf_path = Path(r"D:\招聘\个人简历\杨春_个人简历.pdf").resolve()
    screenshot_path = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\82b066e7-211b-4ed7-bf67-fe4723c9e8ea\persona_test_screenshots\04_resume_preview.png")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )
        page = await browser.new_page()
        print(f"Loading HTML resume from {html_path.as_uri()} ...")
        await page.goto(html_path.as_uri(), wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 截屏供预览
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Captured screenshot to {screenshot_path}")

        # 导出高质量 A4 PDF
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "8mm", "bottom": "8mm", "left": "8mm", "right": "8mm"}
        )
        print(f"Generated PDF resume successfully: {pdf_path} (Size: {pdf_path.stat().st_size} bytes)")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(generate_pdf())
