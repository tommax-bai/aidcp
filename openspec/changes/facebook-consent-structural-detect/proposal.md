## Why

Facebook 的 cookie 同意浮层自动接受（已上线，`src/facebook/consent.ts`）当前既靠一条 cookie 政策文案正则判「是不是同意条」，也靠一组**逐语言的按钮文案正则**（`ACCEPT_ALL` / `NECESSARY`，中英若干短语）来选「点哪个按钮」。按钮文案正则是典型的语言相关脆点：换到词表没覆盖的语种（越南语、西班牙语、印尼语…），后续加群/评论动作可能被残留同意条挡着。这是跨语言识别分层方案里 C3。

**2026-07-12 修订（订正立论、超越下方旧表述）**：一轮评审对本 change 提出 5 处必改，实装前以本块为准。

- **订正现状错述（承重）**：原稿称未覆盖语种下同意条「**认得出**但**点不动** → 诚实 `no_target`」——**不成立**。`present` 门要求 `hasCookiePolicyCopy && 至少一个按钮词表命中`（`consent.ts` `present` 判定），故未覆盖语种下两条按钮正则都 miss → `present=false` → `acceptFacebookConsent` 返回 `handled=false`、流程**当没有浮层一样静默继续**（不是 `no_target`）。且 `COOKIE_COPY` 是 **zh/en 绑定的短语正则、非裸 `/cookie/i`**，未覆盖语种连「是不是同意条」都认不出。故：**只改按钮选取扩不了任何覆盖**，覆盖缺口从存在性判定就开始。
- **据此定性（订正覆盖措辞，#5）**：结构标志未取得前，C3 **零新增语种覆盖**——它交付的是**对既有同意路径的安全加固**（容器隔离 + 登录门负向护栏），语种覆盖扩展**显式 deferred 在 D3-② 结构标志门后**。proposal 的 Why 与 Modified Capabilities 摘要按此口径，不再售卖「扩语种覆盖」。
- **容器 scoping 绝不收窄全页安全扫描（#6，红线）**：`captchaLike`（全页 body + 每个 iframe src）与 `onLoginUrl`（URL）保持**页/URL 级**，只有 cookie 锚点 + 按钮采集 container-scoped；否则验证码渲染在同意容器外会被漏看、consent 误在验证码存在时点击。
- **D4 necessary_only 不与红线冲突（#4）**：已确认同意条内结构分不清主次时，necessary_only **诚实降为 `no_target`**（保「策略所需按钮定位不到即 no_target、绝不改点别的」红线逐字不动），**删除**原 D4「取另一个」best-guess 点击。
- **L4 例外记账（#21）**：同意热路径是 L4「边缘不 fail-closed 丢原文」的**蓄意例外**（edge-only、无云端 LLM、未知语种退化 `no_target` 不上报候选）——因 consent 误点 = 红线（点登录/继续门）、且 consent 页无任何探针证据（登录态不复现）。C3 加**只记账不动作**任务：识别出的同意容器走 `no_target` 时，本地/审计**记录容器内按钮候选**（零点击），供 D3-② 结构标志 Open Question 日后取证。**两轮对抗评审后 C3 收敛为「安全优先」范围**：直接把按钮选取放宽到「结构盲点未知语种按钮」被证不安全（带 cookie 细则的登录/「继续」墙会被误点真门），故 C3 = 容器隔离 + **语言无关登录门负向护栏** + 文字优先 + **只点正向识别的同意动作**（结构消歧待真机坐实 FB 同意条结构标志再开）。这是 C1（界面钉英文）的补充——C1 治新号主群体，C3 交付的是**对既有同意路径的安全加固**（在**绝不误点真门**的前提下把「隔离登录门误点」这条既有风险收紧），**语种覆盖扩展 deferred 在 D3-② 结构标志门后**；未能正向识别的非英同意条退化为诚实 `no_target`（安全优先于覆盖）。

## What Changes

- **核心不变量（两轮评审坐实）：只点正向识别的同意动作，识别不出即诚实 `no_target`、绝不盲点。** cookie 子串只是「存在性」、非「这是同意条」判别器；带 cookie 细则的登录/「继续」墙会通过容器门，结构盲点其主按钮 = 点真登录门。故绝不结构盲点未被正向识别的按钮。
- **语言无关的登录门负向护栏**：容器/页面存在凭据输入（`input[type=password]`/`type=email`/登录表单——同意条从不含，语言无关最硬信号）或容器内有 auth-CTA 按钮（登录/注册/继续，覆盖运营语种）→ 判非同意条、绝不自动点。
- **同意容器隔离 + 文字优先**：present 先隔离「自身文本含 cookie 锚点的有界容器」（全页级 cookie 文案不构成容器）；容器内按钮文案命中 accept/decline 词表时**文字优先**（英中逐字零回归）。
- **结构消歧门控真机结构标志**：仅当容器另命中一个**真机坐实的 FB 同意条结构标志**时，才在同意动作对内按结构角色（主=accept-all/次=necessary-only）消歧未知语种按钮；**标志坐实前结构兜底不启用**——非英未知语种同意条退化为诚实 `no_target`（既有安全行为、非回归，C1 已覆盖主群体）。
- **红线全部保留、逐字不动**：登录门/验证码优先（`onLoginUrl` / `captchaLike` 命中一律 present=false）；点后复探确认横幅消失方判成功；有界重试到上限诚实 `blocked_by_consent` 升级；策略所需按钮结构上定位不到时诚实 `no_target`、绝不改点别的。
- edge-only：MUST NOT 新增边云协议消息、MUST NOT 依赖云端 LLM、MUST NOT 引入云端角色。与 C2（加群结构校验）正交，可并行。
- **不做（YAGNI）**：不建 N 语言按钮字典、不给按钮上视觉模型、不改 present 门去掉 cookie 文案锚点（去掉会让真登录门/无关模态有被误点主按钮的风险）。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `facebook-consent-overlay`: 同意路径**安全加固**（非语种覆盖扩展，2026-07-12 订正）——加**容器隔离**（cookie 锚点 + 按钮采集框定在有界同意容器内；`captchaLike`/`onLoginUrl` 保持页/URL 级不收窄）+ **语言无关登录门负向护栏**（凭据输入 / auth-CTA → 判非同意条）+ **只点正向识别的同意动作**（无文案命中且无真机结构标志即诚实 `no_target`、绝不盲点；necessary_only 分不清主次亦 `no_target`）+ **只记账不动作**（`no_target` 时记录容器候选供结构标志取证）。结构角色消歧（未知语种按钮）**门控**在真机坐实的 FB 同意条结构标志后启用；标志未取得前**零新增语种覆盖**。present 判定门、登录/验证码优先、后置校验、诚实回执、有界重试等红线不变。

## Impact

- 代码：edge `src/facebook/consent.ts`（`CONSENT_SCAN_JS` 采集按钮结构角色 + `pickButton` 结构优先、文案兜底），对应单测 `test/facebook/consent.test.ts`。
- 协议 / 云端：无。不新增消息类型、不动 `command-bridge`、不动云端角色。
- 部署：edge-only；dev 走 edge master land，无 ECS/cloud 部署；真机验收落 backlog 不阻塞码级。
- 依赖：无新增。
