# comment-interaction Specification

## Purpose
TBD - created by archiving change comment-interaction. Update Purpose after archive.
## Requirements
### Requirement: 评论支线接在互动完成与进主页评估之间

系统 SHALL 把评论支线挂在 `interaction.completed`（即**仅在该笔记真发生过 like / collect 时**才进入评论评估），
并把"是否进个人主页"的判断（`AuthorEvaluator`）的触发**从 `interaction.completed` 改挂到评论支线的终结事件**（`comment.done` / `comment.skipped`）。
评论支线 MUST 在笔记详情页仍打开时整条跑完；评论成功 / 跳过 / 失败 MUST 都汇到"是否进主页评估"这唯一出口、且每篇 MUST 只触发一次该评估。
评论支线 MUST NOT 在评论结束后直接进入个人主页（MUST 经"是否进主页评估"，该评估可决定不进 / 已关注跳过）。
系统 MUST 使用独立 `comment.*` 事件族，MUST NOT 复用或扩宽 `InteractionCompletedPayload.actions`（其同时被命令翻译与 `AuthorEvaluator` 消费）。

#### Scenario: 互动后进入评论评估，再评估是否进主页
- **WHEN** 某笔记 `InteractionAppraiser` 选择 like / collect 并 emit `interaction.completed`
- **THEN** 评论支线（`CommentAppraiser`）启动；其终结（`comment.done` 或 `comment.skipped`）后才触发 `AuthorEvaluator` 的"是否进主页"判断；like/collect 命令仍在 `interaction.completed` 同步下发、评论命令在评论支线内下发，二者在评论完成（真回执）之前 MUST 先于任何 `profile_open` / 返回导航

#### Scenario: pass 的笔记不评论也不进主页
- **WHEN** `InteractionAppraiser` 判 pass 并 emit `interaction.skipped`
- **THEN** 评论支线 MUST NOT 触发（评论只在已互动的笔记上发生），照旧由 `BackToFeed` 回流刷下一篇

#### Scenario: 评论失败仍走进主页评估、不死锁
- **WHEN** 评论命令回报 `ok:false`（找不到框 / 未生效 / 验证码）
- **THEN** 评论支线 MUST emit 终结事件触发"是否进主页评估"，MUST NOT 卡死在详情页、MUST NOT 重复触发该评估

#### Scenario: 红线反例——评论完直接进主页或挂错事件（禁止）
- **WHEN** 有实现让评论完成后直接 emit `profile.entered` / 直接下发 `profile_open`，或仍让 `AuthorEvaluator` 直接消费 `interaction.completed` 而绕过评论支线，或扩宽 `InteractionCompletedPayload.actions` 容纳 `comment`
- **THEN** MUST 视为违规、不予合入；进主页 MUST 经"是否进主页评估"，且该评估 MUST 由评论支线终结事件触发

### Requirement: 评估→撰写→去AI味→审批四段单职责角色

系统 SHALL 以四个独立角色实现评论支线，**评估与撰写 MUST NOT 合并**：`CommentAppraiser`（只判定要不要评、产判定不产文本）→
`CommentComposer`（产评论文本）→ `CommentDeAiFlavor`（去 AI 味 + 合规声明判定：**检测步**确定性无 LLM；**改写步**在命中 AI 味信号或与参考语料撞车时按**该账号人设口吻**做至多一次 LLM 改写，改写失败 / 超时 MUST 回退原文、不抛异常）→
`CommentApprovalGate`（循环内飞书人审）。任一段失败 / 不通过 MUST emit `comment.skipped` 并带如实原因，MUST NOT 伪造文本或伪造通过。
`CommentComposer` 作为浏览闭环首个自由文本角色，MUST 自己保证：空 / 超长文本如实跳过、做跨笔记近似去重、撰写时避开裸 `@`（编辑器带 `data-tribute` 提及）；并 SHALL 提供**语义弃权出口**——对着笔记确实写不出有真实内容的话时，MUST 返回弃权（`nothing_genuine`）走 `comment.skipped` 分支，MUST NOT 硬凑客套话（客套敷衍正是评论体裁的 AI 味主形态）。

