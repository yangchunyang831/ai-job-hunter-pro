import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def generate_pdf():
    html_path = (Path(__file__).resolve().parent.parent / "个人简历" / "杨春_个人简历.html").resolve()
    pdf_path = (Path(__file__).resolve().parent.parent / "个人简历" / "杨春_个人简历.pdf").resolve()
    screenshot_path = Path(__file__).resolve().parent / "test_screenshots" / "04_resume_preview.png"
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)

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
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "8mm", "bottom": "8mm", "left": "8mm", "right": "8mm"}
        )
        try:
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            print(f"Generated PDF resume successfully: {pdf_path} (Size: {pdf_path.stat().st_size} bytes)")
        except PermissionError:
            fallback_pdf = Path(r"D:\招聘\个人简历\杨春_个人求职简历.pdf")
            with open(fallback_pdf, "wb") as f:
                f.write(pdf_bytes)
            print(f"Original PDF is currently open in viewer. Saved updated version to: {fallback_pdf} (Size: {fallback_pdf.stat().st_size} bytes)")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(generate_pdf())
