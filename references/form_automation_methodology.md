# 表单自动化实战方法论

基于 LayUI / 传统后台管理系统的表单自动化经验总结。适用于任何需要操作复杂表单（下拉联动、动态字段、弹窗确认）的场景。

## 核心原则

**先探测，再编码。** 不要假设页面结构，每一步都应先获取真实 DOM 再决定操作方式。

## 第一步：页面元素全量探测

创建环境后，第一件事是获取目标页面的所有可交互元素。这是后续所有操作的基础。

### 探测脚本模板

```python
async def probe_page_elements(page):
    """获取页面所有可交互元素的完整信息"""
    info = await page.evaluate("""
    (function() {
        var result = {inputs: [], selects: [], radios: [], checkboxes: [], buttons: [], textareas: []};

        // 所有 input
        document.querySelectorAll('input').forEach(function(el) {
            result.inputs.push({
                id: el.id, name: el.name, type: el.type,
                placeholder: el.placeholder, maxLength: el.maxLength > 0 ? el.maxLength : null,
                required: el.required, visible: el.offsetParent !== null,
                value: el.value, className: el.className.substring(0, 80)
            });
        });

        // 所有 select
        document.querySelectorAll('select').forEach(function(el) {
            result.selects.push({
                id: el.id, name: el.name,
                layFilter: el.getAttribute('lay-filter'),
                laySearch: el.hasAttribute('lay-search'),
                options: Array.from(el.options).map(function(o) {
                    return {value: o.value, text: o.text};
                }),
                visible: el.offsetParent !== null
            });
        });

        // 所有 radio
        document.querySelectorAll('input[type="radio"]').forEach(function(el) {
            var label = el.parentElement ? el.parentElement.textContent.trim().substring(0, 50) : '';
            result.radios.push({
                id: el.id, name: el.name, value: el.value,
                checked: el.checked, label: label, visible: el.offsetParent !== null
            });
        });

        // 所有 checkbox
        document.querySelectorAll('input[type="checkbox"]').forEach(function(el) {
            var label = el.parentElement ? el.parentElement.textContent.trim().substring(0, 50) : '';
            result.checkboxes.push({
                id: el.id, name: el.name, value: el.value,
                checked: el.checked, label: label, visible: el.offsetParent !== null
            });
        });

        // 所有 button
        document.querySelectorAll('button, input[type="submit"], a[class*="btn"]').forEach(function(el) {
            result.buttons.push({
                id: el.id, type: el.type || el.tagName,
                text: el.textContent.trim().substring(0, 30),
                layFilter: el.getAttribute('lay-filter'),
                visible: el.offsetParent !== null
            });
        });

        // 所有 textarea
        document.querySelectorAll('textarea').forEach(function(el) {
            result.textareas.push({
                id: el.id, name: el.name,
                placeholder: el.placeholder,
                visible: el.offsetParent !== null
            });
        });

        return result;
    })()
    """)
    return info
```

### 探测要点

1. **区分原生元素和 UI 框架渲染元素**：LayUI、Element UI、Ant Design 等框架会隐藏原生 select/checkbox，用自定义 DOM 替代
2. **记录 `lay-filter`、`lay-verify` 等框架属性**：这些决定了联动逻辑和校验规则
3. **检查元素可见性**：`offsetParent !== null` 判断元素是否在可视区域
4. **获取所有 option 值**：下拉框的可选项决定了测试数据范围

## 第二步：识别表单提交流程

### 提交按钮定位

```python
# 通过 lay-filter 定位提交按钮
submit_btn = page.locator('button[lay-filter="formName-Submit"]')
```

### 提交后的响应模式

常见的提交响应有三种，必须逐一探测：

| 模式 | 特征 | 处理方式 |
|------|------|----------|
| 直接提交 | 点击后直接发 API 请求 | 等待响应即可 |
| 确认弹窗 | 点击后弹出 layer.confirm | 需要再点击确认按钮 |
| 前端校验拦截 | 点击后不发请求，显示错误提示 | 检查 toast/标红字段 |

