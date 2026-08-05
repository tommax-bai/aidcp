## ADDED Requirements

### Requirement: 正文填写的单步预算随长度伸缩，且边缘必先于云端答复

逐字符输入是 O(正文长度) 的操作，MUST NOT 由云端用与长度无关的常数窗口去等它——否则云端先判失败、边缘仍在往活着的编辑器里写字，形成「记录已 failed、页面上却躺着半篇正文」的错位，并让恢复后的浏览循环与被放弃的打字循环共用同一个 CDP session。

cloud SHALL 按正文长度算出 Facebook `fill_field` 的执行预算，随指令下发（复用既有的 `PublishCommandPayload.timeoutMs`）。云端等待窗口 SHALL 为「下发预算 + 兜底余量」，使边缘**必定先答**；该 timer 的语义 SHALL 退化为「边缘真的失联」的兜底，MUST NOT 作为正常路径的收敛手段。指令**不带**预算时（小红书全路径）等待窗口 MUST 逐字节沿用既有常数窗口。

预算上限 MUST 严格小于边缘发布租约 TTL（安全比例 0.4），否则边缘会在打字途中单方面过期租约、恢复浏览循环去驱动半写的编辑器。

默认配置 SHALL 使用 20 秒固定开销、每字 250 毫秒和 400 秒预算上限，因此 Facebook 正文逐字输入硬上限为 1520 字；默认发布租约 SHALL 为 1000 秒，使填写预算继续不超过租约的 0.4。

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

#### Scenario: 默认 1520 字边界
- **WHEN** Facebook 正文按默认配置包含 1520 个 Unicode 码位
- **THEN** cloud SHALL 允许进入命令序列，并为正文填写下发 400 秒预算
- **AND** 1521 个 Unicode 码位 SHALL 以 `content_too_long` 在零下发状态诚实失败

#### Scenario: 小红书路径不受影响
- **WHEN** 发布平台为小红书
- **THEN** 指令 MUST NOT 携带执行预算，云端等待窗口 MUST 与既有常数窗口逐字节一致

### Requirement: 正文校验必须回读全文

「插入调用没报错」不等于「文本进去了」。正文校验 MUST 回读编辑器**全文**并确认其完整包含终稿正文；MUST NOT 以正文前缀片段作为接受判据——前缀探针会把「编辑器吞掉正文主体」判成成功，从而真的发出一篇被截断的帖子。

编辑器内出现超出终稿正文的额外内容（如打字途中被 typeahead 劫持插入）MUST 视为失败，MUST NOT 提交。

打字前 edge MUST 先清空编辑器并校验其为空：composer 会复用已存在的编辑区、而输入是在光标处**追加**，不清空即会把上一次失败留下的残稿与本篇拼接后发出。

聚焦不是最终成功判据，但 SHALL 是开始输入前的强制前置条件。edge MUST 将焦点绑定到本次唯一定位到的
编辑器，并确认 `document.activeElement` 正是该编辑器后，才允许派发清空或字符输入；MUST NOT 把
“坐标点击已完成”或“某个当前焦点的文本恰好为空”当作目标编辑器已聚焦。编辑器焦点不能确认时，
edge SHALL 诚实回报未开始并保持零字符派发。最终成功判据仍是目标编辑器的全文回读。

Facebook 在选择图片后可能保留旧 composer 并新建一代携带图片的前台 composer。edge SHALL 将文件
输入、图片预览、正文编辑器和提交按钮绑定到同一代前台 composer，MUST NOT 用 DOM 顺序中的第一个
dialog 作为目标。存在多个可见 composer 时，只有唯一位于最上层且包含唯一可见编辑器的 composer
可以成为当前目标；无法唯一确立时 SHALL 以 `ambiguous_target` 停手。

上传成功必须由当前 composer 内与本次文件名一致的新增 `blob:` 图片预览证明。页面头像、既有网络
图片、其他 dialog 或旧 composer 内的图片 MUST NOT 作为上传成功证据。上传引发 composer 换代时，
edge SHALL 在上传确认后重新绑定新一代前台 composer，再开始正文清场与输入。

逐字输入期间，edge SHALL 在每个字符派发前确认 `document.activeElement` 仍是本次绑定的编辑器。
焦点或目标身份漂移时 SHALL 在下一个字符前停止并回报 `composer_focus_lost`，MUST NOT 把剩余正文
继续写入任意当前焦点。失败清场只能作用于仍可确认的同一编辑器；目标归属不明时 MUST 如实标记脏页。

#### Scenario: 编辑器吞掉正文主体
- **WHEN** 编辑器只接受了正文的前若干字符，其余被静默丢弃
- **THEN** edge SHALL 回报 `content_not_accepted` 并清空编辑器
- **AND** MUST NOT 判成功、MUST NOT 提交

#### Scenario: composer 带着上一篇残稿
- **WHEN** 打开的 composer 内已存在上一次失败留下的正文
- **THEN** edge SHALL 先清空并校验为空再开始输入
- **AND** 清不干净则回报 `composer_not_clean`，MUST NOT 在残文之上追加、MUST NOT 开始打字

