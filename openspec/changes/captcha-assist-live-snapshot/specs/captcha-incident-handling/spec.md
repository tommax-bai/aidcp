## ADDED Requirements

### Requirement: 验证码可交互态必须近实时回传现场帧

当验证码 incident 处于可交互态时，系统 SHALL 支持边缘对该 incident 运行一个**有界、自终止、内容去重**的低帧率抓帧循环，使控制台总能看到接近活体的挑战画面。该能力 MUST 复用既有 `captcha.assist.capture` 命令的可选 `live` 字段进入（MUST NOT 新增 MessageType、MUST NOT 新增未在 edge onMessage 白名单内的主动命令）。本能力服务**自刷新 / 多步换图的点选类**验证码；滑块/拖拽类不在范围。抓帧只读、MUST NOT 篡改页面。

#### Scenario: 进入与不带 live 的零回归
- **WHEN** 云端以带 `live` 的 `captcha.assist.capture` 请求抓帧
- **THEN** 边缘推首帧后进入有界实时循环
- **AND** 不带 `live` 的 capture MUST 维持今天的单次抓帧行为（零回归）

#### Scenario: 内容去重且有最小推帧间隔
- **WHEN** 实时循环每个 tick 抓到一帧
- **THEN** MUST 与上次已推帧做内容比较，内容未变 MUST NOT 推送
- **AND** MUST 有最小推帧间隔硬地板与单帧字节/帧率上限，即便去重被动画/倒计时击穿也不全速推大图

#### Scenario: 循环三重有界自终止
- **WHEN** 实时循环运行
- **THEN** MUST 受最大时长、最大帧数、遮罩消失三重约束自终止，MUST NOT 遗留孤儿循环
- **AND** 收敛 MUST 用注入 timer + 迭代计数，MUST NOT 拿 `now()` 当终止条件（防桩测恒定 now 死循环）

#### Scenario: 抓帧与点击互斥
- **WHEN** 边缘正在派发协助点击
- **THEN** 实时 tick MUST 被 `clicking` 互斥暂停，避免抓到点击派发中途的半程态

#### Scenario: 实时窗口绑运营在场
- **WHEN** 运营尚未打开协助页
- **THEN** 系统 MUST 以控制台既有轮询等在场信号 re-arm 抓帧，MUST NOT 仅靠一个固定盲目窗口在运营到场前就自终止

#### Scenario: 迟到实时帧不复活已清除态
- **WHEN** 一帧实时 snapshot 在 incident 已 `cleared`/`expired` 之后到达
- **THEN** 云端 MUST 忽略该帧、MUST NOT 把状态复活为 `ready`

#### Scenario: 控制台选点期冻结与多步换图区分
- **WHEN** 运营已放下至少一个落点、其后实时帧到达
- **THEN** 控制台 MUST 冻结当前画面与已选点（周期自刷新的同一挑战不冲掉选点）
- **AND** 当挑战内容实质改变（换问题）时 MUST NOT 静默沿用旧帧让运营点错，MUST 给显式"挑战已变、请重看"提示并允许手动解冻到最新帧

## MODIFIED Requirements

### Requirement: 人工点击必须由原 edge 注入原浏览器并绑定 snapshot

协助页提交点击时，cloud SHALL 将点击序列作为归一化坐标发送给该 incident 绑定的原 edge；edge MUST 校验 incident、snapshot、当前阻断态和坐标边界后，将坐标映射回当前浏览器视口并派发真实输入事件。**当实时抓帧开启时，snapshot 绑定 MUST 放宽为"近期帧集"**：边缘 MUST 为每个 incident 保留最近 N 帧环、云端 MUST 相应保留最近 N 帧集，`submitClick` 的 `snapshot_mismatch` 守卫 MUST 放宽为"提交的 `snapshotId ∈ 近期集"，并用**该被点帧自己的 crop** 缩放坐标——否则运营点的稍旧但"与所见一致"的帧会被云端上游拦死、边缘帧环成死代码、白跑不降反升。cloud MUST NOT 在自身环境执行点击，MUST NOT 将点击命令广播到多个 edge，MUST NOT 用 DOM 状态篡改替代用户输入。

