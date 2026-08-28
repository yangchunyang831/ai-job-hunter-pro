"""Playwright CDP Browser Controller for real Chrome connection, human-like interaction, and DOM/XHR scraping."""
import time
import random
import logging
import threading
from typing import Optional, List, Dict, Any, Generator
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from src.schemas import RawJobCard
from src.notifier import NotificationManager

logger = logging.getLogger(__name__)


class CDPBrowserController:
    """真实 Chrome CDP 浏览器控制器"""
    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", notifier: Optional[NotificationManager] = None, stop_event: Optional[threading.Event] = None):
        self.cdp_url = cdp_url
        self.notifier = notifier or NotificationManager()
        self.stop_event = stop_event
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.search_page: Optional[Page] = None
        self.chat_page: Optional[Page] = None

    def connect(self):
        """连接到带有 --remote-debugging-port 的日常 Chrome 实例"""
        logger.info(f"Connecting to Chrome via CDP: {self.cdp_url} ...")
        self._playwright = sync_playwright().start()
        try:
            self.browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
            self.context = self.browser.contexts[0]
            logger.info("Successfully connected to real Chrome instance!")
        except Exception as e:
            logger.error(f"Failed to connect to Chrome at {self.cdp_url}: {e}")
            raise RuntimeError(
                "无法连接到 Chrome 浏览器！请确保在命令行中运行了：\n"
                "chrome.exe --remote-debugging-port=9222 --user-data-dir=\"C:\\chrome_debug_profile\""
            ) from e

    def close(self):
        """释放资源"""
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

    def abort(self):
        """强行立即切断浏览器当前操作 (毫秒级中断)"""
        logger.info("🛑 正在强制中断 CDP 浏览器会话...")
        try:
            if self.search_page and not self.search_page.is_closed():
                self.search_page.close()
        except Exception:
            pass
        try:
            self.close()
        except Exception:
            pass

    def human_delay(self, min_s: float = 2.0, max_s: float = 4.5):
        """拟人化随机停顿 (支持即时中断)"""
        delay_time = random.uniform(min_s, max_s)
        if self.stop_event:
            self.stop_event.wait(delay_time)
        else:
            time.sleep(delay_time)

    def human_type(self, page: Page, selector: str, text: str):
        """模拟人类打字速度"""
        page.focus(selector)
        for char in text:
            if self.stop_event and self.stop_event.is_set():
                break
            page.keyboard.type(char, delay=random.randint(60, 160))
            if char in ["，", "。", "！", "？", "\n"]:
                self.human_delay(0.2, 0.4)

    def check_and_handle_captcha(self, page: Page) -> bool:
        """检测滑块验证码并触发熔断"""
        captcha_selectors = [
            ".geetest_radar_tip",
            ".geetest_slider",
            ".verify-slider",
            "[class*='captcha']",
            "[class*='dialog-captcha']"
        ]
        for sel in captcha_selectors:
            try:
                elem = page.query_selector(sel)
                if elem and elem.is_visible():
                    logger.warning("🚨 检测到滑块验证码弹窗！触发熔断保护！")
                    self.notifier.send_captcha_alert()
                    # 轮询等待用户手动完成滑动，避免阻塞后台线程
                    for _ in range(60):
                        if self.stop_event and self.stop_event.is_set():
                            break
                        if not elem.is_visible():
                            logger.info("✅ 验证码已解除，继续执行！")
                            break
                        self.human_delay(1.0, 1.0)
                    return True
            except Exception:
                pass
        return False

    CITY_CODE_MAP = {
        "杭州": "101210100",
        "上海": "101020100",
        "北京": "101010100",
        "深圳": "101280600",
        "广州": "101280100",
        "成都": "101270100",
        "武汉": "101200100",
        "南京": "101190100",
        "苏州": "101190400",
        "全国": "100010000"
    }

    def _get_or_create_search_page(self) -> Page:
        """获取或定位最适合的 BOSS 直聘前台页面，并清理多余的 about:blank 标签页"""
        target_page = None
        
        # 1. 优先寻找已经打开 BOSS 直聘的标签页
        for p in self.context.pages:
            if "zhipin.com" in p.url:
                target_page = p
                break
        
        # 2. 若没有，寻找任意非 about:blank 标签页
        if not target_page:
            for p in self.context.pages:
                if p.url != "about:blank":
                    target_page = p
                    break

        # 3. 若仍没有，复用第 0 个标签页或新建
        if not target_page or target_page.is_closed():
            if len(self.context.pages) > 0:
                target_page = self.context.pages[0]
            else:
                target_page = self.context.new_page()

        self.search_page = target_page

        # 4. 关闭其他多余的 about:blank 空白标签页，防止视觉干扰
        for p in list(self.context.pages):
            if p != self.search_page and p.url == "about:blank":
                try:
                    p.close()
                except Exception:
                    pass

        # 5. 极其关键：将操作标签页激活到最前台，防止 Chrome 后台节流导致 React 停止渲染
        try:
            self.search_page.bring_to_front()
        except Exception:
            pass

        return self.search_page

    def scan_jobs_page(self, query: str, city_code: str = "101210100") -> Generator[RawJobCard, None, None]:
        """
        导航至 BOSS 直聘搜索页并提取岗位卡片数据 (支持多重选择器、前台激活与 URL 编码)
        """
        import urllib.parse

        page = self._get_or_create_search_page()

        # URL 编码防止中文和空格破坏检索参数
        encoded_query = urllib.parse.quote(query.strip())
        search_url = f"https://www.zhipin.com/web/geek/job?query={encoded_query}&city={city_code}"
        logger.info(f"Navigating to: {search_url}")
        
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
            page.bring_to_front()
        except Exception as e:
            logger.warning(f"页面加载通知: {e}")

        self.human_delay(2.0, 4.0)

        # 检查是否跳转到登录或验证页
        if "login" in page.url:
            logger.warning("⚠️ 当前页面处于未登录状态，请在 Chrome 窗口中使用手机 BOSS直聘 App 扫码登录！")
            self.human_delay(3.0, 5.0)

        self.check_and_handle_captcha(page)

        # 模拟真实鼠标滚轮向下滚动以触发数据懒加载
        try:
            page.mouse.wheel(0, random.randint(400, 800))
        except Exception:
            pass
        self.human_delay(1.5, 3.0)

        # 多重选择器兼容策略
        card_selectors = [
            ".job-card-wrapper",
            ".job-card-box",
            ".job-list-box li",
            "ul.job-list-box > li",
            "li.job-card-wrapper",
            "[class*='job-card-wrapper']",
            "[class*='job-card-box']",
            ".job-primary",
            ".job-card-body",
            ".job-card-left"
        ]

        # 等待列表元素渲染
        try:
            page.wait_for_selector(
                ", ".join(card_selectors),
                timeout=8000
            )
        except Exception:
            logger.info("等待列表选择器渲染完成...")

        job_elements = []
        for sel in card_selectors:
            try:
                elems = page.query_selector_all(sel)
                if elems and len(elems) > 0:
                    job_elements = elems
                    logger.info(f"成功匹配到选择器 [{sel}]，共 {len(elems)} 个岗位卡片")
                    break
            except Exception:
                pass

        logger.info(f"Found {len(job_elements)} job cards on current page.")

        def query_first(parent, selectors: List[str]):
            for s in selectors:
                try:
                    el = parent.query_selector(s)
                    if el:
                        return el
                except Exception:
                    pass
            return None

        for card in job_elements:
            if self.stop_event and self.stop_event.is_set():
                logger.info("⏹ 收到停止指令，中断岗位扫描！")
                break
            try:
                # 提取列表级基本信息
                title_elem = query_first(card, [".job-name", "[class*='job-name']", ".job-title", "span.name", "a.job-name"])
                company_elem = query_first(card, [".company-name", "[class*='company-name']", ".company-title", "a.company-name"])
                salary_elem = query_first(card, [".salary", "[class*='salary']", "span.salary", ".salary-text"])
                area_elem = query_first(card, [".job-area", "[class*='job-area']", ".company-location", "span.area"])

                if not (title_elem and company_elem and salary_elem):
                    continue

                title = title_elem.inner_text().strip()
                company = company_elem.inner_text().strip()
                salary = salary_elem.inner_text().strip()
                area = area_elem.inner_text().strip() if area_elem else ""

                # 点击卡片加载右侧详情
                try:
                    card.click(timeout=3000)
                except Exception:
                    pass
                self.human_delay(0.8, 1.5)
                self.check_and_handle_captcha(page)

                # 提取 JD 详情
                detail_sec = query_first(page, [
                    ".job-detail-section",
                    ".job-sec-text",
                    "[class*='job-detail']",
                    "[class*='detail-section']",
                    ".job-detail",
                    ".job-detail-box"
                ])
                jd_text = detail_sec.inner_text().strip() if detail_sec else ""

                hr_title_elem = query_first(page, [".boss-info-attr", "[class*='boss-info-attr']", ".boss-title"])
                hr_title = hr_title_elem.inner_text().strip() if hr_title_elem else "HR"
                
                hr_active_elem = query_first(page, [".boss-active-time", "[class*='boss-active-time']", ".active-time"])
                hr_active = hr_active_elem.inner_text().strip() if hr_active_elem else "刚刚活跃"

                # 构造唯一 ID
                job_id = f"{company}_{title}_{salary}_{area}"

                yield RawJobCard(
                    job_id=job_id,
                    job_title=title,
                    company_name=company,
                    salary_raw=salary,
                    city=area.split("·")[0] if "·" in area else area,
                    district=area.split("·")[1] if "·" in area else "",
                    jd_text=jd_text,
                    hr_title=hr_title,
                    hr_active_status=hr_active,
                    is_remote=("远程" in jd_text or "Remote" in jd_text)
                )

            except Exception as e:
                logger.error(f"Error parsing job card: {e}")
                continue

    def send_initial_greeting(self, greeting_text: str) -> bool:
        """点击【立即沟通】并发送定制开场白"""
        if not self.search_page:
            return False

        try:
            chat_btn = self.search_page.query_selector(".op-btn-chat")
            if not chat_btn:
                return False

            btn_text = chat_btn.inner_text().strip()
            if "继续沟通" in btn_text:
                logger.info("已处于沟通中状态，跳过发起。")
                return False

            logger.info("Clicking '立即沟通' button...")
            chat_btn.click()
            self.human_delay(2.0, 3.5)
            self.check_and_handle_captcha(self.search_page)

            # 模拟在弹出对话框中输入定制开场白 (若平台支持自定义文本)
            # 部分版本点击即直接发送默认打招呼，若有输入框则填入
            input_box = self.search_page.query_selector(".chat-input, textarea")
            if input_box and input_box.is_visible():
                self.human_type(self.search_page, ".chat-input, textarea", greeting_text)
                self.search_page.keyboard.press("Enter")
                self.human_delay(1.0, 2.0)

            return True
        except Exception as e:
            logger.error(f"Failed to send greeting: {e}")
            return False