#### Scenario: 评估为是才进入撰写

- **WHEN** `CommentAppraiser` 判定该笔记值得评论且配额/门槛通过
- **THEN** emit `comment.appraised` 触发 `CommentComposer` 产文本 → `CommentDeAiFlavor` 去 AI 味 / 合规 → `CommentApprovalGate`；评估为否则 emit `comment.skipped`，不进入撰写（不付 LLM 撰写成本）

#### Scenario: 去AI味检测步确定性、改写步失败回退

- **WHEN** `CommentComposer` 产出草稿文本
- **THEN** `CommentDeAiFlavor` 的 AI 味检测 MUST 为确定性规则（无 LLM、可独立单测）；命中信号触发的人设口吻改写走 LLM，改写失败 / 超时 MUST 回退检测前原文并继续流程，MUST NOT 抛异常中断评论支线

#### Scenario: 撰写诚实弃权不硬凑

- **WHEN** `CommentComposer` 面对已判值得评的笔记仍写不出有真实内容的评论（LLM 返回弃权）
- **THEN** MUST emit `comment.skipped{reason:'nothing_genuine'}`，不进入去 AI 味与审批；评论支线照常收敛（下游进主页评估不受影响）

#### Scenario: 红线反例——撰写失败伪造文本（禁止）

- **WHEN** `CommentComposer` LLM 失败 / 产空文本，但实现回退到模板/占位文本照常提交
- **THEN** MUST 视为违规、不予合入；MUST emit `comment.skipped{reason}`，绝不发出无法落地的伪造评论

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬门槛**：该门槛的阈值 SHALL **按内容品类 / 账号可配**（可表达为热度绝对下限、或收藏/点赞比例、或百分位），并按品类给出合理默认；MUST NOT 对所有品类 / 账号写死同一组绝对值（例如固定 `likeCount>1000` **且** `collectCount>300`），以免系统性排除「高赞低藏」的情感 / 颜值类正当爆帖。**通用默认地板** SHALL 为：`likeCount > 300` **且**（`collectCount > 100` **或** `likeCount > 10000` 超高热豁免），边界均为严格大于——把中腰部高收藏内容（教程 / 攻略 / 清单类）纳入候选，同时保留超高热爆帖对收藏绝对值的豁免。**无「收藏」概念的平台**（如 Facebook，其平台词汇 profile 的收藏名词为空）SHALL **只放宽收藏合取项**（收藏子句恒真）、**主门槛 `likeCount > 300` 恒保留**，MUST NOT 因该平台收藏数恒为 0 而退化为无门槛或必须万赞爆帖才可评（该退化正是「收藏绝对值未过固定线就必然不达门槛」在无收藏平台上的极端形态）。为控成本，该硬门槛 SHALL 尽量在**最便宜阶段（调 LLM 之前）**确定性判定，MUST NOT 退化为宽松纯 OR 让过多笔记落到昂贵 LLM 判定。任一不满足门槛 MUST 直接 `comment.skipped`、不进入撰写 / 去 AI 味 / 审批。硬门槛之上，现有 LLM 精品判定（高热度 + 高价值）与飞书人审继续叠加（门槛为必要非充分条件）。此外系统保留**按账号、可持久化的每日评论上限配置**（运营在 console 后台读写、经面板 `/api` 下发）；**实际生效每日上限 = min(运营配置上限, 风控安全配额)**，"今日已评数" MUST 复用风控按账号按天计数。数量、门槛与阈值 MUST 在评估阶段就判定：超上限 / 不达门槛 / LLM 判不值得 MUST 直接走"不评论 → 进主页评估"分支，MUST NOT 进入撰写 / 去 AI 味 / 审批。

#### Scenario: 达到每日上限即停止评论

