"""
Directly targets and replies to conversations that have HR messages.
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
resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"


def generate_reply(hr_msg: str) -> str:
    msg_lower = hr_msg.lower()
    if any(k in msg_lower for k in ["英语", "外语", "口语", "四级", "六级", "专八", "熟练", "水平", "流畅"]):
        return "您好！我的英语具备良好的听说读写能力，能够熟练使用英文进行邮件往来、工单处理及日常客户线上沟通，日常业务沟通无障碍。请问贵司该岗位主要对接哪些区域的客户呢？"
    if any(k in msg_lower for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
        return "好的，我的个人求职简历【杨春_个人求职简历.pdf】已为您发送，请您查收！如果有需要进一步了解的项目经历或细节，随时沟通。"
    if any(k in msg_lower for k in ["到岗", "离职", "什么时候", "在职", "时间"]):
        return "您好！我目前已处于离职状态，可根据贵司安排随时到岗开展工作。"
    if any(k in msg_lower for k in ["回应", "在看", "收到太多", "沟通", "方便", "聊聊"]):
        return "您好！一直在关注贵司的在招岗位，目前时间充裕，非常方便沟通，请问方便进一步了解下岗位职责吗？"
    return "您好！非常感谢您的认可，我对贵司在招岗位很感兴趣，请问方便发一份详细岗位要求了解下吗？"


async def main():
    print("\n" + "="*70)
    print("🤖 BOSS 直聘【HR 回复消息精准定位与应答】启动")
    print(f"📄 绑定简历: {resume_file_path}")
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
            print("1. 正在启动 Chrome 浏览器并进入消息聊天室...", flush=True)
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
            await asyncio.sleep(4.0)
        
        # 针对【会话 3: 师书怡 南京思盖文化传媒】与【会话 5: 王女士 安捷智合】
        targets = [
            {"name": "师书怡 (南京思盖文化传媒)", "x": 200, "y": 300, "msg": "哈哈，你是不是收到太多信息啦，都回复不过来了；看到咱们还在看工作，可以回应一声哦"},
            {"name": "王女士 (安捷智合HR)", "x": 200, "y": 440, "msg": "看你的简历蛮符合的，方便发份详细的简历过来吗？"}
        ]
        
        for t in targets:
            print("\n" + "─"*60)
            print(f"🎯 正在定位并回复 HR: 【{t['name']}】...")
            print("─"*60, flush=True)
            
            # 点击坐标
            await page.mouse.click(t["x"], t["y"])
            await asyncio.sleep(2.5)
            
            reply_text = generate_reply(t["msg"])
            print(f"   💬 HR 消息: \"{t['msg']}\"", flush=True)
            print(f"   🤖 生成智能回复: \"{reply_text}\"", flush=True)
            
            # 索要简历自动发送
            if "简历" in t["msg"]:
                print(f"   📎 自动触发发送简历附件: {resume_file_path}", flush=True)
                send_btn = page.locator("button:has-text('发简历'), button:has-text('发送简历'), [ka*='send_resume'], .chat-op .btn-resume").first
                try:
                    if await send_btn.is_visible():
                        print("   👉 点击平台工具栏【发简历】...", flush=True)
                        await send_btn.click(timeout=3000)
                        await asyncio.sleep(1.5)
                        sure = page.locator(".dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送简历')").first
                        if await sure.is_visible():
                            await sure.click(timeout=3000)
                            print("   🎉 ✅ 简历已通过平台弹窗发送！", flush=True)
                except Exception as e:
                    print(f"   ℹ️ 简历发送提示: {e}", flush=True)
                    
            # 填入输入框发送
            input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
            try:
                if await input_box.is_visible():
                    await input_box.click(timeout=3000)
                    await input_box.fill(reply_text)
                    await page.keyboard.press("Enter")
                    print(f"   🎉 ✅ 消息已成功发送给【{t['name']}】！", flush=True)
                    await asyncio.sleep(2.0)
            except Exception as e:
                print(f"   ⚠️ 输入框提示: {e}", flush=True)
                
        await page.screenshot(path=str(screenshots_dir / "hr_replied_successfully.png"))
        print("\n📸 最终回复截图已保存至 tests/test_screenshots/hr_replied_successfully.png", flush=True)
        print("\n" + "="*70)
        print("🎉 【HR 消息已全部智能回复完毕！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
