## Why

真机探针（2026-07-17，账号 Tianxing Bai / env `k1ei3dbi`）坐实：**被 Facebook 拒绝的评论，今天会被判成「发布成功」**。

现行 ack 判据是「服务器正式 comment id **或** 该评论行内 `role=button` 数 ≥ 2」。被拒评论行的真机形态是 `… 16小时 已拒绝 查看反馈`，恰好带 2 个按钮（「编辑或删除此项」+「查看反馈」）→ `reactions>=2` 为真 → 判成功。既有的待审徽章否决与参与审批闸对「已拒绝」**均不命中**（实测 `false`），其 href 里的 comment_id 是数字、非服务器 base64 格式（故 `hasServer=false`），**没有任何一道闸拦得住**。链路后果：边缘回 `ok` → 云端 `reallySubmitted` 为真 → 打去重标记（目标帖永久烧掉）→ 运营收到绿卡「已在群内发出一条评论（**服务器已确认**）」。用户确认「已拒绝是发布后就出现的」，落在确认窗内，不是延迟态。

这是「MUST NOT 静默假成功」红线的正面击穿，且是当前线上行为。`按钮数 ≥ 2` 从来只是「赞和回复出现了」的**代理指标**，真机证明该代理不成立——被拒行同样有 2 个按钮。

同一批探针还推翻了本 capability 的另一条要求：**刷新兜底腿是假阴性的产地**。探针报 `reloadPersisted:false` / `nodeFound:false`，而两条评论**实际都在**（CDP 复核 + 肉眼双证）——正是运营侧「提交后无法确认评论已上墙」黄卡的真实成因。且刷新腿的判据只要「本人 + 文本」、连按钮都不看，**对被拒评论必定假绿**；刷新还会刷掉押审徽章/弹窗证据（现有代码注释自己承认）。

## What Changes

- **BREAKING（spec 层）**：撤销「有界轮询 reload 是权威兜底」这条要求——真机证明 reload 制造假阴性、且其判据对被拒评论必定假绿。提交后确认改为**纯就地观察**，刷新腿删除，其原有时间预算还给就地窗。
- **BREAKING（spec 层）**：撤销「reaction/reply affordances present」可由**按钮计数**满足的判据。成功 SHALL 只由「服务器正式 comment id」或**具名的赞/回复控件**确认；裸计数不再是合法判据。
- 新增**「已拒绝」独立诚实终态**：识别行内「已拒绝 / 查看反馈」类标记 → 自成一档终态失败。MUST NOT 计成功、MUST NOT 打去重、MUST NOT 塌进 `verification_ambiguous`（那读作「可能已发出」）或 `pending_group_approval`（那是待批准、可等）。此态为**确定被拒**，目标帖应可留给人工处理。
- 新增**「发布中」在飞态**识别：给系统一个现在没有的分诊能力——把「压根没提交」与「提交了但没等到结果」分开，正是 `verification_ambiguous` 今天分不清的东西。在飞态 MUST NOT 被判成任何终态。
- **判据用文案，MUST NOT 用透明度/颜色**：真机实测被拒行与正常行 `opacity` 同为 1、`color` 同为 `rgb(28,30,33)`，**样式零差异**，样式路线结构上不成立。
- **不动任何超时常量**：服务器点头实测 2.8 秒（上轮 3.5 秒），现有就地窗约 10 秒已是 3.5 倍余量。删刷新腿（约 9 秒）后预算内部重分配，**总预算不变** → 云端提交步超时与边缘提交保护窗**均不改**。（反面：若把窗口放宽到 30 秒，短评论会超云端预算 → 云端记 timeout → 不打去重 → 下轮同帖真重发，正是长度感知超时当初要堵的洞。）

## Capabilities

### New Capabilities

（无。本 change 修正既有 capability 的要求，不引入新能力面。）

### Modified Capabilities

- `facebook-comment-verification`: 三条要求变更——①成功判据收窄为「服务器正式 id 或具名赞/回复控件」，撤销按钮计数；②撤销「reload 是权威兜底」，改纯就地观察；③新增「已拒绝」独立终态与「发布中」在飞态，并明确样式（透明度/颜色）不得作为判据。
- `facebook-comment-idempotency`: 窄修——其场景文案把云端步超时描述为覆盖「post-submit **reload**/verify window」，本 change 删除 reload 后该措辞失真。要求本身（长度感知超时防重复评论）不变，仅去除对已删机制的引用。

## Impact

- **受影响仓**：`aidcp-edge`（主体）+ `aidcp-cloud`（仅新增一档 outcome 映射与卡片文案，参照 `pending_group_approval` 既有形态）。
- **edge**：单文件 `src/facebook/comment-executor.ts` 的提交后确认段（`submitComment` / `inPlaceAckConfirm` / `reloadScopedConfirm` / `buildAckVerifyJs` / `buildScopedVerifyJs`）；新增「已拒绝」与「发布中」文案常量（中英覆盖 + 越南语扩展缝，车队实跑越南群）。
- **cloud**：`src/comment-agent/comment-scheduler.ts` 的 `mapFacebookSubmitOutcome` 加一档 + 结果卡文案；`facebook-comment-audit-store.ts` outcome 枚举。**不碰协议**（复用既有 `action.completed` 的 reason 字符串通道）、不碰 console。
- **部署**：edge 侧运营机需 pull + 重建安装包才生效；cloud 侧若加 outcome 映射需按默认序列部署 dev。
- **保留不变量**：`identity_unknown` 不提交；绝不 over-confirm（乐观渲染 / client 占位 id / 整页文本命中一律不算）；提交后**报错浮层**仍不得当失败（真机实证浮层会撒谎）——行内「已拒绝」与该浮层是**两个不同 DOM 物件**，MUST NOT 混为一谈。
- **真机验收（桩测盲区）**：页内 JS 对「发布中 / 已拒绝 / 赞·回复」的判别 FakeCdp 桩不了，须真机坐实并进 backlog。附带：探针补丁（每帧存 `nodeText` + 时间戳选择器回落到 `<a>`）须回写 `aidcp-edge/scripts/fb-comment-verify-probe.ts`——上轮已写「需再调」而未调，直接导致本次重新发现「发布中」。