- **WHEN** 某账号当日已评数 ≥ min(运营配置上限, 风控配额)
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'daily_cap_reached'}`，当日不再评论，直接进"是否进主页评估"

#### Scenario: 运营配置不可越过风控安全线

- **WHEN** 运营把每日上限配成高于风控 `comment` 安全配额
- **THEN** 生效上限 MUST 取风控安全配额（取小），MUST NOT 因运营配置突破封号安全线

#### Scenario: 未达品类/账号硬门槛不评

- **WHEN** 笔记未达该品类 / 账号解析出的硬门槛（按详情页真实点赞 / 收藏量或其比例；通用默认地板为 赞 > 300 且（藏 > 100 或 赞 > 10000））
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'below_comment_threshold'}`，在调 LLM 之前即跳过，不进入撰写

#### Scenario: 中腰部高收藏笔记按新默认地板可入候选

- **WHEN** 一篇笔记 `likeCount = 500`、`collectCount = 150`（旧默认地板 1000 赞下必被排除）
- **THEN** 该笔记通过通用默认地板进入 LLM 精品判定（是否真评论仍由 LLM + 人审决定）

#### Scenario: 无收藏平台按放宽收藏合取项入候选（主门槛仍守）

- **WHEN** 一篇 Facebook 帖 `likeCount = 500`、`collectCount = 0`（该平台无收藏概念、收藏名词为空）
- **THEN** 收藏合取项恒真、主门槛 `likeCount > 300` 满足 ⇒ 该帖通过硬门槛进入 LLM 精品判定，MUST NOT 因收藏数为 0 就判未达门槛

#### Scenario: 无收藏平台主门槛不退化为无门槛

- **WHEN** 一篇 Facebook 帖 `likeCount = 300`（恰等主门槛边界、`collectCount = 0`）
- **THEN** MUST 视为未达门槛不评（主门槛为严格大于、等于不算达标）——放宽收藏合取项 ≠ 无门槛

#### Scenario: 高赞低藏爆帖不再被固定绝对值一律排除

- **WHEN** 一篇情感 / 颜值类高赞低藏笔记（如高点赞、收藏绝对值不高）进入评估
- **THEN** 硬门槛按其品类 / 账号口径判定（比例 / 品类默认 / 超高热豁免），MUST NOT 仅因「收藏绝对值未过固定线」就必然判未达门槛

#### Scenario: 门槛边界严格判定

- **WHEN** 笔记指标恰好等于解析出的阈值边界（如 `likeCount === 300` 或 `collectCount === 100`）
- **THEN** MUST 视为未达门槛、不评（「超过」语义为严格大于，等于不算达标）

#### Scenario: 达门槛仍需过 LLM 与人审

- **WHEN** 笔记通过品类 / 账号硬门槛
- **THEN** 该笔记仅**通过硬门槛**进入后续判定，是否真评论仍由 LLM 精品判定 + 飞书人审决定（门槛是必要非充分条件）

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

因评论 MUST 在详情页打开时发出，审批 SHALL **循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经飞书人审授权。

评论支线在途期间系统 MUST 进入**被看门狗认得的「评论支线在途」暂停态**（复用按-edge 暂停通道）。该暂停态：

