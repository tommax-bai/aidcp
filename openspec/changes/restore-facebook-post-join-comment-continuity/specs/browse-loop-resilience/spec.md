## ADDED Requirements

### Requirement: Facebook 滚动回执报告「无目标」时必须有处置分支，不得让会话无命令悬停

当 Facebook 浏览闭环收到滚动动作失败且原因表示「本次没有可用目标」的回执时，决策端 SHALL 走到一个明确分支：或下发下一条推进命令，或把会话推到终态。MUST NOT 出现「候选分支逐条不命中、通用兜底又把滚动动作排除在外」导致既不发命令也不判终态的悬停。

会话在收到该回执后，SHALL 要么存在下一条待执行命令，要么已进入终态。「等空闲看门狗超时」「等冷待机重启」MUST NOT 被当作该分支的实现。

本要求收窄到 Facebook：证据全部取自 Facebook 会话，其他平台的滚动语义不在本次范围内、行为不变。

#### Scenario: 首页无内容且滚动报无目标
- **WHEN** Facebook 滚动回执为失败、原因为无可用目标
- **THEN** 决策端在同一轮内给出下一步动作或终止会话
- **AND** 不出现无命令、无终态的静默悬停

#### Scenario: 悬停必须可观测
- **WHEN** 决策端确实无法给出下一步
- **THEN** 它诚实终止会话并写明原因
- **AND** 不依赖冷待机重启来掩盖这次悬停

#### Scenario: 既有滚动成功路径不变
- **WHEN** 滚动回执带回新卡
- **THEN** 浏览闭环按既有路径继续
- **AND** 本要求不改变成功路径的行为

### Requirement: 越南语 Feed 恢复控件必须由 Native 通过 CDP 可信点击

当无可用卡片的 Facebook 页面出现唯一、可见且规范化文案精确等于 `Đi đến Bảng feed` 的恢复控件时，Edge SHALL 把它识别为 Feed 恢复目标。页面脚本只可返回当前视口内的唯一坐标，MUST NOT 调用 DOM `click()` 或把“发现控件”当作已恢复。

Native SHALL 在点击前前台化并重新定位同一语义目标，随后只发送一组 CDP `mouseMoved → mousePressed → mouseReleased`。只有该控件消失且页面被重新判定为 home surface，浏览流程才可继续；控件歧义、离开视口、点击前消失或点击后缺少该后置状态时，Edge SHALL 如实返回未开始或结果不明。

#### Scenario: 唯一越南语恢复控件被可信点击
- **WHEN** 空卡片页面存在唯一可见的 `Đi đến Bảng feed` 控件
- **THEN** JavaScript 只返回坐标，Native 重新定位后发送一组 CDP 指针事件
- **AND** 控件消失且 home surface 被确认后才继续既有 Feed 浏览

#### Scenario: DOM click 不得冒充恢复
- **WHEN** 页面脚本识别到该控件
- **THEN** 页面脚本不调用 `HTMLElement.click()`
- **AND** 单纯取得坐标或完成 CDP 发包都不被记录为恢复成功

#### Scenario: 不唯一或后置状态缺失时失败关闭
- **WHEN** 同文案目标不唯一、目标在视口外、点击前已移动消失，或点击后未确认 home surface
- **THEN** Edge 不重复点击、不改点其他控件
- **AND** 按是否已经发出 CDP 点击分别报告未开始或结果不明
