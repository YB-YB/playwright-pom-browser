---
name: playwright-pom-browser
description: General browser automation skill using Python + Playwright. Use when you need to open webpages, scrape content, fill forms, reuse login state, batch screenshots, upload/download files, intercept network requests, or validate end-to-end flows. Supports both one-off scripts and evolving into maintainable Page Object structures. 通用浏览器自动化 skill，用于需要用 Python + Playwright 完成网页操作、抓取、填表、登录复用、截图、文件上传下载、网络拦截或端到端流程验证的任务。
runtime: python>=3.10
---

# 通用浏览器自动化

这是一个基于 Python + Playwright 的通用浏览器自动化 skill。目标不是强制用户采用某一种测试框架，而是让模型能快速完成真实浏览器任务：打开网页、等待内容、点击输入、抓取数据、截图、登录态复用、文件上传下载、网络拦截，以及把一次性脚本逐步整理成可维护代码。

本文件使用 UTF-8 编码。Windows PowerShell 查看中文文档时，建议显式指定编码：

```powershell
Get-Content -Raw -Encoding UTF8 .\SKILL.md
```

## 什么时候使用

用户提出以下需求时优先使用本 skill：

- 用 Python 控制浏览器完成网页操作
- 自动登录、填表、提交、下载或上传文件
- 批量打开 URL 并截图或采集页面内容
- 对需要 JavaScript 渲染的网站做抓取
- 编写可重复运行的浏览器自动化脚本
- 需要保留登录态、Cookie 或 localStorage
- 需要拦截请求、阻止图片加载、分析接口响应
- 需要把一次性浏览器操作沉淀为可维护项目

如果只是临时查看一个网页、点几下页面、调试本地 UI 或获取截图，优先使用当前环境提供的 Browser/Chrome/Playwright 工具。只有当用户明确需要脚本化、可复用、Python 代码或项目化交付时，再使用本 skill。

## 能力范围

- 环境检查：检查 Playwright 包和浏览器是否可用，并给出安装命令
- 浏览器启动：支持 Chromium、Firefox、WebKit；支持 headed/headless
- 页面操作：导航、点击、输入、选择、悬停、上传、拖拽、键盘操作
- 数据读取：文本、属性、输入框值、URL、标题、元素列表
- 等待与断言：可见性、文本、URL、标题、元素数量
- 截图：页面截图、元素截图，自动创建 `screenshots/`
- 登录态复用：保存和加载 `storage_state`
- 网络控制：请求拦截、阻止资源、等待接口响应
- 可维护结构：可选使用 Page Object，但不强制
- **页面元素探测**：全量获取页面可交互元素（input/select/radio/checkbox/button），识别 UI 框架渲染方式
- **UI 框架组件操作**：LayUI、Element UI 等框架的 select/radio/checkbox 模拟点击
- **表单联动识别**：探测字段联动关系，识别动态显隐的必填字段
- **提交流程处理**：处理确认弹窗、前端校验拦截、异步 API 响应
- **批量测试用例执行**：用例隔离、结果验证、汇总报告

## 快速开始

### 1. 确认 Python

本 skill 需要 Python 3.10+。优先使用 `python` 命令。

```bash
python --version
```

### 2. 创建任务环境并安装依赖

不要把虚拟环境创建到本 skill 目录中，也不要把 `.venv` 当作 skill 内容交付。先确定本次浏览器自动化任务的工作目录，在该目录下创建名为 `.venv` 的独立 Python 虚拟环境；后续安装依赖、运行脚本和保存截图/登录态都应在这个任务环境中完成。

