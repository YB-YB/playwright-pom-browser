# Playwright POM Browser

基于 Python + Playwright 的通用浏览器自动化框架。支持网页操作、数据抓取、表单填写、登录态复用、批量截图、文件上传下载、网络拦截及端到端流程验证。既可快速编写一次性脚本，也可演进为可维护的 Page Object 结构。

## 核心功能

- **浏览器控制** — 支持 Chromium、Firefox、WebKit，headed/headless 模式自由切换
- **页面操作** — 导航、点击、输入、选择、悬停、拖拽、键盘操作、文件上传
- **数据读取** — 文本、属性、输入框值、URL、标题、元素列表批量获取
- **等待与断言** — 可见性、文本内容、URL、标题、元素数量等条件等待
- **截图** — 全页面截图、元素级截图，自动管理输出目录
- **登录态复用** — 保存/加载 `storage_state`，避免重复登录
- **网络控制** — 请求拦截、资源阻止、接口响应等待
- **UI 框架适配** — LayUI、Element UI 等框架组件的模拟操作
- **表单联动识别** — 探测字段联动关系，识别动态显隐的必填字段
- **批量测试执行** — 用例隔离、结果验证、汇总报告

## 技术栈

| 组件 | 说明 |
|------|------|
| Python | >= 3.10 |
| Playwright | >= 1.40.0, < 2.0.0 |
| asyncio | 异步执行引擎 |
| unittest | 单元测试框架 |

## 环境要求

- Python 3.10 或更高版本
- 操作系统：Windows / macOS / Linux
- Linux headed 模式需要图形环境（DISPLAY），服务器环境建议使用 headless

## 安装步骤

### 1. 确认 Python 版本

```bash
python --version  # 需要 3.10+
```

### 2. 创建任务工作目录与虚拟环境

> 注意：不要在本项目目录内创建虚拟环境，应在独立的任务目录中操作。

**Linux / macOS：**

```bash
mkdir -p ~/browser-task && cd ~/browser-task
python -m venv .venv
.venv/bin/python -m pip install -r /path/to/playwright-pom-browser/scripts/requirements.txt
.venv/bin/python -m playwright install chromium
```

**Windows PowerShell：**

```powershell
New-Item -ItemType Directory -Force C:\browser-task
Set-Location C:\browser-task
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r C:\path\to\playwright-pom-browser\scripts\requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

### 3. 使用 setup.py 一键安装（可选）

```bash
python scripts/setup.py --browser chromium --venv /path/to/browser-task/.venv
```

支持的参数：
- `--browser` — 选择浏览器类型（chromium / firefox / webkit）
- `--install-all` — 安装所有浏览器
- `--venv` — 指定虚拟环境路径
- `--recreate-venv` — 重建已有虚拟环境
- `--check-only` — 仅检查环境状态，不执行安装

## 使用方法

### 运行冒烟测试

验证环境是否正确配置：

```bash
python scripts/run_test.py --headless
```

### 基于模板编写自动化脚本

复制 `scripts/template.py` 作为起点，修改 `run_task` 函数：

```python
async def run_task(page, manager: BrowserManager) -> None:
    browser = BrowserPage(page, manager.config)

    # 导航到目标页面
    await browser.navigate("https://example.com")
    await browser.wait_for_load_state("domcontentloaded")

    # 读取页面信息
    title = await browser.get_title()
    print(f"页面标题: {title}")

    # 填写表单
    await browser.fill("#username", "admin")
    await browser.fill("#password", "secret")
    await browser.click("button[type=submit]")

    # 截图保存
    await browser.screenshot("result.png")

    # 保存登录态供后续复用
    await manager.save_storage_state("auth.json")
```

### 命令行参数

所有脚本支持统一的 CLI 参数：

```
--headless          无头模式运行（默认）
--headed            显示浏览器窗口
--browser TYPE      浏览器类型：chromium / firefox / webkit
--timeout MS        全局超时（毫秒）
--navigation-timeout MS  导航超时（毫秒）
--base-url URL      基础 URL，支持路径导航如 /dashboard
--screenshot-dir DIR  截图保存目录
--storage-state PATH  登录态 JSON 文件路径
--viewport WxH      视口尺寸，如 1920x1080
--skip-env-check    跳过环境检查（CI 场景）
--install-missing   自动安装缺失依赖
```

### 环境变量配置

支持通过环境变量覆盖默认配置：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `BROWSER_HEADLESS` | 无头模式 | — |
| `BROWSER_TYPE` | 浏览器类型 | chromium |
| `BROWSER_TIMEOUT` | 全局超时(ms) | 30000 |
| `BROWSER_NAVIGATION_TIMEOUT` | 导航超时(ms) | 60000 |
| `BROWSER_VIEWPORT_WIDTH` | 视口宽度 | 1280 |
| `BROWSER_VIEWPORT_HEIGHT` | 视口高度 | 800 |
| `BROWSER_BASE_URL` | 基础 URL | — |
| `BROWSER_SCREENSHOT_DIR` | 截图目录 | ./screenshots |
| `BROWSER_DOWNLOAD_DIR` | 下载目录 | ./downloads |
| `BROWSER_STORAGE_STATE` | 登录态文件路径 | — |
| `BROWSER_PROBE_TIMEOUT` | 浏览器探测超时(s) | 120 |

## 项目结构

```
playwright-pom-browser/
├── SKILL.md                    # Skill 元数据与使用说明
├── README.md                   # 本文件
├── .gitignore
├── scripts/
│   ├── requirements.txt        # Python 依赖声明
│   ├── setup.py                # 环境一键安装脚本
│   ├── template.py             # 自动化脚本模板
│   ├── run_test.py             # 冒烟测试脚本
│   └── framework/              # 核心框架
│       ├── __init__.py
│       ├── base_page.py        # BrowserPage — 页面操作封装
│       ├── browser_manager.py  # BrowserManager — 浏览器生命周期管理
│       ├── config.py           # Config — 运行时配置
│       ├── cli.py              # CLI 参数解析
│       ├── runner.py           # 入口运行器
│       └── utils/              # 工具函数
│           ├── _logging.py     # 日志与输出
│           ├── _platform.py    # 平台检测
│           ├── _install.py     # 依赖安装
│           ├── _browser_detect.py  # 系统浏览器探测
│           └── _common.py      # 公共常量
├── tests/                      # 单元测试
│   ├── test_framework_logic.py
│   └── test_browser_detect.py
├── references/                 # 参考文档
│   ├── browser_automation.md
│   └── form_automation_methodology.md
└── screenshots/                # 截图输出目录（gitignore）
```

## 运行测试

```bash
cd /path/to/playwright-pom-browser
python -m pytest tests/ -v
```

## 注意事项

- 本框架不绕过验证码、风控、付费墙或网站访问限制
- 对受登录保护的网站，需提供合法账号或已保存的登录态
- 批量抓取任务应限制并发和访问频率，遵守目标网站条款
- CI 环境建议使用 `--headless --skip-env-check`，并在镜像中预装浏览器

## 贡献指南

1. Fork 本仓库
2. 在独立分支上开发：`git checkout -b feature/your-feature`
3. 确保所有测试通过：`python -m pytest tests/ -v`
4. 遵循项目编码规范（函数 ≤ 50 行、参数 ≤ 3 个、嵌套 ≤ 3 层）
5. 提交 Pull Request 并描述变更内容

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue 到项目仓库
- 邮件联系项目维护者
