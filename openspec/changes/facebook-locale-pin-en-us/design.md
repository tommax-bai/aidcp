## Context

FB 页面自动化的按钮 / 状态识别本质是「按可见文字关键词匹配」。已坐实的语言脆弱点（file:line 对 edge master 核实）：

- `src/facebook/join-executor.ts:157-186` 三张多语关键词表（JOIN/MEMBER/PENDING）+ `QUESTIONNAIRE_PHRASES`，`contains` 匹配、覆盖不对称（JOIN ~14 语、MEMBER ~8 语），漏语种即 `mainCtaText=null` fail-closed 跳过、或「加成功但没认出→重复加群」。
- `src/facebook/consent.ts:100/112/113` COOKIE_COPY / ACCEPT_ALL / NECESSARY 近纯中英正则，非中英 cookie 横幅不被点、遮挡整页。
- `src/facebook/comment-executor.ts:516` 评论框标签闸中英正则；`src/facebook/identity.ts:93/102` 头像 aria 后缀正则。
- 已有语言无关信号仅零星：URL path 正则（`/login`、`/groups/`）、ARIA role 作用域排除。

界面语言当前是个**不受控变量**：`src/electron/ads-fingerprint.cjs:145` `language_switch:'1'`（语言随代理 IP），无显式 `language` 字段。FB 界面 chrome 语言由账号自身语言设置决定、与内容 / 群组语言无关——本 change 把它在源头钉成英文，是整套跨语言识别分层方案的 P0（C1）。后续 C2（加群动作解耦 + 结构后置校验）、C3（同意浮层结构化）另立 change 修「即便全英文也会坏」的语言无关 bug。

约束（架构铁律）：edge-only、无协议改动（不碰协议四处同步 / 热点 `protocol.ts` / `command-bridge` / 角色注册 / 风控状态机）；不违背「不静默假成功」；不破坏指纹一致性与一 profile 一指纹一 IP 一账号绑定。

## Goals / Non-Goals

**Goals:**
- 新号建号时把界面 chrome 语言钉成规范 `en-US`（指纹语言 + 启动参数 + 导入 cookie 三处一致）。
- 明确存量登录号的唯一有效归一路径（账号服务端语言翻转），并把「写客户端改不动存量号指纹语言」坐实为结构性边界。
- 把大部分按钮 / 状态识别从「N 语」塌成「单语英文」，同时**内容语言完全不动**。

**Non-Goals:**
- 不建 / 不扩 N 语关键词字典（YAGNI）；本 change necessary-not-sufficient。
- 不修「即便全英文也会坏」的语言无关 bug（加群点击靠文字二次选按钮、成败靠文字自证、评论框越界）——归 C2/C3。
- 不改协议、不改 cloud、不改风控 / 角色。
- 不给按钮上视觉识别。
- 不强制存量熟号立即翻转（可维持现语言，pin 优先铺新号）。

## Decisions

### D1：新号指纹语言钉死 en-US，而非随代理 IP
`ads-fingerprint.cjs` 的 `buildFingerprintConfig` 里 `language_switch:'1'`（随 IP）改为关闭 + 显式 `language=['en-US']`。
- **为什么**：语言随 IP 反而制造「美国代理号突现越南语 UI」的不自洽；钉死英文让下游识别单语化。`language` 不在 `assertOsCoherent`（`ads-fingerprint.cjs:107-130`，只断言 OS 一致）里，pin 不触发 coherence 拒建。
- **待验**：`language_switch` 的 0/1 语义与 `language` 字段确切键名需 `scripts/adspower-fingerprint-probe.ts` 真机核实，**不凭记忆写**；实装先加护栏可读的中心常量，真机确认键名后再定值。
- **备选（否决）**：只靠启动参数 `--lang` / cookie `locale`——它们只兜登出 chrome，改不了 AdsPower 指纹层与登录态群面，不足以治本。