```bash
mkdir -p /path/to/browser-task
cd /path/to/browser-task
python -m venv .venv
.venv/bin/python -m pip install -r /path/to/playwright-pom-browser/scripts/requirements.txt
.venv/bin/python -m playwright install chromium
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force C:\path\to\browser-task
Set-Location C:\path\to\browser-task
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r C:\path\to\playwright-pom-browser\scripts\requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

如果希望复用本 skill 的安装辅助脚本，也必须显式把 `--venv` 指向任务工作目录下的环境，而不是使用 skill 内部目录：

```bash
cd /path/to/playwright-pom-browser/scripts
python setup.py --browser chromium --venv /path/to/browser-task/.venv
```

Windows PowerShell：

```powershell
Set-Location C:\path\to\playwright-pom-browser\scripts
python setup.py --browser chromium --venv C:\path\to\browser-task\.venv
```

只检查任务环境，不安装：

```bash
python setup.py --check --venv /path/to/browser-task/.venv
```

如果任务环境已损坏，可显式重建。该操作只允许用于一个已有 `pyvenv.cfg` 的虚拟环境目录：

```bash
python setup.py --browser chromium --venv /path/to/browser-task/.venv --recreate-venv
```

安装全部浏览器：

```bash
python setup.py --all --venv /path/to/browser-task/.venv
```

Linux 环境如缺少浏览器系统依赖，可加 `--with-deps`：

```bash
python setup.py --browser chromium --with-deps --venv /path/to/browser-task/.venv
```

### 3. 运行通用示例

从本 skill 的 `scripts` 目录运行内置 smoke test 时，也使用任务环境中的 Python：

```bash
/path/to/browser-task/.venv/bin/python /path/to/playwright-pom-browser/scripts/run_test.py --headless
# Windows PowerShell:
C:\path\to\browser-task\.venv\Scripts\python.exe C:\path\to\playwright-pom-browser\scripts\run_test.py --headless
```

示例默认打开内置 `data:` 页面，读取标题，并保存截图；需要访问真实站点时可传 `--url https://example.com`。

### 4. 创建自己的脚本

**重要**：`template.py` 依赖 `framework/` 目录，复制时必须一起拷贝：

```bash
# 方案 A：连 framework 一起复制（推荐）
cp -r /path/to/playwright-pom-browser/scripts/template.py /path/to/playwright-pom-browser/scripts/framework/ /path/to/browser-task/
```

Windows PowerShell：

```powershell
Copy-Item C:\path\to\playwright-pom-browser\scripts\template.py, C:\path\to\playwright-pom-browser\scripts\framework -Destination C:\path\to\browser-task -Recurse
```

```bash
# 方案 B：直接在本 skill 的 scripts 目录里创建脚本，通过本地 framework 引用
cd /path/to/playwright-pom-browser/scripts
cp template.py browser_task.py
```

复制到任务目录后，确保 `framework/` 目录在 `browser_task.py` 或 `template.py` 同级，并使用任务环境里的 Python 运行：

```text
/path/to/browser-task/
  .venv/
  browser_task.py
  framework/
    __init__.py
    base_page.py
    browser_manager.py
    config.py
    cli.py
    utils.py
```

```bash
.venv/bin/python browser_task.py --headless
# Windows PowerShell:
.\.venv\Scripts\python.exe browser_task.py --headless
```

然后编辑 `run_task()`：

```python
async def run_task(page, manager):
    helper = BrowserPage(page, manager.config)
    await helper.navigate("https://example.com")
    print(await helper.get_title())
    await helper.screenshot("example.png")
```

`BrowserPage` 也提供兼容别名 `BasePage`。新脚本优先使用 `BrowserPage`，只有迁移旧代码时才需要 `BasePage`。

## 推荐工作流

### 表单自动化（后台管理系统）

针对 LayUI / Element UI 等 UI 框架的后台管理系统，遵循以下步骤：

**Step 1：全量探测页面元素**

创建环境后，第一件事是获取目标页面所有可交互元素。不要假设页面结构。

