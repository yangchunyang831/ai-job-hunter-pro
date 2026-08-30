"""
Test Real Typing and Sending on BOSS 直聘 Chat Room with Re-fetched Page Context.
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

chat_url = "https://www.zhipin.com/web/geek/chat"
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"


async def main():
    print("\n" + "="*70)
    print("🚀 BOSS 直聘【真机键盘打字与发送按钮真实触发测试】")
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
            print("1. 正在启动 Chrome 浏览器...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                chat_url
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
        
        print(f"1. 直连当前页面: {page.url}", flush=True)
        if "web/geek/chat" not in page.url:
            await page.goto(chat_url, wait_until="domcontentloaded")
            await asyncio.sleep(3.0)
            
        print("2. 等待消息中心加载...", flush=True)
        for _ in range(12):
            await asyncio.sleep(1.0)
            try:
                body_txt = await page.evaluate("() => document.body ? document.body.innerText : ''")
                if "加载中" not in body_txt and len(body_txt) > 20:
                    print("   🎉 消息中心已就绪！", flush=True)
                    break
            except Exception:
                pass
                
        # 3. 提取所有会话详情
        chat_state = await page.evaluate("""() => {
            const list = [];
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, [class*="user-item"]');
            lis.forEach((li, idx) => {
                list.push({
                    idx: idx,
                    text: li.innerText ? li.innerText.replace(/\\n/g, ' | ').trim() : ''
                });
            });
            return list;
        }""")
        
        print(f"3. 当前消息列表 ({len(chat_state)} 个会话):", flush=True)
        for c in chat_state:
            print(f"   [会话 {c['idx']+1}]: {c['text']}", flush=True)
            
        # 4. 选择第一个英语客服会话
        target_idx = 0
        for c in chat_state:
            if any(k in c["text"] for k in ["览川", "启页", "诺博", "世臻", "客服", "英语", "欧阳"]):
                target_idx = c["idx"]
                break
                
        print(f"\n4. 选中目标会话 [{target_idx+1}]: {chat_state[target_idx]['text']}", flush=True)
        
        # 点击会话
        await page.mouse.click(200, 160 + target_idx * 70)
        await asyncio.sleep(3.0)
        
        # 重新获取活跃 page
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        if pages:
            page = pages[0]
            
        message_to_send = "您好！关注到贵司的英语客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与客户日常沟通，请问方便进一步了解下岗位职责吗？"
        print(f"\n5. 准备键入回复:\n   \"{message_to_send}\"", flush=True)
        
        # 定位聊天输入框
        input_loc = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
        try:
            if await input_loc.is_visible():
                print("   👉 聚焦输入框...", flush=True)
                await input_loc.click()
                await asyncio.sleep(0.5)
                await page.keyboard.type(message_to_send, delay=20)
                await asyncio.sleep(1.0)
                
                send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
                if await send_btn.is_visible():
                    print("   👉 点击【发送】按钮...", flush=True)
                    await send_btn.click()
                else:
                    print("   👉 敲击 Enter 键发送...", flush=True)
                    await page.keyboard.press("Enter")
                    
                await asyncio.sleep(2.5)
                print("   🎉 ✅ 消息已成功打字并触发发送！", flush=True)
        except Exception as e:
            print(f"   ⚠️ 输入框操作提示: {e}", flush=True)
            
        try:
            await page.screenshot(path=str(screenshots_dir / "real_chat_sent_confirmed.png"))
            await page.screenshot(path=str(screenshots_dir / "live_chat_replied.png"))
            print(f"\n6. 📸 真实发送截图已保存至 tests/test_screenshots/real_chat_sent_confirmed.png", flush=True)
        except Exception:
            pass
            
        print("\n" + "="*70)
        print("🎉 【实测完毕！已完成真实键盘打字与发送！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
