## MODIFIED Requirements

### Requirement: 越南语 Feed 恢复控件必须由 Native 通过 CDP 可信点击

当无可用卡片的 Facebook 页面出现唯一、可见且规范化文案精确等于 `Đi đến Bảng feed` 的恢复控件时，Edge SHALL 把它识别为 Feed 恢复目标。页面脚本只可返回当前视口内的唯一坐标，MUST NOT 调用 DOM `click()` 或把“发现控件”当作已恢复。

Native MUST NOT merely because this recovery control exists activate the browser. It SHALL immediately re-locate the same semantic target before sending exactly one CDP `mouseMoved → mousePressed → mouseReleased` sequence. If the containing `page.scroll` is the watchdog-authorized `idle_recover_nudge`, the common scroll entry MAY already have activated the exact target once; the recovery-control path MUST NOT activate it a second time. Only when the control disappears and the page is reclassified as the home surface may browsing continue. Ambiguous, offscreen, stale, or postcondition-missing controls SHALL return an honest not-started or indeterminate result.

#### Scenario: 唯一越南语恢复控件被可信点击

- **WHEN** 空卡片页面存在唯一可见的 `Đi đến Bảng feed` 控件
- **THEN** JavaScript 只返回坐标，Native 重新定位后发送一组 CDP 指针事件
- **AND** 控件消失且 home surface 被确认后才继续既有 Feed 浏览

#### Scenario: 恢复控件不独立触发前台化

- **WHEN** 非看门狗 `page.scroll` 命中唯一可见的恢复控件
- **THEN** Native 重新定位并执行既有可信点击，但不调用 `Page.bringToFront`

#### Scenario: 看门狗恢复命令最多前台化一次

- **WHEN** `idle_recover_nudge` 已在公共滚动入口激活精确 target，随后命中 Feed 恢复控件
- **THEN** 恢复控件路径不再次激活 target
- **AND** it still re-locates the control before pointer input

#### Scenario: DOM click 不得冒充恢复

- **WHEN** 页面脚本识别到该控件
- **THEN** 页面脚本不调用 `HTMLElement.click()`
- **AND** 单纯取得坐标或完成 CDP 发包都不被记录为恢复成功

#### Scenario: 不唯一或后置状态缺失时失败关闭

- **WHEN** 同文案目标不唯一、目标在视口外、点击前已移动消失，或点击后未确认 home surface
- **THEN** Edge 不重复点击、不改点其他控件
- **AND** 按是否已经发出 CDP 点击分别报告未开始或结果不明