```python
# 打开目标表单后，获取所有 input/select/radio/checkbox/button
info = await page.evaluate("""
(function() {
    var result = {inputs: [], selects: [], radios: [], checkboxes: [], buttons: []};
    document.querySelectorAll('input').forEach(function(el) {
        result.inputs.push({id: el.id, name: el.name, type: el.type,
            placeholder: el.placeholder, required: el.required,
            visible: el.offsetParent !== null});
    });
    document.querySelectorAll('select').forEach(function(el) {
        result.selects.push({id: el.id, name: el.name,
            layFilter: el.getAttribute('lay-filter'),
            options: Array.from(el.options).map(function(o) { return {value: o.value, text: o.text}; })});
    });
    // ... radio, checkbox, button 同理
    return result;
})()
""")
```

**Step 2：识别 UI 框架渲染方式**

- LayUI select → 原生 select 被隐藏，操作 `dd[lay-value]` 元素
- LayUI radio → 检查是否有 `lay-ignore`，决定直接点击还是点外层容器
- 确认弹窗 → `layer.confirm` 的按钮顺序由 `btn` 数组决定

**Step 3：探测联动逻辑**

选择某个字段后检查哪些新字段变为可见。联动出来的字段通常是必填的。

**Step 4：探测提交流程**

监听网络请求，确认提交后是否有确认弹窗、是否直接发 API、是否被前端校验拦截。

**Step 5：编写测试用例**

- 规则名称加场景+时间戳避免重名
- 每个用例前关闭弹窗重新打开表单
- 成功判定：表单关闭 / 失败判定：表单仍打开

详细方法论见 `references/form_automation_methodology.md`。

### 一次性任务

直接在 `template.py` 的 `run_task(page, manager)` 中写流程。适合临时抓取、批量截图、简单填表。

### 稳定任务

当脚本超过一个页面或需要长期维护时，把页面相关逻辑放进 `pages/`：

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

推荐结构：

```text
my_browser_task/
  browser_task.py
  pages/
    __init__.py
    login_page.py
  data/
    input.csv
  screenshots/
  auth.json
```

## 命令行参数

`run_test.py` 和 `template.py` 支持：

| 参数 | 说明 |
| --- | --- |
| `--headless` | 无头模式运行 |
| `--headed` | 有头模式运行 |
| `--interactive` | 未指定 headed/headless 时交互式询问运行模式 |
| `--browser chromium` | 指定浏览器，支持 `chromium` / `firefox` / `webkit` |
| `--timeout 30000` | 全局超时，单位毫秒 |
| `--navigation-timeout 60000` | 导航超时，单位毫秒 |
| `--base-url https://example.com` | 设置基础 URL，可在脚本里导航到 `/path` |
| `--screenshot-dir screenshots` | 设置截图保存目录 |
| `--storage-state auth.json` | 加载已保存的 Playwright 登录态 |
| `--viewport 1280x800` | 设置浏览器视口尺寸 |
| `--browser-probe-timeout 120` | 浏览器可用性检查的启动超时，单位秒 |
| `--skip-env-check` | 跳过环境检查 |
| `--install-missing` | 环境缺失时自动安装 `requirements.txt` 中的 Python 依赖和 Playwright 浏览器；只应在任务目录的虚拟环境中使用 |
| `--recreate-venv` | `setup.py` 专用；删除并重建指定的任务虚拟环境，目标目录必须是已有虚拟环境 |

默认运行模式是 headless；默认行为是只检查环境并给出安装建议，不会静默下载依赖。

脚本失败时会打印异常类型、当前 URL、核心配置和截图目录；如需 traceback，设置 `BROWSER_DEBUG=1` 后重跑。

## 环境变量