- **覆盖范围为评论支线在途全程**：从该笔记进入评论支线（互动完成后开始评估/撰写）起，到该笔记评论支线终局（`comment.done` 或 `comment.skipped`）止；MUST NOT 只覆盖 `comment.cleared` 之后的审批等待段，因为评估 / 撰写 / 去 AI 味阶段（数秒到数十秒）内账号同样 MUST 停在待评论帖上。
- **经统一命令出口生效**：暂停 MUST 由发命令的统一出口（软暂停闸）扣住一切会离开当前待评论帖的浏览 / 互动命令——包括并行互动回执触发的 stale-target 重扫滚屏、idle 看门狗的恢复滚屏、换帖 `open_note`、`refresh`、feed 续滚。MUST NOT 退化为只在单个 idle-nudge 翻译点做门控（该退化会漏掉上述其余出口）。
- **看门狗按"有意暂停"处理**：暂停期间 idle 计时 MUST 冻结（不因无浏览上报累积 idle 而 nudge / 结束会话）。
- **窗内不提前结束会话**：暂停期间由动作数 / 时长 / 配额上限触发的 `session.should_end` MUST 推迟到评论支线终局后再评估，MUST NOT 在评论支线在途时结束会话而废掉一条正在人审 / 已授权的评论；但 `session.end` 本身 MUST 仍可达（暂停不得阻塞真正需要的结束）。
- **终局解除顺序严格（读评 surface 相等时）**：读、评 surface 相等的账号（如小红书，迁移结构性不可达），`comment.approved` / `comment.skipped` 终局 MUST 先解除暂停态并恢复看门狗计时，再下发已授权评论命令——否则评论命令会被自己设的暂停态扣住。
- **迁移在途持续抑制离页命令（读评 surface 不等时）**：读、评 surface 不等的账号（如 Facebook：读 feed、评论 detail，`comment.approved` 后经 `open_note{purpose:'navigate'}` 两步迁移），离页命令抑制 MUST **覆盖整个迁移在途窗口**（从迁移 navigate 命令下发起，到浏览器落地详情、评论命令下发止），期间 MUST 继续经统一命令出口扣住一切会离页的浏览 / 互动命令（`page.scroll` / 换帖 `open_note` / `refresh` / feed 续滚 / stale-target 重扫）；否则迁移落地前后并发的 scroll 会经边缘 `ensureFeed` 把浏览器整页拽回列表面、迁移拿不到详情、已批准评论被丢。本迁移的 `open_note{purpose:'navigate'}` 命令与落地后的 `comment` 命令 MUST **豁免**该抑制（它们即迁移支线本身），MUST NOT 被自己设的抑制扣住而静默丢弃。该迁移在途抑制窗口 MUST 有界，并在迁移终局（落地回执 / 迁移下发被拦 / 被抢占 / 会话 reset）解除，MUST NOT 悬挂钉死会话。

MUST 设**硬性短超时**（可信停留上限）；超时 / 拒绝 MUST 视为本篇不评、记审计、emit `comment.skipped` 进"是否进主页评估"。
审批 MUST 复用既有 `/tmp` 先到先得审批信号机制、用**评论专属 requestId 命名空间**（与发帖 `publish-<recordId>` 区分）；**未获授权 MUST NOT 下发评论命令**。

该暂停态跨平台一致：小红书（读评同为详情面，评论就地直发）与 Facebook（读 feed、评论 detail，`comment.approved` 后经 `open_note{navigate}` 两步迁移、迁移在途窗口持续抑制离页命令）均适用。

#### Scenario: 授权后下发、超时则跳过
- **WHEN** 飞书人审在超时窗口内写入评论 requestId 的授权信号
- **THEN** `CommentApprovalGate` MUST emit `comment.approved` 触发评论命令下发；若窗口内未授权 / 被拒，MUST emit `comment.skipped{reason:'approval_timeout'|'rejected'}`、退出暂停态、进"是否进主页评估"

#### Scenario: 撰写窗内并行互动回 no_target 不得把目标帖滚走
- **WHEN** 评论支线已进入（评估 / 撰写 / 去 AI 味在途、`comment.cleared` 尚未发出），同一笔记的并行互动（点赞 / 收藏）回执带 `ok:false, reason:'no_target'`
- **THEN** 系统 MUST NOT 因该回执下发 stale-target 重扫滚屏（或任何离开当前待评论帖的命令）；账号 MUST 停在待评论帖上直到评论支线终局；该互动如实记为失败（不假成功、不重扫）

#### Scenario: 审批窗内 stray 边缘上报不得下发移动命令
- **WHEN** 浏览会话处于"评论支线在途"暂停态，其间到达任一边缘上报（迟到的 `page.cards` / feed 上报 / 互动回执等）
- **THEN** 系统 MUST NOT 经统一命令出口下发 `open_note` 换帖 / `scroll` / `refresh` 等会离开当前待评论帖的命令；仅 `session.end` 与暂停通道放行的命令可达

