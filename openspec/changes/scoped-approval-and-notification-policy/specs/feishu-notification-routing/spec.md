## MODIFIED Requirements

### Requirement: 一切出站消息按「来源会话 → 账号团队群 → 默认群」统一解析

除被分组 `client_only` 策略合法抑制的**无来源会话发布按钮审批卡**外，**每一条**出站飞书消息（入站平台通知、账号业务结果卡、审批卡、免审通知、运维 / 配置 / 验证码 / 风控告警）投递目标 SHALL 由**同一处**共享解析按下列补集式优先级决定，MUST NOT 由各调用点内联自建解析链：

1. **来源会话**——该消息属于一个由飞书命令事件创建、且持有非空来源会话（`originChatId`）的委托任务时，SHALL 投递到该来源会话（下命令的私聊或群）；分组 `client_only` MUST NOT 抑制该卡。
2. **账号团队群**——否则，消息带归属 `accountId` 时，SHALL 经 `resolveChatIdForAccount` 按 `accounts.group_label` → `group_route.chat_id` 路由到该账号的团队群。
3. **默认群**——否则（无来源会话且无归属账号、账号无 `group_label`、团队键未命中 `group_route`、或路由读取失败），SHALL 投递到默认群链的结果。

仅对已持久化 `pending_approval`、无来源会话、分组显式 `client_only` 且账号客户审批归属可证明的 `review` 发布稿，发送决策 MAY 在目标解析前抑制飞书按钮卡。该例外 MUST NOT 抑制评论免审通知、发布结果、失败、运维告警、飞书命令回执或任何有来源会话的发布审批卡。策略或归属不可读/不可证 MUST 回退发送并继续上述路由。

回落 SHALL 以**补集**实现（`来源会话为空 → 团队路由`；`团队路由未命中 → 默认群`），MUST NOT 以「哪些卡类型允许走团队路由」的白名单枚举实现——白名单会在新增卡类型时静默漏配，且漏配与配错在运营视角不可区分。

任何一层解析失败 MUST NOT 抛入投递闭包，SHALL 逐层 try/catch 穿透并回落下一档；未命中团队路由时 SHALL 输出 config-gap 日志。消息 MUST NOT 因未绑定团队或路由读取失败而被静默丢弃。

**本要求取代先前「面向运营方的卡片 / 告警 MUST NOT 按账号路由、SHALL 维持默认（管理）群」的例外**（运营方于 2026-07-16 显式定案）。据此：未被合法抑制的审批卡与带账号的运维告警 SHALL 按上述优先级走来源会话 / 团队群；只有**无归属账号**的告警（握手 config-error 等）才落默认群。

**已接受的暴露面（SHALL 显式记载，不得视为疏漏）**：飞书审批卡回调**不做任何权限校验**——回调只按卡内 `requestId` 关联应答，不校验点按者身份、不校验卡所在会话。因此「谁看得见审批卡＝谁能批准」，授权等价于可见性。而 `group_route` 仅存 `(group_label, chat_id)`、**无内部 / 外部标记**，故本规则对全部已映射团队一视同仁、无法按路由区分对待。由此，**若将来把外部客户群映射为某团队路由，该客户即自动获得该账号的批准按钮与运维可见性，系统内无闸可拦**。在引入「路由可信标记」之前，映射外部客户群 SHALL 由人工流程约束；本段 SHALL 保留为该后续改动的依据。

#### Scenario: 巡视通知走账号团队群
- **WHEN** 账号 `acc-1`（属 `teamA`）的通知巡视产出评论 / @ 通知
- **THEN** 该通知 SHALL 投递到 `teamA` 对应的群

#### Scenario: 排期业务结果卡走账号团队群
- **WHEN** 账号 `acc-1`（属 `teamA`，`group_route` 有 `teamA → oc_team_a_chat`）的排期发帖产出「本槽无新素材」结果卡、或排期评论产出「按需评论未产出」终态卡
- **THEN** 该卡 SHALL 投递到 `oc_team_a_chat`
- **AND** MUST NOT 因「卡片属命令回执类」而被硬绑默认（管理）群

#### Scenario: 命令触发的终态结果卡回来源会话、不走团队群
- **WHEN** 账号 `acc-1`（属 `teamA`，`group_route` 有 `teamA → oc_team_a_chat`）由飞书私聊 `/publish` 或 `/comment` 命令触发的委托任务产出终态结果卡、其任务持有来源会话 `P`
- **THEN** 该结果卡 SHALL 投递到 `P`
- **AND** MUST NOT 投递到 `oc_team_a_chat`

#### Scenario: 自动化审批卡默认走账号团队群
- **WHEN** 账号 `acc-1`（属 `teamA`，`group_route` 有 `teamA → oc_team_a_chat`）由无来源命令会话路径产出发布或评论审批卡，且没有有效 `client_only` 抑制决策
- **THEN** 该审批卡 SHALL 投递到 `oc_team_a_chat`
- **AND** MUST NOT 因「审批卡属运营方向」而被硬绑默认（管理）群

#### Scenario: 客户端可达的分组仅客户端稿件不发按钮卡
- **WHEN** 无来源会话的 review 发布稿属于 `client_only` 分组且账号客户审批归属可证明
- **THEN** Cloud 不发送飞书按钮审批卡，但稿件仍为 `pending_approval` 并可由客户端读取审批

#### Scenario: 飞书命令稿件始终回来源会话
- **WHEN** `/publish` 产生的 review 稿件持有非空来源会话，即使账号分组为 `client_only`
- **THEN** 发布审批卡 SHALL 发回来源会话，MUST NOT 被分组策略抑制

#### Scenario: 免审通知和其它消息不被仅客户端策略抑制
- **WHEN** `client_only` 分组账号产出评论免审通知、发布结果、失败或运维告警
- **THEN** 消息仍按统一解析投递，MUST NOT 因稿件审核入口策略被丢弃

#### Scenario: 带账号的运维告警走账号团队群
- **WHEN** 账号 `acc-1`（属 `teamA`）触发人设未绑 / 验证码 / 边缘离线 / CDP 不健康 / 发布熔断等运维告警
- **THEN** 该告警 SHALL 投递到 `teamA` 对应的群

#### Scenario: 无归属账号的告警落默认群
- **WHEN** 边缘握手 config-error 等**不带 `accountId`** 的告警产出
- **THEN** 该告警 SHALL 投递到默认群
- **AND** MUST NOT 为其臆造账号作用域以求得一个团队群

#### Scenario: 未绑定团队的消息仍落默认群、绝不丢
- **WHEN** 账号 `acc-2` 无 `group_label`，或其团队键在 `group_route` 无匹配行，或路由读取抛错，其任意出站卡片产出
- **THEN** 该卡 SHALL 投递到默认群链的结果
- **AND** SHALL 输出 config-gap 日志
- **AND** MUST NOT 因未绑定或读取失败而被静默丢弃

#### Scenario: 新增卡类型不得内联自建解析
- **WHEN** 新增一处出站卡片 / 告警的发送点
- **THEN** 其投递目标 MUST 经共享解析取得
- **AND** MUST NOT 内联 `resolveDefaultChatId` / `getDefaultChat` / `FEISHU_CHAT_ID` 自建目标——内联解析会绕过 config-gap 诊断，使「没接线」与「配错了」在运营视角不可区分
