> **实装前以 proposal / design「2026-07-12 修订」块为准**：C3 首发定性为**安全加固、零新增语种覆盖**（结构标志未取得前）；现状错述已订正（未覆盖语种是 `handled=false` 静默继续、非 `no_target`；`COOKIE_COPY` 非跨语言稳定）；D4 分不清主次时诚实 `no_target` 不 best-guess。

## 1. aidcp-edge — 容器隔离 + 登录门负向护栏 + 只点正向识别

- [ ] 1.1 `src/facebook/consent.ts` `CONSENT_SCAN_JS`：**先隔离同意容器**——定位「自身文本含 cookie 锚点的有界容器」（cookie 文案节点最近 `[role="dialog"]`/`[aria-modal="true"]` 祖先或紧致 fixed/overlay 容器）；**cookie 锚点 + 按钮采集** container-scoped。**但 `captchaLike`（全页 body + 每 iframe src）与 `onLoginUrl`（URL）MUST 保持页/URL 级、不收窄进容器**（#6 红线：验证码渲染在容器外不能被漏看，否则 consent 会在验证码存在时误点）。全页级 cookie 文案不构成容器。
- [ ] 1.2 **登录门负向护栏（语言无关优先）**：容器/页面命中「凭据输入（`input[type=password]`/`type=email`/登录表单）」或「容器内 auth-CTA 按钮（登录/注册/继续，覆盖运营语种）」→ 判非同意条、绝不自动点。凭据输入是主防线（语言无关），auth-CTA 词表为补充。
- [ ] 1.3 `pickButton` **只点正向识别的同意动作**：容器内文案命中 accept/decline 词表 → 文字优先按文案选（英中零回归）；**无文案命中且未取得真机结构标志 → 诚实 `no_target`，绝不结构盲点未识别按钮**。necessary_only 结构分不清主/次时亦诚实 `no_target`（D4 订正，绝不 best-guess「取另一个」）。
- [ ] 1.4 结构消歧 D3-②（**门控**）：仅当容器另命中真机坐实的 FB 同意条结构标志时，才在同意动作对内按结构角色消歧未知语种按钮；标志未坐实前此路径不启用（默认 `no_target`）。
- [ ] 1.5 **只记账不动作（#21，L4 例外补偿）**：识别出的同意容器走 `no_target` 时，本地/审计记录容器内按钮候选（文案 + 结构线索，**零点击**），供 D3-② 结构标志 Open Question 日后真机取证；这是「边缘不 fail-closed 丢原文」在 consent 热路径蓄意例外下的最小补偿。

## 2. aidcp-edge — 测试

- [ ] 2.1 红线用例（复验揪出）：**登录/「继续」墙容器自身含 cookie 细则、主按钮「登录/继续」、URL=`/groups/xxx`（非 `/login`）→ 登录门负向护栏命中（凭据输入或 auth-CTA）→ 判 NOT-consent、不点任何按钮**。
- [ ] 2.2 红线用例：容器内按钮文案均不命中词表、无结构标志 → 诚实 `no_target`，**绝不结构盲点**任何按钮。
- [ ] 2.3 「文字优先」用例：容器内文案命中 accept/decline 词表时按文案选、与既有实现逐字一致（英中零回归断言）。
- [ ] 2.4 「凭据输入护栏语言无关」用例：容器含 `input[type=password]` → 判 NOT-consent（不依赖 auth-CTA 词表命中）。
- [ ] 2.5 （门控）结构消歧用例：桩「命中结构标志 + 未知语种按钮对」→ 按结构角色选主/次；无标志时同输入 → `no_target`。
- [ ] 2.6 回归保留：登录门/验证码优先、后置校验横幅消失才成功、有界重试诚实 `blocked_by_consent`。**验证码在容器外用例（#6）**：把 captcha 信号（iframe/body 文本）置于隔离同意容器**之外** → 断言 `present=false`（consent 让位、绝不点）。
- [ ] 2.7 只记账不动作用例（#21）：识别出同意容器但无正向识别按钮 → `no_target` + 审计记录候选、**断言零点击**。
- [ ] 2.8 D4 用例：已确认同意条内结构分不清主/次 → necessary_only 诚实 `no_target`（绝不 best-guess 点另一个）。
- [ ] 2.9 `npm test` + `npm run typecheck` 全绿。

## 3. 集成与部署

- [ ] 3.1 edge master land（edge-only，无协议/无云端），干净 worktree 确认。
- [ ] 3.2 dev 生效路径：electron:dev / 安装包重建后运营机 pull master（无 ECS）。
- [ ] 3.3 真机验收项登记 backlog（同意容器边界真机取证定档；**FB 同意条结构标志取证——启用 D3-② 前 MUST 通过负向验收「不与 Continue-墙家族匹配」**；非英文同意条真机点通）——不阻塞码级。

## 4. 收尾

- [ ] 4.1 `openspec validate facebook-consent-structural-detect --strict` 通过。
- [ ] 4.2 tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注；archive。
