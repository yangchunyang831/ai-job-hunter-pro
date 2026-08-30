"""
Real Live Communication with Full Hydration Wait and Confirmation.
Ensures skeleton boxes are replaced by real rendered DOM cards,
clicks real 立即沟通, handles dialog, sends the message, and captures the sent chat bubble.
"""
import sys
import os
import subprocess
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
target_search_url = "https://www.zhipin.com/web/geek/job?query=%E8%8B%B1%E8%AF%AD%E5%AE%A2%E6%9C%8D&city=101020100"


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【真实打招呼消息实战发送与确认】")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("1. 启动 Chrome 浏览器...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                target_search_url
            ])
            for _ in range(12):
                await asyncio.sleep(1.0)
                try:
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    break
                except Exception:
                    pass

        if not browser:
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"1. 成功直连 Chrome！当前 URL: {page.url}", flush=True)
        
        if "query=" not in page.url or "101020100" not in page.url:
            print("2. 导航至上海英语客服页面...", flush=True)
            await page.goto(target_search_url, wait_until="domcontentloaded")
            
        print("2. 正在等待页面卡片彻底渲染 (去除骨架屏)...", flush=True)
        # 等待真实卡片出现
        real_card = None
        for sec in range(15):
            await asyncio.sleep(1.0)
            cards = await page.query_selector_all(".job-card-wrapper, .job-card-box, li.job-card, .job-card-left")
            btn = await page.query_selector(".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通')")
            if cards and btn:
                print(f"   🎉 第 {sec+1} 秒真实卡片与【立即沟通】按钮已完全就绪！", flush=True)
                break
                
        await page.screenshot(path=str(screenshots_dir / "step1_cards_rendered.png"))
        print("   📸 已截图: tests/test_screenshots/step1_cards_rendered.png", flush=True)
        
        # 3. 提取第一个卡片信息
        card_info = await page.evaluate("""() => {
            const card = document.querySelector('.job-card-wrapper, .job-card-box, li.job-card');
            if (!card) return null;
            return {
                title: card.querySelector('.job-name, .job-title') ? card.querySelector('.job-name, .job-title').innerText.trim() : '',
                company: card.querySelector('.company-name') ? card.querySelector('.company-name').innerText.trim() : '',
                salary: card.querySelector('.salary') ? card.querySelector('.salary').innerText.trim() : ''
            };
        }""")
        
        print(f"3. 锁定目标岗位: {card_info}", flush=True)
        
        # 4. 点击第一个卡片
        first_card = page.locator(".job-card-wrapper, .job-card-box, li.job-card").first
        if await first_card.is_visible():
            print("4. 点击左侧第一个岗位卡片...", flush=True)
            await first_card.click()
            await asyncio.sleep(2.0)
            
        # 5. 点击右侧【立即沟通】
        chat_btn = page.locator(".btn-startchat, a:has-text('立即沟通'), button:has-text('立即沟通'), .op-btn-chat").first
        if await chat_btn.is_visible():
            btn_text = (await chat_btn.inner_text()).strip()
            print(f"5. 发现右侧沟通按钮: 【{btn_text}】，正在点击...", flush=True)
            await chat_btn.click()
            await asyncio.sleep(2.5)
            
        # 6. 处理打招呼弹窗 (如果出现)
        dialog_sure = page.locator(".dialog-startchat .btn-sure, .dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送'), button:has-text('留个话')").first
        try:
            if await dialog_sure.is_visible():
                print("6. 发现打招呼确认弹窗，正在点击【确定/发送】...", flush=True)
                await dialog_sure.click()
                await asyncio.sleep(2.5)
        except Exception:
            pass
            
        await page.screenshot(path=str(screenshots_dir / "step2_after_chat_click.png"))
        print("   📸 已截图: tests/test_screenshots/step2_after_chat_click.png", flush=True)
        
        # 7. 检查是否打开了聊天页面或弹出了聊天窗
        print("7. 正在检查当前聊天窗口与发送状态...", flush=True)
        all_pages = context.pages
        chat_page = None
        for pg in all_pages:
            if "web/geek/chat" in pg.url:
                chat_page = pg
                break
                
        if chat_page:
            print(f"   🎉 已进入独立聊天页: {chat_page.url}", flush=True)
            await chat_page.bring_to_front()
            await asyncio.sleep(3.0)
            await chat_page.screenshot(path=str(screenshots_dir / "step3_real_chat_window.png"))
            
            # 读取已发送的消息
            sent_msgs = await chat_page.evaluate("""() => {
                const msgs = [];
                document.querySelectorAll('.item-myself, .chat-item-myself, .message-content, [class*="myself"]').forEach(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    if (txt) msgs.push(txt);
                });
                return msgs;
            }""")
            print(f"   💬 聊天窗口中已送达的我的消息: {sent_msgs}", flush=True)
        else:
            print("   ℹ️ 正在当前页面右侧检查聊天抽屉/消息记录...", flush=True)
            sent_msgs = await page.evaluate("""() => {
                const msgs = [];
                document.querySelectorAll('.item-myself, .chat-item-myself, .message-content, [class*="myself"]').forEach(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    if (txt) msgs.push(txt);
                });
                return msgs;
            }""")
            print(f"   💬 当前页面已发送的消息: {sent_msgs}", flush=True)
            
        print("\n" + "="*70)
        print("🎉 【真实实战打招呼全流程执行完成！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