#### Scenario: 审批窗内不因动作数/时长/配额提前结束会话
- **WHEN** 浏览会话处于"评论支线在途"暂停态，其间一条边缘回执使动作数 / 时长 / 配额触及会话结束阈值
- **THEN** `session.should_end` MUST 推迟到评论支线终局（`comment.done` / `comment.skipped`）后再评估，MUST NOT 在评论在途时结束会话废掉在审 / 已授权评论

#### Scenario: 等待审批期间不卡死会话、不误判 idle
- **WHEN** 浏览会话处于"评论支线在途"暂停态
- **THEN** 看门狗 MUST 按"有意暂停"处理、MUST NOT 因 idle 重启或结束会话；该 edge 的其他浏览 / 互动命令 MUST 在暂停期间不下发，`session.end` MUST 仍可达

#### Scenario: 读评 surface 相等——终局先解除暂停再下发评论
- **WHEN** 评论支线到达终局（`comment.approved` 或 `comment.skipped`），且该账号读、评 surface 相等（如小红书，迁移不可达）
- **THEN** 系统 MUST 先解除暂停态并恢复看门狗计时，再下发已授权评论命令；MUST NOT 让评论命令被残留暂停态扣住而静默丢弃

#### Scenario: 读评 surface 不等——迁移在途持续抑制离页命令、放行迁移与评论
- **WHEN** `comment.approved` 后该账号读、评 surface 不等（如 Facebook），系统经 `open_note{purpose:'navigate'}` 两步迁移，迁移 navigate 尚未落地详情
- **THEN** 系统 MUST 在整个迁移在途窗口继续经统一命令出口扣住一切会离页的浏览 / 互动命令（`page.scroll` / 换帖 `open_note` / `refresh` / feed 续滚 / stale-target 重扫），使并发 scroll 不会经 `ensureFeed` 把浏览器拽回列表面；同时 MUST 放行本迁移的 `open_note{purpose:'navigate'}` 与落地后的 `comment` 命令；该迁移在途窗口 MUST 有界并在迁移终局解除，MUST NOT 悬挂钉死会话

#### Scenario: 红线反例——未授权或超时仍发评论（禁止）
- **WHEN** 有实现在无授权信号 / 超时后仍下发评论命令，或为绕开"页面久留"把评论改成无人审自动直发
- **THEN** MUST 视为违规、不予合入；评论 MUST 在授权信号存在时才下发（AC-PUB），未授权 / 超时一律 `comment.skipped` 不发

### Requirement: 执行端发评论动作——拟人输入 + 发布后校验、绝不假成功

边缘 SHALL 实装 `executeComment`：① 点折叠态评论入口（`.engage-bar .input-box .content-edit .not-active.inner-when-not-active`，"说点什么"）激活编辑器；
② 点编辑器本体（`p#content-textarea.content-input[contenteditable]`）落 caret；③ `dispatchKeystrokes` 拟人逐字输入；
④ 提交前 `captchaPresentFresh` 自检；⑤ 点提交键（`.engage-bar.active … button.btn.submit`，"发送"；空/无效内容时带 `.gray` 禁用、有效内容后 `.gray` 消失）；
⑥ **后置校验：编辑器清空 且 自己的评论作为顶部新 `div#comment-<id>` 行出现**。MUST 经既有 `reportActionCompleted{action,ok,reason}` 如实回报；
找不到框 / 按钮回 `no_target`、提交后未生效回 `state_unchanged`、验证码回 `blocked_by_captcha`。MUST NOT 静默假成功。MUST 复用 `LocatingEngine` 三道闸、不破坏其接口。

#### Scenario: 发布成功的判定
- **WHEN** 输入文本、点"发送"后，编辑器清空且评论列表顶部出现包含本次文本的新 `div#comment-<id>` 行
- **THEN** `executeComment` MUST 回 `reportActionCompleted{action:'comment', ok:true}`；评论数文本不可靠，MUST NOT 仅凭计数判定

