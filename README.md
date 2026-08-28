# AI Agent 智能求职自动化与多轮沟通系统

> **一站式搞定“智能筛选 $\rightarrow$ 定制打招呼/投递 $\rightarrow$ 基础信息摸底 $\rightarrow$ 自定义多轮追问 $\rightarrow$ 飞书/微信人机协同”的全流程求职助手。**

---

## 📖 项目定位与核心优势

本项目基于 **真实 Chrome + CDP (Chrome DevTools Protocol) + Python + DeepSeek + 飞书/微信 Webhook** 打造，旨在为求职者提供一套**高稳定性、零封号风险、精准匹配、信息透明**的智能化求职闭环。

### 🌟 核心特色
1. **真实浏览器 CDP 直连（极低风控）**：复用日常 Chrome 浏览器的登录态、Cookie、指纹与扩展插件，零 WebDriver 自动化指纹。
2. **多城市与四级空间地理辐射筛选**：
   - **Tier 1 本地通勤圈（$\le 10\text{km}$）**：家门口通勤神仙岗，适度放宽门槛。
   - **Tier 2 邻近核心地级市**：同城高铁都市圈覆盖。
   - **Tier 3 省内中心城市**：薪资溢价覆盖异地租房成本。
   - **Tier 4 全国优质机会 / 远程办公（Remote）**：专属绿色通道，最高优先级。
3. **全方位基础工作信息摸底（拒绝信息不对称）**：
   - AI 自动在多轮沟通中摸清：**薪资结构（Base/绩效/年终）、试用期打折与五险一金缴纳、工作时间（965/996/大小周/弹性）、业务属性（自研 vs 外包驻场）、办公地点**。
4. **职位类别与单岗位自定义追问引擎**：
   - **类别级模板**：针对 AI 岗、后端架构岗、前端岗定制专业技术与业务痛点提问。
   - **岗位级覆写**：针对特定公司/团队指定专属问题。
   - **渐进式拟人化提问**：杜绝“查户口式”审讯，采用自然、礼貌的交谈节奏。
5. **人机协同（HITL）与熔断防护**：
   - 关键节点（面试邀约、索要微信/电话、薪资谈判、滑块验证码）自动暂停并推送飞书/微信，人工无缝接管。

---

## 📂 项目目录结构

```
d:\招聘\
├── .gitignore                           # Git 忽略配置
├── README.md                            # 项目全景概览
├── docs/                                # 系统核心技术与业务规范
│   ├── 01_architecture_design.md        # 系统全层级架构与 CDP 控制机制
│   ├── 02_screening_strategy.md         # 多城市四级地理与多维筛选过滤规范
│   ├── 03_dialogue_and_inquiry_engine.md# 多轮沟通状态机、基础信息核实与自定义追问规范
│   └── 04_risk_control_and_safety.md    # 平台防封号与拟人化风控实践手册
├── config/                              # 配置模板体系
│   ├── cities.yaml                      # 多城市与空间辐射圈配置
│   ├── candidate_profile.yaml           # 候选人标准简历画像与事实边界库
│   ├── inquiry_templates.yaml           # 职位类别与单岗位自定义追问模板
│   └── blacklist.yaml                   # 企业、行业与套路关键词黑名单
└── src/                                 # 核心代码架构
    ├── __init__.py
    ├── config_loader.py                 # 配置加载与 Pydantic 校验器
    └── schemas.py                       # 数据模型与枚举定义
```

---

## 🚀 快速启动指引

### 1. 环境准备
* Python 3.10+
* Google Chrome 浏览器

### 2. 启动带调试端口的日常 Chrome 浏览器
在终端执行以下命令（启动前请先关闭所有 Chrome 窗口）：

```bash
# Windows
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
```
在打开的 Chrome 中打开 [BOSS直聘](https://www.zhipin.com) 并手动扫码登录。

### 3. 配置项目参数
根据个人情况修改 `config/` 目录下的配置文件：
1. `config/candidate_profile.yaml`：填入你的技术履历、亮点项目、期望薪资底线。
2. `config/cities.yaml`：填入你的居住地坐标与目标城市辐射规则。
3. `config/inquiry_templates.yaml`：配置你想让 AI 代问的问题。

---

## 📜 开源参考与致谢
本项目在架构与风控设计上深度参考并汲取了以下开源项目的优秀实践：
* **`longsizhuo/BossZhiPin_Job_Search`**（CDP 架构与轻量 LLM 交互）
* **`jolie-z/Auto-JobHunter`**（多 Agent 协作与飞书数据看板）
* **`WenYu0306/Orchestra`**（网络数据监听与多平台适配）