| 变量 | 作用 | 示例 |
| --- | --- | --- |
| `BROWSER_HEADLESS` | 强制 headed/headless | `true` / `false` |
| `BROWSER_TYPE` | 指定浏览器 | `chromium` / `firefox` / `webkit` |
| `BROWSER_TIMEOUT` | 全局超时，单位毫秒 | `30000` |
| `BROWSER_NAVIGATION_TIMEOUT` | 导航超时，单位毫秒 | `60000` |
| `BROWSER_VIEWPORT_WIDTH` | 视口宽度，单位像素 | `1280` |
| `BROWSER_VIEWPORT_HEIGHT` | 视口高度，单位像素 | `800` |
| `BROWSER_BASE_URL` | 基础 URL | `https://example.com` |
| `BROWSER_SCREENSHOT_DIR` | 截图目录 | `screenshots` |
| `BROWSER_LOCALE` | 浏览器上下文 locale，不设置则使用 Playwright 默认值 | `zh-CN` |
| `BROWSER_USER_AGENT` | 自定义 User-Agent | `Mozilla/5.0 ...` |
| `BROWSER_STORAGE_STATE` | 登录态文件 | `auth.json` |
| `BROWSER_ACCEPT_DOWNLOADS` | 是否接受下载 | `true` / `false` |
| `BROWSER_PROBE_TIMEOUT` | 浏览器可用性检查的启动超时，单位秒 | `120` |
| `BROWSER_SKIP_ENV_CHECK` | 跳过环境检查 | `1` |
| `BROWSER_DEBUG` | 失败时额外打印 traceback | `1` |

## 登录态复用

首次登录后保存：

```python
await manager.save_storage_state("auth.json")
```

后续运行时加载，优先用命令行参数：

```bash
.venv/bin/python template.py --storage-state auth.json
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe template.py --storage-state auth.json
```

也可以在代码里设置；需要放在创建 `BrowserManager(config)` 之前：

```python
config.storage_state_path = "auth.json"
async with BrowserManager(config) as manager:
    await manager.create_context()
    page = await manager.create_page()
```

## 下载与接口响应

点击后保存下载：

```python
path = await browser.download_by_click("a.download")
# 大文件可指定超时（毫秒）
path = await browser.download_by_click("a.download", timeout=120000)
```

等待指定接口响应：

```python
response = await browser.wait_for_response(
    "**/api/items",
    action=lambda: browser.click("#load-items"),
)
data = await response.json()
```

## 选择器建议

优先级从高到低：

1. `get_by_test_id()`
2. `get_by_role()`
3. `get_by_label()`
4. `get_by_placeholder()`
5. 稳定 CSS selector
6. XPath 兜底

避免依赖随机 class、复杂 DOM 层级和纯文本的脆弱匹配。

## page.evaluate 规范

Playwright 的 `page.evaluate()` 中如果有多条语句且需要返回值，必须用 IIFE 包裹：

```python
# ❌ 错误：裸 return 会报 "return not in function"
await page.evaluate("""
var x = document.getElementById('foo');
return x.value;
""")

# ✅ 正确：IIFE 包裹
await page.evaluate("""
(function() {
    var x = document.getElementById('foo');
    return x.value;
})()
""")

# ✅ 正确：单表达式不需要 return
await page.evaluate("document.getElementById('foo').value")
```

## 操作被遮挡元素

当元素被弹窗遮罩、下拉框等覆盖时：

- `locator.click(force=True)` — 跳过可见性检查直接点击
- `locator.fill(value, force=True)` — 跳过可操作性检查直接填值
- `page.evaluate("el.click()")` — 最后手段，完全绕过 Playwright 的检查
- 优先清除遮挡物（`close_all_layers`）再操作

## 注意事项

- 本 skill 不绕过验证码、风控、付费墙或网站访问限制。
- 对受登录保护的网站，优先让用户提供可合法访问的账号或已保存的登录态。
- 对大批量抓取任务，应限制并发和访问频率，遵守目标网站条款。
- CI 环境建议使用 `--headless --skip-env-check`，并在 CI 镜像中预装浏览器。
- Linux headed 模式需要图形环境；服务器环境优先使用 headless。

更多代码模式见 `references/browser_automation.md`。
