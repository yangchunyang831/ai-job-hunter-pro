import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\chrome_debug_profile"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        captured_jobs = []
        
        async def on_response(response):
            if "joblist.json" in response.url or "recommend" in response.url or "job/list" in response.url:
                try:
                    data = await response.json()
                    job_list = data.get("zpData", {}).get("jobList", [])
                    if job_list:
                        print(f"🔥 成功通过底层 XHR 拦截到 {len(job_list)} 个真实岗位数据包！")
                        for j in job_list:
                            captured_jobs.append(j)
                except Exception:
                    pass
                    
        page.on("response", on_response)
        
        print("1. 正在访问非湖南高危搜索页 (上海·海外客服)...")
        await page.goto("https://www.zhipin.com/web/geek/job?query=%E6%B5%B7%E5%A4%96%E5%AE%A2%E6%9C%8D&city=101020100")
        await page.wait_for_timeout(6000)
        
        print(f"累计捕获真实岗位: {len(captured_jobs)} 个")
        for idx, j in enumerate(captured_jobs[:6], 1):
            b_name = j.get("brandName", "未知公司")
            j_name = j.get("jobName", "未知岗位")
            s_desc = j.get("salaryDesc", "面议")
            c_name = j.get("cityName", "上海")
            print(f"  👉 [{idx}] 【{b_name}】{j_name} ({s_desc}) | 城市: {c_name}")
            
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
