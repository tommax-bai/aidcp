## ADDED Requirements

### Requirement: 正文填写的单步预算随长度伸缩，且边缘必先于云端答复

逐字符输入是 O(正文长度) 的操作，MUST NOT 由云端用与长度无关的常数窗口去等它——否则云端先判失败、边缘仍在往活着的编辑器里写字，形成「记录已 failed、页面上却躺着半篇正文」的错位，并让恢复后的浏览循环与被放弃的打字循环共用同一个 CDP session。

cloud SHALL 按正文长度算出 Facebook `fill_field` 的执行预算，随指令下发（复用既有的 `PublishCommandPayload.timeoutMs`）。云端等待窗口 SHALL 为「下发预算 + 兜底余量」，使边缘**必定先答**；该 timer 的语义 SHALL 退化为「边缘真的失联」的兜底，MUST NOT 作为正常路径的收敛手段。指令**不带**预算时（小红书全路径）等待窗口 MUST 逐字节沿用既有常数窗口。

预算上限 MUST 严格小于边缘发布租约 TTL（安全比例 0.4），否则边缘会在打字途中单方面过期租约、恢复浏览循环去驱动半写的编辑器。

edge SHALL 按下发预算自我掐表：预算耗尽即停止输入、清空编辑器、诚实回报，MUST NOT 继续写入已被上游放弃的编辑器；清场失败 MUST 如实上报，MUST NOT 谎报干净页。云端未下发预算时，edge SHALL 使用**小于**云端常数窗口的兜底预算，使旧云端配新边缘时仍是边缘先答。

逐字符的拟人化键盘节奏 MUST NOT 因本要求而改变。

#### Scenario: 长正文在下发预算内打完
- **WHEN** 云端为一篇 300 字正文下发按长度算出的 `fill_field` 预算
- **THEN** edge SHALL 在预算内逐字输完全文并通过全文校验
- **AND** cloud MUST NOT 在边缘答复之前判超时

#### Scenario: 预算耗尽即停手清场
- **WHEN** 正文在下发预算内打不完
- **THEN** edge SHALL 停止输入、清空编辑器、回报 `fill_deadline_exceeded`（清不干净则标为 dirty）
- **AND** MUST NOT 提交，MUST NOT 让输入循环继续写入编辑器

#### Scenario: 正文超出可打完的上限
- **WHEN** 正文长度超出预算上限所能容纳的字符数
- **THEN** cloud SHALL 诚实 `failed`（`content_too_long`）
- **AND** MUST NOT 截断正文，MUST NOT 下发任何指令

#### Scenario: 小红书路径不受影响
- **WHEN** 发布平台为小红书
- **THEN** 指令 MUST NOT 携带执行预算，云端等待窗口 MUST 与既有常数窗口逐字节一致

### Requirement: 正文校验必须回读全文

「插入调用没报错」不等于「文本进去了」。正文校验 MUST 回读编辑器**全文**并确认其完整包含终稿正文；MUST NOT 以正文前缀片段作为接受判据——前缀探针会把「编辑器吞掉正文主体」判成成功，从而真的发出一篇被截断的帖子。

编辑器内出现超出终稿正文的额外内容（如打字途中被 typeahead 劫持插入）MUST 视为失败，MUST NOT 提交。

打字前 edge MUST 先清空编辑器并校验其为空：composer 会复用已存在的编辑区、而输入是在光标处**追加**，不清空即会把上一次失败留下的残稿与本篇拼接后发出。

聚焦 SHALL 视为尽力而为、MUST NOT 作为成功判据——唯一判据是打完后的全文回读。

#### Scenario: 编辑器吞掉正文主体
- **WHEN** 编辑器只接受了正文的前若干字符，其余被静默丢弃
- **THEN** edge SHALL 回报 `content_not_accepted` 并清空编辑器
- **AND** MUST NOT 判成功、MUST NOT 提交

#### Scenario: composer 带着上一篇残稿
- **WHEN** 打开的 composer 内已存在上一次失败留下的正文
- **THEN** edge SHALL 先清空并校验为空再开始输入
- **AND** 清不干净则回报 `composer_not_clean`，MUST NOT 在残文之上追加、MUST NOT 开始打字