### 探测提交流程

```python
# 监听网络请求
requests = []
page.on('request', lambda req: requests.append(req.url) if '/api/' in req.url else None)

# 点击提交
await submit_btn.click()
await asyncio.sleep(2)

# 检查是否有确认弹窗
confirm = page.locator('.layui-layer-dialog')
if await confirm.count() > 0:
    print("有确认弹窗，需要二次确认")
    # LayUI confirm 的按钮顺序由 btn 数组决定
    # btn: ['取消', '确认'] → btn0=取消, btn1=确认
    await confirm.locator('.layui-layer-btn1').click()
```

## 第三步：识别联动逻辑

### 什么是联动

选择某个字段后，页面动态显示/隐藏其他字段区域。常见于：
- 选择"类型"后显示该类型的专用参数
- 选择"管制措施"后显示对应的配置项
- 选择"地区"后加载对应的城市列表

### 探测联动

```python
# 选择一个类型
await click_layui_select(page, "category", "9")
await asyncio.sleep(2)

# 检查哪些元素变为可见
visible_after = await page.evaluate("""
(function() {
    var visible = [];
    document.querySelectorAll('input, select, textarea').forEach(function(el) {
        if (el.offsetParent !== null && el.id) {
            visible.push({id: el.id, type: el.type, name: el.name});
        }
    });
    return visible;
})()
""")
```

### 联动字段是必填的

**关键教训**：联动显示的字段通常是必填的。如果不填写这些字段，提交会被前端或后端校验拦截。

## 第四步：操作 UI 框架组件

### LayUI Select（下拉框）

LayUI 会隐藏原生 `<select>`，渲染一个 `.layui-form-select` 容器。操作方式：

```python
async def click_layui_select(page, select_id, value):
    """点击 LayUI 下拉框选项"""
    select_wrapper = page.locator(f"#{select_id} + .layui-form-select")
    title_input = select_wrapper.locator(".layui-select-title input")
    await title_input.click(timeout=10000)
    await asyncio.sleep(0.5)
    dd_item = select_wrapper.locator(f'dd[lay-value="{value}"]')
    await dd_item.click(timeout=10000)
    await asyncio.sleep(0.5)
```

**为什么不能用 JS 直接设值**：LayUI select 的 `change` 事件绑定在渲染后的 DOM 上，直接修改原生 select 的 value 不会触发联动回调。必须模拟点击 `dd` 元素。

### LayUI Radio（单选按钮）

LayUI radio 使用 `lay-ignore` 属性保留原生样式，或用自定义容器包裹。操作方式：

```python
# 如果有 lay-ignore，可以直接点击原生 radio
await page.locator('#chk_warning').click(force=True)

# 如果是 LayUI 渲染的，需要点击外层容器
await page.locator('#hdr_warning').click()

# 或者调用页面已有的 JS 函数
await page.evaluate('selectMeasure("warning")')
```

### LayUI Input（输入框）

```python
# 方式1：Playwright fill（推荐，会触发 input/change 事件）
await page.locator(f'#{input_id}').fill(value, force=True, timeout=10000)

# 方式2：JS 设值（当元素被遮挡无法 fill 时使用）
await page.evaluate(f"""
(function() {{
    var inp = document.getElementById('{input_id}');
    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, '{value}');
    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
    inp.dispatchEvent(new Event('change', {{bubbles: true}}));
}})()
""")
```

### LayUI Layer 弹窗

```python
# 关闭所有弹窗
await page.evaluate("""
(function() {
    if (typeof layui !== 'undefined' && layui.layer) layui.layer.closeAll();
    document.querySelectorAll('.layui-layer-shade').forEach(function(el) { el.remove(); });
    document.querySelectorAll('.layui-layer').forEach(function(el) { el.remove(); });
})()
""")
```