#### Scenario: 有效点击序列派发到原 edge
- **WHEN** 操作者基于最新 snapshot 提交两个图片点位和一个验证按钮点位
- **THEN** cloud 只向绑定 edge 发送点击命令，edge 将这些点映射到原浏览器并通过输入事件执行

#### Scenario: 稍旧但在近期集内的帧可提交
- **WHEN** 实时抓帧已推进 latest，但操作者提交的是被冻结的稍旧帧、其 `snapshotId` 仍在近期 N 帧集内
- **THEN** cloud MUST 放行该点击，edge MUST 用该被点帧自己的 crop 缩放坐标注入，MUST NOT 因非 latest 而判 `stale_snapshot`

#### Scenario: 超出近期集的 stale snapshot 拒绝点击
- **WHEN** 操作者基于已被挤出近期集或已过期的 snapshot 提交点击
- **THEN** cloud 或 edge MUST 拒绝该点击并返回 `stale_snapshot`，MUST NOT 盲目点击当前页面

#### Scenario: edge 当前不在阻断态
- **WHEN** edge 收到 assist 点击命令但 fresh probe 显示当前已无 captcha/unknown 阻断
- **THEN** edge MUST 不执行点击，并发送或保持 `risk.captcha_cleared` 的正常清除路径

### Requirement: 远程协助后的恢复必须由 edge 复检清除驱动

edge 执行远程协助点击后 SHALL 等待有界 settle 时间并重新探测阻断遮罩。仅当 fresh probe 确认 captcha/unknown 遮罩已消失时，edge SHALL 发送 `risk.captcha_cleared`，cloud 才 SHALL 解除该 edge 暂停；如果遮罩仍存在，系统 MUST 返回 still_blocked，并允许操作者刷新截图后重试。**实时抓帧循环 MUST NOT 用单次 probe 看不到遮罩就自主发 `risk.captcha_cleared`**：多步验证码在旧挑战消失、新挑战未绘出之间存在瞬时无遮罩窗口，自主判 cleared MUST 经连续 K 次确认 + 最小 settle 才成立。**实时循环的自主 probe 结果 MUST NOT 经 `click_result` 混入 `incident.lastResult`**，以免把非运营发起的探测记成一次复检、污染审计与前端"上次复检"。cloud MUST NOT 因点击命令成功送达、Feishu 链接被打开、协助页按钮被点击或告警被手动解决而恢复 edge。

#### Scenario: 点击后验证码清除
- **WHEN** edge 执行 assist 点击序列后 fresh probe 显示阻断遮罩消失
- **THEN** edge 发送 `risk.captcha_cleared`，cloud 通过既有 onCleared 路径恢复该 edge 下发并标记 incident cleared

#### Scenario: 实时循环瞬时无遮罩不误清除
- **WHEN** 实时循环某一 tick 的单次 probe 未见遮罩，但下一挑战尚未绘出
- **THEN** 系统 MUST 要求连续 K 次确认 + 最小 settle 后才判 cleared，单次未见 MUST NOT 触发 `risk.captcha_cleared` 或提前解 `restricted`

#### Scenario: 自主探测不混入运营复检结果
- **WHEN** 实时循环自主 probe 得到状态
- **THEN** 该结果 MUST NOT 经 `click_result` 通道写入 `incident.lastResult`，前端"上次复检"只反映运营点击发起的复检

#### Scenario: 点击后仍被阻断
- **WHEN** edge 执行 assist 点击序列后 fresh probe 仍显示 captcha/unknown
- **THEN** edge 返回 still_blocked，cloud 保持该 edge 暂停并向协助页展示新的处理状态

#### Scenario: 手动解决告警不恢复 edge
- **WHEN** 操作者在告警列表中手动解决对应 captcha 告警但 edge 尚未发送 `risk.captcha_cleared`
- **THEN** cloud MUST 只闭合告警日志行，MUST NOT 将 incident 标记 cleared，MUST NOT resume 该 edge