#### Scenario: 坐标点击没有把焦点交给目标编辑器
- **WHEN** edge 已点击编辑器坐标，但 `document.activeElement` 仍不是本次唯一定位到的编辑器
- **THEN** edge SHALL 对该编辑器执行有界的程序化聚焦并重新确认目标身份
- **AND** 仍不能确认时 SHALL 零字符失败，MUST NOT 向错误焦点逐字输入

#### Scenario: 图片上传换代后旧 composer 仍留在 DOM
- **WHEN** 上传图片后 Facebook 保留旧 composer，并新建携带本次图片预览的前台 composer
- **THEN** edge SHALL 在新 composer 的编辑器内填写正文，旧 composer 保持不变
- **AND** 头像或旧 composer 的图片 MUST NOT 提前确认上传成功

#### Scenario: 逐字输入中途焦点漂移
- **WHEN** 已输入正文前缀后，页面把焦点移到另一个 composer 或页面控件
- **THEN** edge SHALL 在派发下一个字符前停止并回报 `composer_focus_lost`
- **AND** 剩余正文 MUST NOT 写入新焦点，失败结果的外层 `reasonCode` MUST NOT 为 `confirmed`

### Requirement: 正文长度在生成侧确定性收口，且越界不得截断或废稿

各平台正文长度区间 MUST 有唯一事实源，生成 prompt 里的长度要求与生成后的校验 MUST 读同一处；
MUST NOT 在两处各写一份数字——改一处而另一处照旧不会产生任何报错，症状只是「规则明明写着却不生效」。

云端 MUST 在内容生成后对正文长度做确定性判定，MUST NOT 只依赖 prompt 里的软提示。
长度判定 MUST 按码位计数，与边缘逐字输入循环及填写预算换算同口径。

判定结果 MUST 分三态，且三态的处置各不相同：

- 落在区间内 SHALL 直接采用。
- 越界但在容差内 SHALL 采用并记录偏离，MUST NOT 触发重写——为几个字重写等于给几乎每一篇多付一次
  模型调用，而后果只是篇幅偏离、完全可恢复。
- 越出容差 SHALL 带纠正说明重写，且重写 MUST 有上限。纠正说明 MUST 点名实测字数、目标区间与修改方向；
  不携带这三项的重试只是重掷一次骰子，期望值与首稿相同。

重写次数用尽后正文仍越出容差时，系统 SHALL 采用偏离较小的一稿并响亮记录，
**MUST NOT 中止发布管线**（长度区间是质量目标而非物理约束，为它废掉整篇稿子是过度加闸），
**MUST NOT 截断正文以「满足」区间**（截断产生残句，且会把「模型没有遵从要求」伪装成一次正常产出）。

`content_too_long` 仍 SHALL 作为下发前的诚实闸保留，但 MUST NOT 被当作长度问题的解法：
它在图片已生成、人工已审核之后才响。

#### Scenario: 正文略微超出区间
- **WHEN** 生成的正文越界幅度落在容差内
- **THEN** 系统 SHALL 采用该稿并记录实测长度与偏离
- **AND** MUST NOT 因此重新调用模型

#### Scenario: 正文长度离谱
- **WHEN** 生成的正文越出容差
- **THEN** 系统 SHALL 附带实测字数、目标区间与修改方向重写，且重写次数受上限约束
- **AND** 重写后合格则采用重写稿

#### Scenario: 重写后仍然越界
- **WHEN** 重写次数用尽而正文仍越出容差
- **THEN** 系统 SHALL 采用偏离较小的一稿并记录该事实
- **AND** MUST NOT 截断正文，MUST NOT 中止发布管线

### Requirement: 在途发布的诚实回执与页面写者在场是两件事

断连、暂停与执行器故障等回收路径 MUST 立即把全部在途发布诚实判失败并发出回执，
使云端与审批侧看到失败而非半成品。

但「回执已发出」MUST NOT 被读成「页面已经空出来」。发布 dispatch 仍在页面上按自身预算逐字输入，
只有它自己的收敛才证明写者离开。因此判定「普通浏览可否恢复」的探针 MUST 反映**页面写者在场**，
MUST NOT 读那张会被回收路径整表清空的回执登记。

两者混用的后果不是重复发帖（提交另有租约闸挡住），而是**两个写者短暂共用同一个页面**：
恢复导航把发布页导走，发布一侧看到的是自己写入的正文凭空消失。

写者在场计数 MUST 由 dispatch 自身的生命周期成对增减，且加计与其后必然执行的减计之间
MUST NOT 存在可抛出的语句——一次未配对的加计会让浏览永久冻结。

#### Scenario: 云端连接断开时正文仍在输入中
- **WHEN** 回收路径已为在途发布发出诚实失败回执，而 dispatch 仍在页面上逐字输入
- **THEN** 普通浏览 SHALL 保持封锁，直到该 dispatch 真正收敛
- **AND** dispatch 收敛后 SHALL 恢复浏览
