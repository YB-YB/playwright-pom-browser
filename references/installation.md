# 环境安装与配置

本文档提供 Playwright 浏览器自动化环境的完整安装说明。日常使用只需参考 SKILL.md 中的"快速开始"；遇到安装问题或 CI 配置时再查阅本文档。

## 基本原则

- **不要在本 skill 目录中创建虚拟环境**，应在独立的任务工作目录中操作
- **不要把 `.venv` 当作 skill 内容交付**，虚拟环境属于任务环境
- 后续运行脚本、保存截图、下载文件和登录态都应在任务目录中完成

## 完整安装步骤

### Linux / macOS

```bash
# 1. 创建任务目录
mkdir -p /path/to/browser-task && cd /path/to/browser-task

# 2. 创建虚拟环境
python -m venv .venv

# 3. 安装 Python 依赖
.venv/bin/python -m pip install -r /path/to/playwright-pom-browser/scripts/requirements.txt

# 4. 安装 Chromium 浏览器
.venv/bin/python -m playwright install chromium

# 5. （可选）Linux 环境缺少系统依赖时
.venv/bin/python -m playwright install-deps chromium
```

### Windows PowerShell

```powershell
# 1. 创建任务目录
New-Item -ItemType Directory -Force C:\path\to\browser-task
Set-Location C:\path\to\browser-task

# 2. 创建虚拟环境
python -m venv .venv

# 3. 安装 Python 依赖
.\.venv\Scripts\python.exe -m pip install -r C:\path\to\playwright-pom-browser\scripts\requirements.txt

# 4. 安装 Chromium 浏览器
.\.venv\Scripts\python.exe -m playwright install chromium
```

## setup.py 一键安装

使用本 skill 内置的安装辅助脚本（必须显式把 `--venv` 指向任务目录的 `.venv`）：

```bash
cd /path/to/playwright-pom-browser/scripts

# 安装指定浏览器
python setup.py --browser chromium --venv /path/to/browser-task/.venv

# 安装全部浏览器
python setup.py --all --venv /path/to/browser-task/.venv

# 仅检查环境（不安装）
python setup.py --check --venv /path/to/browser-task/.venv

# 重建损坏的虚拟环境
python setup.py --browser chromium --venv /path/to/browser-task/.venv --recreate-venv

# Linux 环境安装系统依赖
python setup.py --browser chromium --with-deps --venv /path/to/browser-task/.venv
```

Windows PowerShell 示例：

```powershell
Set-Location C:\path\to\playwright-pom-browser\scripts
python setup.py --browser chromium --venv C:\path\to\browser-task\.venv
```

## 验证安装

```bash
# Linux / macOS
/path/to/browser-task/.venv/bin/python /path/to/playwright-pom-browser/scripts/run_test.py --headless

# Windows PowerShell
C:\path\to\browser-task\.venv\Scripts\python.exe C:\path\to\playwright-pom-browser\scripts\run_test.py --headless
```

示例默认打开内置页面，读取标题并保存截图。需要访问真实站点时可传 `--url https://example.com`。

## 创建自己的脚本

**重要**：`template.py` 依赖 `framework/` 目录，复制时必须一起拷贝。

**方案 A：连 framework 一起复制（推荐）**

```bash
# Linux / macOS
cp -r /path/to/playwright-pom-browser/scripts/template.py /path/to/playwright-pom-browser/scripts/framework/ /path/to/browser-task/

# Windows PowerShell
Copy-Item C:\path\to\playwright-pom-browser\scripts\template.py, C:\path\to\playwright-pom-browser\scripts\framework -Destination C:\path\to\browser-task -Recurse
```

**方案 B：直接在本 skill 的 scripts 目录里创建脚本**

```bash
cd /path/to/playwright-pom-browser/scripts
cp template.py browser_task.py
```

复制后的任务目录结构：

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
    runner.py
    utils/
```

运行：

```bash
# Linux / macOS
.venv/bin/python browser_task.py --headless

# Windows PowerShell
.\.venv\Scripts\python.exe browser_task.py --headless
```

## 完整命令行参数

`run_test.py` 和 `template.py` 支持以下参数：

| 参数 | 说明 |
| --- | --- |
| `--headless` | 无头模式运行（默认） |
| `--headed` | 有头模式运行 |
| `--interactive` | 未指定 headed/headless 时交互式询问 |
| `--browser chromium` | 指定浏览器，支持 `chromium` / `firefox` / `webkit` |
| `--timeout 30000` | 全局超时，单位毫秒 |
| `--navigation-timeout 60000` | 导航超时，单位毫秒 |
| `--base-url https://example.com` | 设置基础 URL，可在脚本里导航到 `/path` |
| `--screenshot-dir screenshots` | 设置截图保存目录 |
| `--storage-state auth.json` | 加载已保存的 Playwright 登录态 |
| `--viewport 1280x800` | 设置浏览器视口尺寸 |
| `--browser-probe-timeout 120` | 浏览器可用性检查的启动超时，单位秒 |
| `--skip-env-check` | 跳过环境检查 |
| `--install-missing` | 环境缺失时自动安装 Python 依赖和 Playwright 浏览器 |

默认行为：headless 模式、检查环境但不静默下载依赖。脚本失败时会打印异常类型、当前 URL、核心配置和截图目录；设置 `BROWSER_DEBUG=1` 可额外打印 traceback。

## 完整环境变量

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
| `BROWSER_DOWNLOAD_DIR` | 下载目录 | `downloads` |
| `BROWSER_LOCALE` | 浏览器上下文 locale | `zh-CN` |
| `BROWSER_USER_AGENT` | 自定义 User-Agent | `Mozilla/5.0 ...` |
| `BROWSER_STORAGE_STATE` | 登录态文件路径 | `auth.json` |
| `BROWSER_ACCEPT_DOWNLOADS` | 是否接受下载 | `true` / `false` |
| `BROWSER_PROBE_TIMEOUT` | 浏览器可用性检查超时，单位秒 | `120` |
| `BROWSER_SKIP_ENV_CHECK` | 跳过环境检查 | `1` |
| `BROWSER_DEBUG` | 失败时额外打印 traceback | `1` |

## CI 环境配置

```bash
# 预装步骤（写入 CI 镜像）
python -m pip install -r scripts/requirements.txt
python -m playwright install chromium --with-deps

# 运行时
python template.py --headless --skip-env-check
```

## 查看中文文档

Windows PowerShell 查看中文文档时，建议显式指定编码：

```powershell
Get-Content -Raw -Encoding UTF8 .\SKILL.md
```