#### Scenario: 找不到框 / 提交无效如实回报
- **WHEN** 评论框 / 提交键定位失败，或点击"发送"后编辑器未清空且无自己的评论行出现
- **THEN** MUST 回 `ok:false` 且 `reason` 为 `no_target` / `state_unchanged`；MUST NOT 回 `ok:true`

#### Scenario: 提交前命中验证码
- **WHEN** 提交前 `captchaPresentFresh` 检出验证 / 安全浮层
- **THEN** MUST 回 `ok:false, reason:'blocked_by_captcha'`，MUST NOT 提交、MUST NOT 假成功

#### Scenario: 红线反例——点了发送就当成功（禁止）
- **WHEN** 有实现点击"发送"后不做后置校验即回 `ok:true`
- **THEN** MUST 视为违规、不予合入；`ok:true` MUST 以"编辑器清空 且 自己的评论行出现"为前提

### Requirement: 协议 v2 新增 interaction.comment 并三处同步

系统 SHALL 新增 cloud→edge 消息 `interaction.comment`（payload `CommentPayload{noteId, text, thinkMs?}`）。
两份 `src/comm/protocol.ts`（edge / cloud）MUST 逐字一致新增该 `MessageType` 与 payload；`command-bridge.ts` MUST 加 `comment → interaction.comment` 映射；
`EdgeCommand.action` 并集 MUST 加 `comment`；`docs/protocol.md` 头部计数与 §2 表 MUST 同步；两份 `protocol-contract.test.ts` 的 `ALL_MESSAGE_TYPES` 与计数断言 MUST 由 54 改为 55。

#### Scenario: 两份 protocol.ts 不漂移
- **WHEN** 新增 `interaction.comment` 后运行 `npm run typecheck` 与 `npm run test:acceptance`
- **THEN** `Record<MessageType,true>` 穷举与 `AC-PROTO-*`（计数 55）MUST 全过；任一处（两份 protocol.ts / command-bridge / docs / 两份 contract test）漏改 MUST 使构建失败

#### Scenario: 红线反例——单边新增消息（禁止）
- **WHEN** 仅在 cloud 侧 protocol.ts 新增 `interaction.comment` 而未同步 edge 侧 / contract test 计数
- **THEN** MUST 视为违规、不予合入；协议三处 + 两份 contract test MUST 原子同步

### Requirement: 评论纳入风控闸与按账号配额、计数挂真实回执、终态单写

系统 SHALL 把 `comment` 纳入下发前风控闸与会话预算：`role-dispatcher` 的 `canInteract`、`freshBudget()`、`consumeBudget` 并集 MUST 加 `comment`，
下发前 MUST 过 `riskController.canDo('comment')`、被拒 MUST 诚实跳过（不下发、不扣预算、不伪造）。`comment` 计数 / 持久化 MUST 只在执行端真回执 `ok:true` 时经 `interaction.occurred → RiskController.record('comment')` 发生（`handler.ts` 过滤与事件类型加 `comment`）。
账号风控终态 MUST 仅由云端 `RiskController` 单写；边缘与各评论角色 MUST 只读 `canDo`、MUST NOT 写终态。

#### Scenario: 被风控拒则诚实跳过
- **WHEN** 下发评论前 `riskController.canDo('comment')` 返回 false（配额尽 / `restricted` / `warned` / `frozen`）
- **THEN** MUST 不下发评论命令、不扣预算、emit `comment.skipped{reason}`，MUST NOT 伪造已评

#### Scenario: 仅真回执成功才计数
- **WHEN** 评论命令回执 `ok:true`
- **THEN** MUST emit `interaction.occurred` 使 `RiskController.record('comment')` 按账号计数并持久化；回执 `ok:false` MUST NOT 计数、MUST NOT 扣预算

#### Scenario: 红线反例——下发即记账或边缘改写终态（禁止）
- **WHEN** 有实现在下发评论时就 `record('comment')` / 扣预算，或在边缘改写账号风控终态
- **THEN** MUST 视为违规、不予合入；计数 MUST 挂真回执、终态 MUST 仅云端 `RiskController` 单写

