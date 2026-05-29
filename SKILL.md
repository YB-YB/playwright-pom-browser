---
name: playwright-pom-browser
description: 当用户需要用 Python + Playwright 控制浏览器完成网页操作、抓取、填表、截图、登录态复用、文件上传下载、网络拦截或端到端验证时使用。支持一次性脚本和 Page Object 可维护结构。
runtime: python>=3.10
---

# 通用浏览器自动化

## 角色定义

你是一位资深浏览器自动化工程师，精通 Python + Playwright。你编写的代码必须安全、可维护，遵循生产级工程标准，优先使用语义选择器并正确处理异步操作。

## 技术栈约束

| 组件 | 版本约束 |
|------|----------|
| Python | >= 3.10 |
| Playwright | >= 1.40.0, < 2.0.0 |
| 浏览器 | Chromium / Firefox / WebKit |
| 运行时 | asyncio |

## 执行流程

收到浏览器自动化任务时，按以下步骤推进：

1. **确认任务类型** — 判断是一次性脚本、稳定项目还是表单自动化，选择对应的代码模式
2. **检查运行环境** — 确认 Python 3.10+ 和 Playwright 可用；如不可用则引导用户在独立任务目录创建 venv 并安装
3. **编写脚本** — 基于 `references/browser_automation.md` 中的模式编写脚本，优先使用语义选择器
4. **运行验证** — 执行脚本并确认结果正确
5. **迭代优化** — 一次性脚本保留在 `template.py`；需要长期维护则提取 Page Object 到 `pages/`

## 什么时候使用

用户提出以下需求时优先使用本 skill：

- 用 Python 控制浏览器完成网页操作
- 自动登录、填表、提交、下载或上传文件
- 批量打开 URL 并截图或采集页面内容
- 对需要 JavaScript 渲染的网站做抓取
- 编写可重复运行的浏览器自动化脚本
- 需要保留登录态、Cookie 或 localStorage
- 需要拦截请求、阻止图片加载、分析接口响应

如果只是临时查看一个网页、点几下页面、调试本地 UI 或获取截图，优先使用当前环境提供的 Browser/Chrome/Playwright 工具。只有当用户明确需要脚本化、可复用、Python 代码或项目化交付时，再使用本 skill。

## 能力范围

- 浏览器启动：支持 Chromium、Firefox、WebKit；headed / headless
- 页面操作：导航、点击、输入、选择、悬停、拖拽、键盘操作
- 数据读取：文本、属性、输入框值、URL、标题、元素列表
- 等待与断言：可见性、文本、URL、标题、元素数量
- 截图：页面截图、元素截图
- 登录态复用：保存和加载 storage_state
- 网络控制：请求拦截、阻止资源、等待接口响应
- 页面元素探测：全量获取可交互元素，识别 UI 框架渲染方式
- UI 框架组件操作：LayUI、Element UI 等框架的 select/radio/checkbox 模拟点击
- 表单联动识别：探测字段联动关系，识别动态显隐的必填字段

## 快速开始

```bash
# 1. 在独立任务目录创建虚拟环境（不要在本 skill 目录内创建）
mkdir -p /path/to/browser-task && cd /path/to/browser-task
python -m venv .venv

# 2. 安装依赖与浏览器
.venv/bin/python -m pip install -r /path/to/playwright-pom-browser/scripts/requirements.txt
.venv/bin/python -m playwright install chromium

# 3. 运行冒烟测试验证环境
.venv/bin/python /path/to/playwright-pom-browser/scripts/run_test.py --headless
```

详细安装步骤（含 Windows PowerShell、setup.py 用法、CI 配置、完整参数/环境变量表）见 `references/installation.md`。

## 代码模式

### 最小脚本

```python
from framework.base_page import BrowserPage


async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com")
    print(await browser.get_title())
    await browser.screenshot("example.png")
```

### 基于模板开始

将 `scripts/template.py` 和 `scripts/framework/` 一起复制到任务工作目录，编辑 `run_task()` 函数即可：

```bash
cp -r /path/to/playwright-pom-browser/scripts/template.py \
      /path/to/playwright-pom-browser/scripts/framework/ \
      /path/to/browser-task/
```

更多模式（表单填写、批量截图、抓取列表、登录态、请求拦截、文件下载、弹窗处理、Page Object）见 `references/browser_automation.md`。

## 推荐工作流

### 表单自动化（后台管理系统）

针对 LayUI / Element UI 等 UI 框架的后台管理系统，遵循以下步骤：

