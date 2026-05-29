# 浏览器自动化代码模式

本文档提供通用 Python + Playwright 自动化写法。默认从简单脚本开始，只有在任务复杂时才引入 Page Object。

默认安装流程是在本次任务或项目工作目录中先创建名为 `.venv` 的独立 Python 虚拟环境，再在该环境中安装依赖和 Playwright 浏览器。不要把虚拟环境创建到 skill 目录，也不要把 `.venv` 作为 skill 内容交付。后续运行脚本、保存截图、下载文件和登录态都应在任务目录中完成。

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

如果复用 `setup.py`，必须显式传入任务环境路径，例如 `python setup.py --browser chromium --venv /path/to/browser-task/.venv`。任务环境损坏时可加 `--recreate-venv` 重建；Linux 环境缺系统依赖时，加 `--with-deps` 安装 Playwright 浏览器依赖。

本文档使用 UTF-8 编码。Windows PowerShell 查看中文文档时，建议使用：

```powershell
Get-Content -Raw -Encoding UTF8 .\references\browser_automation.md
```

下面的示例默认替换任务目录中 `template.py` 里的 `run_task(page, manager)` 函数；如果单独新建脚本，需要同时把本 skill 的 `scripts/framework/` 目录复制到脚本同级。运行时使用任务目录的 `.venv`。

## 最小脚本

```python
from framework.base_page import BrowserPage


async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com")
    title = await browser.get_title()
    print(title)
    await browser.screenshot("example.png")
```

## 表单填写

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com/login")
    await browser.fill_text("#username", "demo")
    await browser.fill_text("#password", "secret")
    await browser.click("button[type=submit]")
    await browser.expect_url("**/dashboard")
```

## 批量截图

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    urls = [
        "https://example.com",
        "https://example.com/about",
    ]

    for index, url in enumerate(urls, start=1):
        await browser.navigate(url)
        await browser.wait_for_page_loaded()
        await browser.screenshot(f"page_{index}.png")
```

## 抓取列表数据

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com/products")

    items = browser.locator(".product-card")
    rows = []
    for i in range(await items.count()):
        item = items.nth(i)
        rows.append({
            "title": await item.locator(".title").inner_text(),
            "price": await item.locator(".price").inner_text(),
        })

    print(rows)
```

## 保存登录态

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com/login")
    await browser.fill_text("#username", "demo")
    await browser.fill_text("#password", "secret")
    await browser.click("button[type=submit]")
    await browser.expect_url("**/dashboard")
    await manager.save_storage_state("auth.json")
```

## 加载登录态

优先通过命令行参数加载：

```bash
.venv/bin/python template.py --storage-state auth.json
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe template.py --storage-state auth.json
```

也可以在入口脚本里配置，位置需要在创建 `BrowserManager(config)` 之前：

```python
config.storage_state_path = "auth.json"
```

然后正常创建 context 和 page。

## 使用基础 URL

设置 `BROWSER_BASE_URL=https://example.com` 后，可以用以 `/` 开头的相对路径导航：

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("/dashboard")
```

## 请求拦截

阻止图片以提升速度：

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)

    async def block_images(route):
        await route.abort()

    await browser.intercept_request("**/*.{png,jpg,jpeg,gif,webp}", block_images)
    await browser.navigate("https://example.com")
```

## 等待接口响应

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com")
    response = await browser.wait_for_response(
        "**/api/products",
        action=lambda: browser.click("#load-products"),
    )
    print(await response.json())
```

## 下载文件

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com/reports")
    path = await browser.download_by_click("a.download-report")
    print(path)
```

## Page Object 写法

当一个任务需要多个页面、多个场景或长期维护时，再把页面行为封装成类。

```python
from framework.base_page import BrowserPage


class SearchPage(BrowserPage):
    async def open(self):
        await self.navigate("https://example.com/search")

    async def search(self, keyword: str):
        await self.fill_text("[name=q]", keyword)
        await self.click("button[type=submit]")
        await self.wait_for_page_loaded()

    async def result_titles(self) -> list[str]:
        return await self.get_all_texts(".result-title")
```

调用：

```python
async def run_task(page, manager):
    search = SearchPage(page, manager.config)
    await search.open()
    await search.search("playwright")
    print(await search.result_titles())
```

## 处理弹窗 (alert/confirm/prompt)

两种模式：

**模式 1：asyncio.gather（推荐，无竞态）**

```python
import asyncio

async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com")

    # 同时等待 dialog 和触发 dialog 的点击
    text, _ = await asyncio.gather(
        browser.accept_alert(timeout=5000),
        browser.click("#delete-btn"),
    )
    print(f"Dialog said: {text}")
```

**模式 2：expect_alert（先注册再触发）**

```python
async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    await browser.navigate("https://example.com")

    # 先注册处理器，再执行触发动作
    browser.expect_alert("accept")
    await browser.click("#delete-btn")
```

**处理 prompt 弹窗：**

```python
import asyncio

async def run_task(page, manager):
    browser = BrowserPage(page, manager.config)
    msg, _ = await asyncio.gather(
        browser.prompt_alert("my input", timeout=5000),
        browser.click("#prompt-btn"),
    )
```

## 稳定性建议

- 优先使用语义选择器：role、label、test id。
- 点击后等待页面变化时，优先等待确定信号：`wait_for_url("**/target")`、`wait_for_response(...)` 或元素断言。`wait_for_navigation()` 也必须传 `url` 目标，避免依赖传统 navigation 事件。
- 不要默认等待 `networkidle`，很多现代网页会持续发送请求。
- 对必须出现的元素使用显式断言或 `wait_for_selector()`。
- 脚本失败时会打印异常类型、当前 URL、核心配置和截图目录；设置 `BROWSER_DEBUG=1` 可额外打印 traceback。
- 把账号、密码、目标 URL 放在环境变量或配置文件中，不要写死在代码里。
- 大批量任务应限制访问频率，并记录失败项方便重试。