### Requirement: Facebook automatic comment path must not weaken xhs human approval

Facebook scheduled comments SHALL use a separate platform-specific automatic path gated by deterministic validators and kill switches. Existing xhs comment interaction and manual approval requirements MUST remain intact; changes to shared composer helpers MUST preserve xhs `CommentApprovalGate` behavior and MUST NOT make xhs comments auto-post without approval.

#### Scenario: xhs approval still required
- **WHEN** xhs comment interaction produces a draft after this change
- **THEN** it still waits for the existing human approval gate before edge submit, unless an existing explicit manual path already defines otherwise

#### Scenario: Facebook validator path does not enter xhs manual skip set
- **WHEN** Facebook scheduled comment code runs
- **THEN** it uses its own automatic account tracking and does not add Facebook accounts to xhs manual-comment skip-quota collections

### Requirement: Shared compose extraction preserves approval semantics

If composition and cleanup logic is refactored into shared helpers, the helper SHALL be wrapped by separate xhs `withApproval` and Facebook `withValidators` callers. The helper itself MUST NOT decide that a comment can be posted.

#### Scenario: Helper returns draft only
- **WHEN** shared composition logic succeeds
- **THEN** it returns candidate text to the caller; xhs approval or Facebook validators still determine whether submit is allowed

### Requirement: Facebook comments require human review by default

All Facebook comments — whether or not they carry contact info — SHALL pass the Feishu human-review gate before edge submit when `AIDCP_FB_COMMENT_REVIEW_ALL` is not the literal string `false` (default ON). The gate MUST fail closed: an unwired approval port, a review timeout, or a rejection MUST result in an honest non-submitting outcome (`compose_skipped` / `approval_rejected_or_timeout`) with no edge submit and no dedup mark. Contact comments keep their existing always-reviewed behavior and keep showing the contact line on the card; non-contact comments show only the comment body with no phantom trailing line.

#### Scenario: Non-contact FB comment waits for review by default
- **WHEN** a Facebook non-contact comment is composed and passes deterministic validation with `AIDCP_FB_COMMENT_REVIEW_ALL` unset
- **THEN** it MUST request Feishu approval and MUST NOT submit until approved

#### Scenario: Review rejected or unwired → honest no-submit
- **WHEN** the approval port is unwired, times out, or returns rejected for a Facebook comment
- **THEN** the run MUST audit `compose_skipped` with reason `approval_rejected_or_timeout` (or the unwired equivalent), MUST NOT call edge submit, and MUST NOT record the target as commented