## 第五步：验证提交结果

### 成功判定

```python
# 方式1：表单弹窗关闭 = 提交成功
form_open = await page.evaluate("""
(function() {
    var layers = document.querySelectorAll('.layui-layer-page');
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].style.display !== 'none') return true;
    }
    return false;
})()
""")
if not form_open:
    print("提交成功")

# 方式2：检测成功 toast
# admin.toast({txt: '新增成功', type: 'success'}) 会短暂显示
```

### 失败判定

```python
# 方式1：检查标红字段
danger_fields = await page.evaluate("""
(function() {
    return Array.from(document.querySelectorAll('.layui-form-danger')).map(function(d) {
        return {id: d.id, name: d.name};
    });
})()
""")

# 方式2：检查 toast 错误提示
# admin.toast({txt: '请选择受理机构', type: 'error'})

# 方式3：表单仍打开 = 提交被阻止
```

## 第六步：测试用例设计

### 命名规范

规则名称加入 **场景描述 + 时间戳**，避免重名冲突：

```python
from datetime import datetime
ts = datetime.now().strftime("%m%d%H%M%S")
name = f"信用卡套现正常提交_{ts}"
```

### 用例隔离

每个用例前关闭所有弹窗并重新打开新增表单：

```python
for tc_id, tc_func in ALL_TEST_CASES:
    await close_all_layers(page)
    await click_add_button(page)
    result = await tc_func(page)
```

### 校验类用例不需要填全部字段

验证"缺少某字段时的校验提示"时，只需填写除目标字段外的其他字段，然后直接提交。

## 常见坑与解决方案

| 问题 | 原因 | 解决 |
|------|------|------|
| `Locator.click` 超时 | 元素被遮罩层覆盖 | 用 `force=True` 或 JS `el.click()` |
| `fill()` 超时 | 元素不可见或被覆盖 | 用 `force=True` 参数 |
| `return not in function` | `page.evaluate` 中多语句有裸 return | 用 IIFE 包裹：`(function(){...})()` |
| 联动字段不显示 | 用 JS 设值没触发事件 | 必须模拟点击 dd 元素 |
| 提交后无反应 | 有确认弹窗未处理 | 检测 `.layui-layer-dialog` 并点击确认 |
| 提交失败但无错误 | 联动的必填字段未填写 | 先探测联动字段，全部填写 |
| 多个 layer-page 冲突 | 系统有其他弹窗（如修改密码） | 用更精确的选择器如 `.popup-bottom-page` |
| 规则名称重复 | 多次运行同名数据 | 名称加时间戳 |
| 浏览器被关闭 | 提交成功后页面跳转或 layer 全部关闭 | 每个用例前重新检查页面状态 |

## evaluate 中 JS 代码规范

Playwright 的 `page.evaluate()` 对 JS 有特殊要求：

```python
# ❌ 错误：多语句中使用裸 return
await page.evaluate("""
var x = document.getElementById('foo');
return x.value;
""")

# ✅ 正确：用 IIFE 包裹
await page.evaluate("""
(function() {
    var x = document.getElementById('foo');
    return x.value;
})()
""")

# ✅ 正确：单表达式不需要 return
await page.evaluate("document.getElementById('foo').value")
```

## 完整测试流程模板

```python
async def run_all_tests(page):
    await login(page)
    await navigate_to_target_page(page)
    await close_all_layers(page)

    results = []
    for tc_id, tc_func in ALL_TEST_CASES:
        # 每个用例前重置表单
        await close_all_layers(page)
        await open_form(page)
        try:
            result = await tc_func(page)
            results.append((tc_id, "PASS" if result else "FAIL"))
        except Exception as e:
            results.append((tc_id, f"ERROR: {e}"))

    # 汇总
    for tc_id, status in results:
        print(f"  {tc_id}: {status}")
```
