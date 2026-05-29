---
name: playwright-pom-browser
description: Use when the user needs Python + Playwright browser automation for scripted web actions, scraping JavaScript-rendered pages, form filling, screenshots, login state reuse, file upload/download, network interception, or end-to-end validation. Supports one-off scripts and maintainable Page Object structures.
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

## 输入 (Input)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `task_goal` | string | 是 | 无 | 用户要完成的浏览器自动化目标，例如登录、填表、截图、抓取或端到端验证 |
| `target_url` | string | 条件必填 | 无 | 目标页面 URL；如果任务只要求生成通用模板，可不提供 |
| `auth_method` | string | 否 | `none` | 登录方式：`none`、`credentials`、`storage_state`、`manual_login` |
| `storage_state_path` | string | 否 | 无 | Playwright 登录态 JSON 路径，仅在 `auth_method=storage_state` 时使用 |
| `output_type` | string | 否 | `script` | 输出形式：`script`、`page_object`、`test_case`、`data_file`、`screenshot` |
| `browser` | string | 否 | `chromium` | 浏览器类型：`chromium`、`firefox`、`webkit` |
| `headless` | boolean | 否 | `true` | 是否使用无头模式运行 |
| `task_dir` | string | 否 | 当前任务目录 | 保存脚本、截图、下载文件和登录态的独立任务目录 |

输入校验规则：

- `task_goal` 缺失时停止执行，并要求用户补充自动化目标。
- 需要访问具体页面但 `target_url` 缺失时停止执行，并列出缺失字段。
- `auth_method=storage_state` 但 `storage_state_path` 缺失时停止执行，并说明需要登录态文件路径。
- `output_type` 或 `browser` 不在允许值内时，改用默认值并在结果中说明修正。
- `task_dir` 不得位于本 skill 目录内，虚拟环境、截图、下载文件和登录态必须保存在独立任务目录。

## 输出 (Output)

| 输出物 | 触发条件 | 格式与验收标准 |
|--------|----------|----------------|
| 自动化脚本 | `output_type=script` 或一次性任务 | 可运行的 Python 脚本，包含 `run_task(page, manager)`，无硬编码敏感信息 |
| Page Object | `output_type=page_object` 或多页面长期维护任务 | 页面类继承 `BrowserPage`，公共方法命名清晰，选择器集中封装 |
| 测试用例 | `output_type=test_case` 或端到端验证任务 | 包含前置条件、执行步骤、断言和失败截图 |
| 数据文件 | 抓取或批量采集任务 | CSV、JSON 或用户指定格式，字段含义明确 |
| 运行报告 | 所有执行型任务 | 包含运行命令、浏览器类型、目标 URL、结果摘要、截图或下载文件路径 |
| 失败诊断 | 执行失败时 | 包含异常类型、当前 URL、失败步骤、已尝试修复动作和下一步建议 |

## 执行流程

收到浏览器自动化任务时，按以下步骤推进：

1. **确认任务类型** — 判断是一次性脚本、稳定项目还是表单自动化；输出任务类型、目标 URL 和交付形式
2. **校验输入参数** — 按 Input 表检查必填字段、登录方式、浏览器类型和任务目录；输出缺失项或规范化后的参数
3. **检查运行环境** — 确认 Python 3.10+ 和 Playwright 可用；输出环境检查结果和必要安装命令
4. **编写脚本** — 基于 `references/browser_automation.md` 中的模式编写脚本，优先使用语义选择器；输出脚本或 Page Object 文件
5. **运行验证** — 执行脚本并检查页面状态、数据、截图或断言结果；输出运行报告和失败诊断
6. **修正并复验** — 若脚本失败，基于失败诊断最多修正 3 次并重新运行；输出最终结果和剩余风险

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

## 失败处理策略

| 失败场景 | 处理步骤 | 输出要求 |
|----------|----------|----------|
| 必填输入缺失 | 停止执行，列出缺失字段和示例值，不生成猜测脚本 | 缺失字段清单、建议补充格式 |
| 外部依赖不可用 | 先检查 Python、Playwright 包和浏览器安装状态；允许按 `references/installation.md` 修复后重试一次 | 环境检查结果、安装命令、重试结果 |
| 脚本运行失败 | 保留异常类型、当前 URL、截图目录和失败步骤；修正后最多重新运行 3 次 | 失败诊断、修正摘要、最终验证结果 |
| 输出格式不符 | 对照 Output 表检查脚本、报告或数据文件；格式不符时自动修正并重新校验 | 修正前问题、修正后产物 |
| 决策不确定 | 暂停并给出 2-3 个可选方案，说明推荐方案和风险 | 选项列表、推荐理由 |
| 权限不足 | 停止涉及写入、下载或访问受限资源的动作，说明所需权限或合法凭证 | 权限缺口、可恢复步骤 |
| 选择器不稳定 | 优先改用 test id、role、label、placeholder，再降级到稳定 CSS，XPath 仅兜底 | 已尝试选择器、最终选择器依据 |

## 验收标准

交付前必须完成以下检查：

- 输入参数已按 Input 表校验，缺失项和默认值处理已说明。
- 脚本不包含硬编码账号、密码、Token、密钥或绕过访问限制的逻辑。
- 至少运行一次脚本或冒烟测试；无法访问真实站点时，说明阻断原因并运行本地环境检查。
- 运行报告包含命令、浏览器类型、目标 URL、结果摘要和截图、下载或数据文件路径。
- 修改后的 Skill 文档保持在 500 行以内，详细模式继续放在 `references/` 目录中。

## 示例

### 示例 1：黄金路径，生成一次性截图脚本

**输入**：

- `task_goal`: 打开首页并保存截图
- `target_url`: `https://example.com`
- `output_type`: `script`
- `browser`: `chromium`

**AI 行为**：

1. 校验目标 URL 和输出类型。
2. 复制 `scripts/template.py` 与 `scripts/framework/` 到任务目录。
3. 在 `run_task(page, manager)` 中实现导航、等待 `domcontentloaded`、截图。
4. 运行脚本并返回截图路径。

**输出**：

- 可运行脚本：`template.py`
- 运行命令：`.venv/bin/python template.py --headless --browser chromium`
- 运行报告：页面标题、截图路径、执行结果

### 示例 2：边界场景，复用登录态访问后台页面

**输入**：

- `task_goal`: 复用登录态进入后台并采集表格数据
- `target_url`: `https://example.com/admin`
- `auth_method`: `storage_state`
- `storage_state_path`: `auth.json`
- `output_type`: `data_file`

**AI 行为**：

1. 校验 `auth.json` 路径存在且不位于公开输出目录。
2. 使用 `--storage-state auth.json` 创建浏览器上下文。
3. 进入后台页面后等待表格可见，采集表头和行数据。
4. 输出 JSON 或 CSV，并在报告中记录采集行数。

**输出**：

- 数据文件：`admin_table.json` 或用户指定格式
- 运行报告：采集字段、行数、登录态使用方式

### 示例 3：失败场景，目标页面要求验证码

**输入**：

- `task_goal`: 自动登录并提交表单
- `target_url`: `https://example.com/login`
- `auth_method`: `credentials`

**AI 行为**：

1. 打开登录页并检测到验证码或风控提示。
2. 停止自动化登录，不尝试绕过验证码或风控。
3. 请求用户提供合法登录态，或改为手动登录后保存 `storage_state`。

**输出**：

- 失败诊断：检测到验证码或风控
- 可恢复方案：手动登录后保存登录态，再使用 `--storage-state auth.json` 继续

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
