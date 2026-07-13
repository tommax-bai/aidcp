## MODIFIED Requirements

### Requirement: 下发失败按副作用分界——离线回待审，序列失败终态

下发失败处理 SHALL 按「是否已对边缘产生副作用」分界：**边缘离线**（授权到达时没有可投递的在线 edge、指令未发出、零副作用）→ 草稿回 `pending_approval` + 作废该次授权信号 + 通知重批——关掉「批准后恰逢离线即烧稿」的窗口、保住生成与生图成本；**edge task acquire 超时**（已向在线 edge 投递 acquire、但在时限内未收到 `acquired`，零条发布业务命令）→ 同样回 `pending_approval` + 作废该次授权信号 + 通知重批，但通知 MUST 明确为“浏览器未完成接管/检查浏览器或 CDP”，MUST NOT 称为“边缘离线”；**指令序列中途失败**（页面状态未知）→ 保持 `failed` 终态，MUST NOT 自动重试（自动重跑有重复发帖风险）。所有路径 MUST 如实通知，绝不静默。

#### Scenario: 离线失败草稿可重批
- **WHEN** 授权到达时该账号无在线边缘节点
- **THEN** 草稿回到待审、该次授权信号被作废、运营收到“边缘离线请稍后重批”通知；边缘恢复后重批即可下发，内容零重生成

#### Scenario: 在线 edge 未在时限内接管浏览器
- **WHEN** 发布 acquire 已投递到在线 edge，但在 acquire 时限内未收到 `edge.task.acquired`，且尚未发送首条发布业务命令
- **THEN** 草稿保持待审、该次授权信号被作废、运营收到“浏览器未完成接管，请检查浏览器/CDP后重新批准”通知；通知 MUST NOT 声称边缘离线

#### Scenario: 序列失败不自动重跑
- **WHEN** 发布指令序列执行到中途失败（如选择器落空）
- **THEN** 该草稿判 `failed` 终态并如实通知；MUST NOT 对同一草稿自动重跑整条序列