### D2：启动参数 `--lang=en-US` 兜登出 / 未登录 chrome
`browser-provider.ts:133` 的 `launchArgs`（现 `['--window-size=1440,980','--deny-permission-prompts']`）追加 `--lang=en-US`。
- **为什么**：登出页 / 首次未登录态的浏览器 chrome 由启动参数主导；登录态群面由账号语言主导，此参数只补边角。定位为 belt-not-authority。

### D3：导入号 cookie 确保含 `locale=en_US`
`facebook-account-import.cjs`（`FB_COOKIE_NAMES` 已含 `locale`，:14）在归一化导入 cookie 时，若缺 `locale` 则注入 `locale=en_US`。
- **为什么**：统一导入号初始会话界面语言。同为 belt——FB 账号服务端语言最终权威，会在登录后覆盖；此项只保证首屏与登录前一致。

### D4：存量登录号走账号服务端语言翻转，写客户端不放宽
`ads-write-api.cjs:23` `WRITE_ALLOWLIST` 含 `user/update` 但仅经 `updateProfileProxy` 两键代理 body（:175-180）、`fingerprint_config` 只在 `user/create` 设（:143）→ 存量号指纹语言结构性改不动。
- **决定**：**不放宽写客户端**去改指纹语言（放宽会撞 `adspower-environment-provisioning` 的 update-仅两键红线）。存量号唯一路 = 一次性登入把 FB 账号语言改英文。以运维 runbook 落地 + 可选边缘自动化（导航设置页改语言），标记真机验证门。
- **备选（否决）**：放宽 `user/update` 透传 fingerprint——违反既有 spec 结构性边界，否决。

### D5：内容语言绝不塌
只统一界面 chrome；帖文 / 群名 / 评论 / 人名等内容层不碰，仍归云端多语判定（评论生成已天然多语）。

## Risks / Trade-offs

- [pin en-US 被 FB 当异常 / 与「看起来像本地用户」冲突] → 缓解：英文界面刷本地语言群是常见真实形态；`language` 不进一致性断言；现「语言随 IP」更异常。默认铺新号；熟号可维持现语言。
- [FB 界面语言未必只由账号设置决定、内容可能随之变] → 缓解：propose 阶段列为真机待验第一项，验证前不把「内容不塌」当已证；码级改动本身可回滚（旗标 / 常量）。
- [`language_switch` 语义 / `language` 键名凭记忆写错] → 缓解：先跑 `scripts/adspower-fingerprint-probe.ts` 核实再定值；实装留常量单点。
- [存量号翻转设置页路径未知 / 跨版本漂] → 缓解：先 runbook 手动、自动化标真机门，不阻塞新号路径先发。
- [pin 只治「界面语言随内容变」，治不了语言无关 bug] → 明示 necessary-not-sufficient，C2/C3 接力；本 change 不夸大收益。
- [启动参数 / cookie 被误当能改登录态群面] → 文档写死其只兜登出 chrome，避免误判「pin 了但群面还是外语」为回归。

## Migration Plan

1. edge 本地改 `ads-fingerprint.cjs`（language 常量单点）+ `browser-provider.ts`（`--lang`）+ `facebook-account-import.cjs`（locale 注入），加单测。
2. `npm run typecheck` + `npm test`（edge），确认无回归。
3. 真机：`scripts/adspower-fingerprint-probe.ts` 核 `language_switch`/`language` 键值语义；建一个新号验界面英文 + 内容不塌。
4. 部署 dev（edge 侧），运营机重建 / pull 后新号生效。
5. 存量号：先 runbook 手动翻转一批验证，再评估边缘自动化。
6. 回滚：语言常量 / `--lang` / cookie 注入均为局部可逆改动，秒级回退到「随 IP」。

## Open Questions

- `language_switch:'0'` 是否等于「不随 IP、用显式 language」？`language` 是否即 AdsPower 期望键名（vs `languages`/其它）？→ 真机 probe 定。
- 是否给「新号是否 pin」加 env 旗标（便于灰度 / 回退），还是直接改默认？→ 倾向直接改默认（现随 IP 本就是缺陷），但保留常量单点便于回滚。
- 存量号翻转是否值得做边缘自动化，还是长期 runbook？→ 视存量号规模与翻转设置页稳定性，真机后定。