#### Scenario: Reversible escape hatch restores auto-publish
- **WHEN** `AIDCP_FB_COMMENT_REVIEW_ALL=false`
- **THEN** a non-contact Facebook comment MAY submit directly after validation (today's behavior); contact comments still require review

#### Scenario: Shadow never reviews or submits
- **WHEN** Facebook comment shadow/dry-run mode is active
- **THEN** the run MUST short-circuit to the shadow outcome before requesting any human review and MUST NOT submit

#### Scenario: manualOverride bypasses quota but never review
- **WHEN** a Feishu `/comment` run sets `manualOverride` (operator authority) with review enabled
- **THEN** it MAY skip quota/risk/daily-cap gates but MUST still require Feishu review before submit — the human review is not bypassable by operator override

#### Scenario: Red-line reversal — non-contact FB comment auto-posts under default (forbidden)
- **WHEN** an implementation submits a non-contact Facebook comment without review while `AIDCP_FB_COMMENT_REVIEW_ALL` is unset
- **THEN** it MUST be treated as a violation and not merged

### Requirement: 评论链人设注入对齐互动评估样板

评论支线的判定与产文角色（`CommentAppraiser` / `CommentComposer` / `CommentDeAiFlavor` 的两条改写路径）SHALL 注入账号人设的**性格字段**（`background` / `tone`，判定角色另注入 `like_principle` 类互动原则；对齐互动评估角色的注入水平），使不同人设账号在「是否开口」「怎么说话」上产生可区分差异；判定角色 SHALL 注入 `behavior_guidelines.style`（浏览风格）作为行为倾向背景。撞车改写路径（与参考语料雷同触发的重写）MUST 与主改写路径同源使用人设口吻行，MUST NOT 以无人设的通用口吻改写。无人设账号仍按 `mandatory-account-persona` 既有闸诚实拒绝，本要求不改变该行为。

#### Scenario: 判定与撰写 prompt 含性格字段

- **WHEN** 构造 `CommentAppraiser` / `CommentComposer` 的 prompt
- **THEN** prompt 含该账号 `background` / `tone`（判定另含互动原则与浏览风格），MUST NOT 仅注入「名字 + 职业 + 兴趣清单」

#### Scenario: 撞车改写带人设口吻

- **WHEN** 评论草稿与参考语料近似撞车、触发重写
- **THEN** 重写 prompt 含该账号人设口吻行（与主改写路径同源），产出保留该账号个人腔，MUST NOT 收敛为通用中庸腔

### Requirement: 撰写语境穿透与言语行为多样化

系统 SHALL 让评论撰写基于「刚发生的真实体验」而非孤立正文：`CommentAppraiser` 判定「值得评」的理由 SHALL 经 `comment.appraised` payload（可选字段）穿透到撰写 prompt；撰写 prompt SHALL 注入本次互动类型（like / collect）与作者名；会话内已采集到该笔记当页评论时 SHALL 注入头部摘要（限幅 3-5 条）以贴合现场话题、避免重复他人已说，未采集到时 MUST 诚实不注入、MUST NOT 为此改动事件时序或新增边缘采集。撰写的**切入角** SHALL 为可选面板（共鸣 / 真问题 / 自己的相关经历 / 纯情绪短评等）由人设与内容选择，MUST NOT 钉死单一「共鸣或提问」两模式；长度约束 SHALL 表述为「一般一两句，可以更短、更随口」（保留平台上限硬闸），MUST NOT 诱导恒定长度。

#### Scenario: 判定理由穿透进撰写

- **WHEN** `CommentAppraiser` 产出「值得评」判定且 payload 携带 reason
- **THEN** 撰写 prompt 含「你刚才觉得这篇值得评，因为…」语境；payload 无 reason 时省略该片段（可选字段向后兼容）

#### Scenario: 当页评论缺失不编造

- **WHEN** 会话内未采集到该笔记的当页评论
- **THEN** 撰写 prompt 省略现场评论片段，MUST NOT 编造「大家在聊…」占位语境

#### Scenario: 切入角与长度不钉死

- **WHEN** 同一账号在多篇不同笔记下撰写评论
- **THEN** 切入角随人设与内容在面板内变化、长度自然波动，MUST NOT 每条都呈「一句共鸣 / 一个提问 + 近似等长」的模板签名

### Requirement: 去 AI 味信号集覆盖评论体裁

`CommentDeAiFlavor` 的 AI 味检测 SHALL 使用**评论体裁专用信号集**（客套模板句如「感谢分享」「学到了」单句成评、空洞附和、和稀泥句式等，人工校准维护），命中 **1 条**即触发人设口吻改写；MUST NOT 仅复用发帖侧长文议论文连接词词表与其阈值（该词表对评论体裁近零召回、致改写路径长期空转）。改写指令 SHALL 允许「可以更短、更随口」，MUST NOT 强制等长。发帖侧既有词表与阈值不受本要求影响。

#### Scenario: 客套模板评论被检出并改写

- **WHEN** 评论草稿为「感谢分享，学到了！」类客套模板句（不含议论文连接词）
- **THEN** 评论体裁信号集命中、触发按账号人设口吻的改写；改写后保持贴题、允许比原文更短

#### Scenario: 发帖侧不受影响

- **WHEN** 发布正文走发帖侧去 AI 味
- **THEN** 发帖侧词表、阈值与行为与本 change 之前一致