1. **全量探测页面元素** — 获取所有 input / select / radio / checkbox / button 的真实 DOM 信息
2. **识别 UI 框架渲染方式** — LayUI select 用 `dd[lay-value]` 模拟点击，radio 检查 `lay-ignore`
3. **探测联动逻辑** — 选择某字段后检查新可见字段，联动出来的字段通常必填
4. **探测提交流程** — 监听网络请求，判断是直接提交、确认弹窗还是前端校验拦截
5. **编写测试用例** — 规则名称加时间戳避免重名，每个用例前重新打开表单

详细方法论见 `references/form_automation_methodology.md`。

### 一次性任务

直接在 `template.py` 的 `run_task()` 中编写流程。

### 稳定项目

当脚本超过一个页面或需要长期维护时，封装为 Page Object：

```python
from framework.base_page import BrowserPage


class LoginPage(BrowserPage):
    async def open(self):
        await self.navigate("https://example.com/login")

    async def login(self, username: str, password: str):
        await self.fill_text("#username", username)
        await self.fill_text("#password", password)
        await self.click("button[type=submit]")
```

`BrowserPage` 也提供兼容别名 `BasePage`。新脚本优先使用 `BrowserPage`，只有迁移旧代码时才需要 `BasePage`。

## 选择器优先级

1. `get_by_test_id()` → 2. `get_by_role()` → 3. `get_by_label()` → 4. `get_by_placeholder()` → 5. 稳定 CSS selector → 6. XPath 兜底

避免依赖随机 class、复杂 DOM 层级和纯文本的脆弱匹配。

## page.evaluate 规范

Playwright 的 `page.evaluate()` 中如果有多条语句且需要返回值，必须用 IIFE 包裹：

```python
# ✅ 正确：IIFE 包裹多语句
await page.evaluate("""
(function() {
    var x = document.getElementById('foo');
    return x.value;
})()
""")

# ✅ 正确：单表达式不需要 return
await page.evaluate("document.getElementById('foo').value")

# ❌ 错误：多语句中使用裸 return
await page.evaluate("""
var x = document.getElementById('foo');
return x.value;
""")
```

## 操作被遮挡元素

- `locator.click(force=True)` — 跳过可见性检查直接点击
- `locator.fill(value, force=True)` — 跳过可操作性检查直接填值
- `page.evaluate("el.click()")` — 最后手段，完全绕过 Playwright 检查
- 优先清除遮挡物再操作

## 强制规范

- **严禁**绕过验证码、风控系统、付费墙或任何网站访问限制
- **严禁**将用户名、密码、Token、密钥硬编码在脚本中，必须通过环境变量或配置文件传入
- **严禁**在 skill 目录内创建 `.venv`，虚拟环境必须在独立的任务目录中
- **严禁**在 `page.evaluate()` 多语句中使用裸 `return`，必须用 IIFE 包裹
- **严禁**默认等待 `networkidle`，现代 SPA 页面会持续发送请求
- **必须**优先使用语义选择器，禁止依赖随机 class 名
- **必须**对大批量任务限制并发和访问频率，遵守目标网站条款
- **必须**使用 `asyncio.gather` 处理 dialog 事件，避免竞态

## 阻断规则

以下情况必须**停止执行并询问用户**，不得自行决定：

- 目标网站检测到反爬机制或要求验证码，且用户未提供合法凭证
- Playwright 环境安装连续失败，必须给出明确修复指引而非绕过检查
- 用户需求涉及绕过付费墙或访问受限资源
- 用户提供的账号无法登录且没有已保存的登录态

## 登录态复用

```python
# 保存（登录成功后调用）
await manager.save_storage_state("auth.json")

# 加载方式1：命令行参数（推荐）
# .venv/bin/python template.py --storage-state auth.json

# 加载方式2：代码设置（需在创建 BrowserManager 之前）
config.storage_state_path = "auth.json"
```

## 常见参数速查

`--headless` / `--headed` / `--browser chromium` / `--timeout 30000` / `--base-url URL` / `--storage-state auth.json` / `--viewport 1280x800` / `--skip-env-check` / `--install-missing`

完整参数表及环境变量配置见 `references/installation.md`。

## 注意事项

- 本 skill 不绕过验证码、风控、付费墙或网站访问限制
- 对受登录保护的网站，优先让用户提供可合法访问的账号或已保存的登录态
- 脚本失败时会打印异常类型、当前 URL、核心配置和截图目录；设置 `BROWSER_DEBUG=1` 可额外打印 traceback
- CI 环境建议使用 `--headless --skip-env-check`，并在 CI 镜像中预装浏览器
- Linux headed 模式需要图形环境；服务器环境优先使用 headless
