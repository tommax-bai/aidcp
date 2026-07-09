## Context

建号自助人设 v1（change `edge-persona-keyword-generation`，已归档 + 上 dev）真机反馈 5 问题。根因坐实：#1 云端 `isPersonaBound` 从不下发边缘（`UiSnapshotPayload`/`WelcomePayload` 无 persona 字段）；#5 gate 正确 fail-closed 但引导差；#2/#3/#4 输入设计问题，其中 #4 的互动开关既迷惑又**无输出映射**（v1 不产 behavior_guidelines）。本变更做薄快修，不碰未验证的提质改动。

## Goals / Non-Goals

**Goals:**
- 已绑人设的账号连云后如实显示「已设置」并跳过向导（修 #1 真 bug）。
- gate 判据不变，但引导透明、分态（修 #5）。
- 垂类可自定义、兴趣可自由文本、删掉无效互动开关（修 #2/#3/#4）。
- 协议改动最小、安全（只加可选字段）。

**Non-Goals:**
- `behavior_guidelines` 生成、结构化多维 payload、一句话补充、草稿边缘编辑（后置/另议）。
- 放宽生成 gate、绕过握手（红线，MUST NOT）。
- 扩 soul 结构（加 comment_principle/follow_principle 等，碰热点类型）。
- 垂类→兴趣联动子标签词库（维护负担重、抛弃自定义垂类长尾，用自由文本替代）。

## Decisions

### D1：personaBound 搭 ui.snapshot 顺风车，不新开 persona.query（修 #1）
`ui.snapshot` 是 hello 注册后既有的 cloud→edge 主动推送，已携账号资料。加一个可选 `personaBound?: boolean` 最省：**不新增 MessageType**（穷举计数不变、AC-PROTO 仍 65、不碰 command-bridge/白名单），只需两份 `protocol.ts` 逐字加字段 + 两份 AC-PROTO 往返镜像 + `docs/protocol.md` 载荷表补字段（**§2 计数不变**）。备选 persona.query（边缘主动查）会新增消息类型、更重，否。

### D2：personaBound 只在 true 时下发（守全空不发包）
`ui-snapshot.ts` 有「全空不发包」守卫且 `payload.account` 只在有昵称时才置。若无条件塞 `personaBound=false` 会让每次 hello 都发包、且轻微违「宁缺毋假」。**决定**：仅在 `isPersonaBound=true` 时带该字段；边缘默认「未设置」，收到 true 才翻「已设置」。语义上「无字段 = 未知/未绑」，边缘本地默认已覆盖。

### D3：onboarding 三态 = personaBound × 连接态（修 #1 + #5）
边缘据 `personaBound`（来自 ui.snapshot）× `auth/cloud`（来自 status）渲染：已绑→已设置跳过；未绑+未连云→引导先启动登录；未绑+已连云→启用向导。**personaBound 只在连云后到达**——但连云前的正确引导本就是「请启动登录」，一旦连上快照即把徽标翻「已设置」，无矛盾。（防御：确保连云前的空闲态不把已知已绑账号误显示为「未设置」——边缘默认态即「未设置」，连云后由 true 翻正，可接受；不引入 last-known 缓存，YAGNI。）

### D4：gate 判据不动，只改可见性（修 #5）
`personaReady = auth==='logged in' && cloud==='connected'` 保持。红线：无 core=无 WS=无账号，放宽即静默假成功。改的是 `updatePersonaGate` 的 hint——分别判 `auth!=='logged in'`（提示扫码登录）与 `cloud!=='connected'`（提示等待连云），给指向「启动」的 CTA 文案。

### D5：兴趣 = 标签 + 自由文本混合；垂类枚举 + 自定义（修 #2/#3）
不做垂类→兴趣联动词库（只覆盖常见垂类、抛弃自定义垂类长尾、维护重）。改「少量高频标签快捷选 + 自由文本兜底长尾」：更具体的兴趣输入让生成器 prompt 展开出更有领域纵深、跨账号更不雷同的 seed_keywords（零维护）。垂类同理加「自定义」自由文本项。采集端把自由文本并入 `keywordSelections`。

### D6：删互动开关（修 #4）
v1 生成器只产 identity+interests、不产 behavior_guidelines，互动勾选对产物零影响。删掉这个「无输出映射」的迷惑维度。behavior_guidelines 生成后置——现有硬编码兜底是调优过的已知good，从粗糙选项派生可能更空泛 + 抬失败率（4 子字段须全出、缺一即 parse 失败）；「行为全坍缩」被夸大（appraiser prompt 仍带完整差异化 identity+interests）。

### D7：服务端轻量输入校验（随自由文本一起补）
自由文本引入弱注入面（CJK 语义注入白名单拦不住），但严重度低：accountId 取握手绑定值（非 payload 自报）、影响面仅用户自己的人设、产物经 `loadSoulFromValue` 结构复验。`handler.ts` 对 `keywordSelections` 补单项长度 + 条数上限（有界爆炸面），超限诚实拒绝。

## Risks / Trade-offs

- **[personaBound 只在连云后到达]** 连云前徽标显示「未设置」（本地默认）。→ Mitigation：连云前引导本就是「请启动登录」；连上即翻正。不引入 last-known 缓存（YAGNI）。
- **[自由文本注入面]** → Mitigation：D7 长度/条数上限 + accountId 握手绑定 + 产物结构复验；语义注入影响面仅自己人设，低严重度、可接受。
- **[两份 protocol.ts 热点]** → Mitigation：只加一个可选字段、不新增消息类型；动前 fetch 确认无并发协议 change；单写者串行。
- **[edge renderer 与活跃 change edge-multi-environment-fleet 同区]** → Mitigation：改动集中在 persona-config section；集成前 rebase 核对、按 §7 解冲突。

## Migration Plan

- 协议为新增可选字段、非破坏：先 cloud 部署（旧 edge 忽略新字段），再发 edge 安装包。
- 回滚：edge 回退即忽略 personaBound、按本地默认渲染；cloud 新字段无人读时闲置。

## Open Questions

- 高频兴趣标签保留哪几个（做快捷选）、自由文本占位提示文案。
- 垂类「自定义」的输入校验上限具体值（长度/条数）。
