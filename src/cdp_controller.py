"""Playwright CDP Browser Controller for real Chrome connection, human-like interaction, and DOM/XHR scraping."""
import os
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
    """真实 Chrome CDP 浏览器控制器 (支持 CDP 直连 + 自动拉起有头浏览器自愈)"""
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
        """连接到带有 --remote-debugging-port 的 Chrome 实例，若未启动则自动自愈拉起有头浏览器"""
        logger.info(f"Connecting to Chrome via CDP: {self.cdp_url} ...")
        self._playwright = sync_playwright().start()
        
        # 1. 优先尝试直接连接已存在的 9222 CDP 调试端口
        try:
            self.browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
            self.context = self.browser.contexts[0]
            logger.info("✅ 成功连接到前台已运行的 Chrome CDP 实例！")
            return
        except Exception as e:
            logger.warning(f"CDP 端口 {self.cdp_url} 未就绪 ({e})，正在自动为您启动桌面可视化有头 Chrome 浏览器...")

        # 2. 若未启动，全自动在桌面拉起有头 Chrome 窗口 (无需用户手动开命令行)
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        chosen_exe = None
        for cp in chrome_paths:
            if os.path.exists(cp):
                chosen_exe = cp
                break
                
        user_data_dir = r"C:\chrome_debug_profile"
        try:
            self.context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path=chosen_exe,
                headless=False,
                viewport={"width": 1440, "height": 900},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check"
                ]
            )
            # 立即让弹出的窗口导航到 BOSS 直聘首页，绝不留在 about:blank
            init_page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.search_page = init_page
            try:
                init_page.goto("https://www.zhipin.com", wait_until="domcontentloaded", timeout=15000)
                init_page.bring_to_front()
            except Exception:
                pass
            logger.info(f"🎉 成功自动为您在桌面启动有头 Chrome 浏览器并打开 BOSS 直聘！")
        except Exception as launch_err:
            logger.error(f"自动启动 Chrome 失败: {launch_err}")
            raise RuntimeError(f"无法自动拉起 Chrome 浏览器: {launch_err}") from launch_err

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
        # 核心直辖市与重点经济中心
        "全国": "100010000",
        "北京": "101010100",
        "上海": "101020100",
        "广州": "101280100",
        "深圳": "101280600",
        "杭州": "101210100",
        "成都": "101270100",
        "武汉": "101200100",
        "南京": "101190100",
        "苏州": "101190400",
        "重庆": "101040100",
        "西安": "101110100",
        "合肥": "101220100",
        "郑州": "101180100",
        "贵阳": "101260100",
        # 湖南省全地级市覆盖
        "怀化": "101251200",
        "长沙": "101250100",
        "株洲": "101250300",
        "湘潭": "101250200",
        "衡阳": "101250400",
        "邵阳": "101250900",
        "岳阳": "101251000",
        "常德": "101250600",
        "张家界": "101251100",
        "益阳": "101250700",
        "郴州": "101250500",
        "永州": "101251400",
        "娄底": "101250800",
        "湘西": "101251500",
        "吉首": "101251500",
        "铜仁": "101260600"
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

    def build_boss_url(
        self,
        search_mode: str = "recommend",
        query: Optional[str] = None,
        city_code: str = "101210100",
        filters: Optional[Dict[str, Any]] = None,
        page_num: int = 1
    ) -> str:
        """
        根据检索模式与多维筛选矩阵动态生成 BOSS 直聘标准 URL
        """
        import urllib.parse

        filters = filters or {}
        
        # 1. 智能推荐流模式 (无需输入任何关键词，BOSS 千人千面算法专属推荐)
        if search_mode == "recommend":
            base = "https://www.zhipin.com/web/geek/job-recommend"
            params = []
            if city_code and city_code != "100010000":
                params.append(f"city={city_code}")
            if params:
                return f"{base}?{'&'.join(params)}"
            return base

        # 2. 条件筛选池 / 关键词检索模式
        base = "https://www.zhipin.com/web/geek/job"
        params = [f"city={city_code}"]

        if query and query.strip():
            params.append(f"query={urllib.parse.quote(query.strip())}")

        exp = filters.get("experience", [])
        if exp:
            exp_val = ",".join(exp) if isinstance(exp, list) else str(exp)
            params.append(f"experience={exp_val}")

        deg = filters.get("degree", [])
        if deg:
            deg_val = ",".join(deg) if isinstance(deg, list) else str(deg)
            params.append(f"degree={deg_val}")

        scale = filters.get("scale", [])
        if scale:
            scale_val = ",".join(scale) if isinstance(scale, list) else str(scale)
            params.append(f"scale={scale_val}")

        stage = filters.get("stage", [])
        if stage:
            stage_val = ",".join(stage) if isinstance(stage, list) else str(stage)
            params.append(f"stage={stage_val}")

        salary = filters.get("salary", [])
        if salary:
            salary_val = ",".join(salary) if isinstance(salary, list) else str(salary)
            params.append(f"salary={salary_val}")

        job_type = filters.get("job_type", "1901")
        if job_type:
            params.append(f"jobType={job_type}")

        if page_num > 1:
            params.append(f"page={page_num}")

        return f"{base}?{'&'.join(params)}"

    def scan_jobs_page(
        self,
        query: Optional[str] = None,
        city_code: str = "101210100",
        search_mode: str = "recommend",
        filters: Optional[Dict[str, Any]] = None,
        page_num: int = 1
    ) -> Generator[RawJobCard, None, None]:
        """
        导航至 BOSS 直聘岗位池（支持智能推荐、条件筛选池与关键词搜索）并提取岗位卡片
        """
        page = self._get_or_create_search_page()

        search_url = self.build_boss_url(
            search_mode=search_mode,
            query=query,
            city_code=city_code,
            filters=filters,
            page_num=page_num
        )
        logger.info(f"Navigating to [{search_mode}]: {search_url}")
        
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
            # 兼容 BOSS 直聘全部版本与 DOM 结构的【立即沟通】按钮选择器
            chat_btn_selectors = [
                ".btn-startchat",
                "a:has-text('立即沟通')",
                "button:has-text('立即沟通')",
                ".op-btn-chat",
                ".op-btn .btn-startchat",
                "[class*='btn-startchat']",
                ".job-detail-box .btn-startchat"
            ]
            
            chat_btn = None
            for sel in chat_btn_selectors:
                try:
                    btn = self.search_page.query_selector(sel)
                    if btn and btn.is_visible():
                        chat_btn = btn
                        break
                except Exception:
                    pass

            if not chat_btn:
                logger.info("未在当前卡片详情页找到【立即沟通】按钮，可能已沟通过或正在加载。")
                return False

            btn_text = chat_btn.inner_text().strip()
            if "继续沟通" in btn_text:
                logger.info("该岗位已处于沟通中状态，跳过重复发起。")
                return False

            logger.info(f"🚀 点击【立即沟通】按钮 (文字: {btn_text}) ...")
            chat_btn.click()
            self.human_delay(2.0, 3.5)
            self.check_and_handle_captcha(self.search_page)

            # 处理 BOSS 直聘打招呼确认弹窗 (如：您正在发起沟通 / 确认发送)
            confirm_dialog_selectors = [
                ".dialog-startchat .btn-sure",
                ".dialog-container .btn-sure",
                ".dialog-wrap button:has-text('确定')",
                ".dialog-wrap button:has-text('发送')",
                "button:has-text('确认沟通')",
                ".chat-input-dialog .btn-sure"
            ]
            for c_sel in confirm_dialog_selectors:
                try:
                    confirm_btn = self.search_page.query_selector(c_sel)
                    if confirm_btn and confirm_btn.is_visible():
                        logger.info(f"👉 确认打招呼弹窗并点击发送: {c_sel}")
                        confirm_btn.click()
                        self.human_delay(1.0, 2.0)
                        break
                except Exception:
                    pass

            # 模拟在弹出对话框中输入定制开场白 (若平台支持自定义文本)
            input_box = self.search_page.query_selector(".chat-input, textarea, .dialog-chat-input")
            if input_box and input_box.is_visible():
                self.human_type(self.search_page, ".chat-input, textarea, .dialog-chat-input", greeting_text)
                self.search_page.keyboard.press("Enter")
                self.human_delay(1.0, 2.0)

            logger.info("✅ 成功向 HR 发起【立即沟通】！")
            return True
        except Exception as e:
            logger.error(f"Failed to send greeting: {e}")
            return False
