## Context

同意浮层自动接受已上线（`src/facebook/consent.ts`，change `facebook-consent-overlay-auto-accept`）。现状 `CONSENT_SCAN_JS` 在页面里用三条正则：`COOKIE_COPY`（present 门锚点）、`ACCEPT_ALL` / `NECESSARY`（按钮选取，逐语言短语）。`pickButton` 按策略取 `acceptAll` / `necessaryOnly` 坐标，缺则诚实 `no_target`。**2026-07-12 订正（#9，超越原「问题只在按钮选取」判断）**：`present` 门是 `hasCookiePolicyCopy && 至少一个按钮词表命中`——未覆盖语种下按钮正则全 miss → `present=false` → `acceptFacebookConsent` 返 `handled=false`、**静默继续**（非 `no_target`）；且 `COOKIE_COPY` 是 **zh/en 绑定短语正则、非裸 `/cookie/i`**，未覆盖语种连同意条都认不出。故覆盖缺口**从存在性判定就开始**、不止于按钮选取；只改按钮选取扩不了覆盖。C3 首发交付因此定性为**安全加固**（容器隔离 + 登录门护栏），语种覆盖 deferred 在 D3-② 结构标志门后。

这是跨语言识别分层方案 C3，与 C1（[[facebook-locale-pin-en-us]] 界面钉英文）互补：C1 治新号首屏英文，C3 治登出态 / 存量号 / 非英文残留同意条这条语言无关缝。与 C2（加群结构校验）正交，edge-only 可并行。

## Goals / Non-Goals

**Goals:**
- **安全优先**：无论何语种，绝不误点真登录 / 「继续」门（复验坐实的核心红线）。
- **对既有同意路径安全加固**（容器隔离 + 登录门负向护栏 + 文字优先），在**能正向识别为同意条**的前提下运作；**语种覆盖扩展 deferred 在 D3-② 真机结构标志门后**（结构标志坐实前零新增语种覆盖，只加固安全）。
- present 门、登录/验证码优先、后置校验、有界重试、诚实回执**全部逐字保留**。
- 纯 edge-only、纯本地确定性 DOM 判定，零协议 / 零云端改动。

**Non-Goals:**
- 不建 N 语言接受按钮字典（YAGNI）；登录门负向护栏优先用语言无关的凭据输入信号。
- 不给按钮上视觉模型。
- **不结构盲点未正向识别的按钮**（复验证不安全）——未识别即 `no_target`。
- 不追求「任意未知语种同意条都能自动点」——安全优先于覆盖，该 case 退化为诚实 `no_target`，C1 已覆盖主群体。
- 不动同意策略语义（accept_all 默认 / necessary_only env 开关）。

## Decisions

**D0：核心不变量——只点正向识别的同意动作，识别不出即诚实 `no_target`（两轮评审坐实）。** 第二轮复验证明「结构盲点未识别按钮」本质不安全：cookie 子串只是存在性、非「这是同意条」判别器；带 cookie 细则的登录/「继续」墙（`/groups/xxx` 非 `/login`）会通过容器门、其登录按钮不命中 accept/decline 词表 → 结构兜底点主按钮 = 点真登录门。且「候选按钮」无法既纳入未知语言同意按钮又排除登录按钮。故整个 change 的地板是：**自动点击只点正向识别为接受/拒绝的按钮，无正向识别即 `no_target`、绝不盲点。**

**D1：present 门 = 同意容器隔离，仅作用域，不当充分判据。** `CONSENT_SCAN_JS` 先隔离「自身文本含 cookie 锚点的有界容器」（cookie 文案节点最近 `[role="dialog"]`/`[aria-modal="true"]` 祖先或紧致 fixed/overlay 容器），把 present 扫描与按钮判定框定在容器内。全页级 cookie 文案不构成容器。但「容器含 cookie 子串」**不足以**判定同意条（见 D0）——还须过登录门负向护栏（D2）+ 正向识别同意动作（D3）。

**D2：语言无关的登录门负向护栏（复验补的关键防线）。** 容器/页面命中任一即判非同意条、绝不自动点：① 存在**凭据输入**（`input[type=password]`/`type=email`/登录表单）——凭据输入是登录/注册面的**语言无关**标志，同意条从不含；② 容器内存在命中 **auth-CTA 词表**（log in/sign up/continue/create account/登录/注册/继续，覆盖运营语种）的按钮。凭据输入护栏语言无关、最硬；auth-CTA 词表是补充。备选（只靠容器 cookie 子串判同意）被否——正是复验揪出的登录门误点成因。

**D3：只点正向识别的同意动作；文字优先，结构消歧门控真机标志。** 被点按钮须是正向识别的接受/拒绝动作：① 文案命中既有 accept/decline 词表（**文字优先**，英中逐字零回归）；或 ② **仅当**容器另命中一个**真机坐实的 FB 同意条结构标志**时，在该同意动作对内按结构角色（主=accept-all/次=necessary-only）消歧。**取得真机结构标志前，结构兜底绝不点未被文案命中的按钮** → 无正向识别即 `no_target`。这样 unsure→decline，红线安全；结构消歧只服务「已正向确认是同意条 + 只是不知按钮词」的窄case。备选（无标志也结构盲点）被否——复验证不安全。

**D4：necessary_only 分不清主/次时诚实 `no_target`（2026-07-12 订正，#4）。** 原稿「necessary_only 取另一个」是 best-guess 点击、可能落在 accept-all 上，与 proposal 逐字保留的红线「策略所需按钮结构上定位不到时诚实 `no_target`、绝不改点别的」冲突。**订正**：已确认同意条内若结构分不清主/次，necessary_only **诚实降为 `no_target`**（绝不改点别的）；accept_all 若能正向识别主按钮则点、否则亦 `no_target`。保红线逐字不动，宁可 `no_target`（后续有界重试 / 诚实 `blocked_by_consent`）不 best-guess 误点。删除原「取另一个」退化。

## Risks / Trade-offs

- [登录/「继续」墙含 cookie 细则 → 误点真门（复验揪出的核心红线）] → **D2 登录门负向护栏 + D3 只点正向识别**双防线：凭据输入/auth-CTA 命中即判非同意条；无正向识别的按钮绝不盲点。unsure→decline。
- [C3 因此对「纯未知语种、无结构标志、无凭据输入」的同意条不自动点] → 接受：退化为诚实 `no_target`（既有安全行为、非回归），且 C1（新号界面钉英文）已覆盖主群体、残留非英同意条群体窄且随 C1 存量号归一收缩。安全优先于覆盖。
- [结构消歧误挑 necessary vs accept-all] → 只在已确认同意条内、后置校验认「横幅消失」，两者都清、动作放行；策略偏好退化不触红线。
- [`getComputedStyle`/结构线索缺失或隔离不出容器] → 回落纯文案路径（命中才点），再不行诚实 `no_target`，绝不盲点。

## Migration Plan

- 纯 edge，改 `consent.ts` + 单测；无 schema / 无协议 / 无云端。
- 部署：edge master land → dev（electron:dev / 安装包重建后运营机生效）；无 ECS。
- 回滚：结构选取是**叠加层**，回退即恢复「纯文案正则」老行为，秒级可回滚（保留文案路径就是天然回滚位）。

## Open Questions

- **FB 同意条结构标志（决定 D3 结构消歧能否开启）**：FB cookie 同意条是否有稳定、与登录墙可区分的结构标志（data-testid / 特定 dialog 结构 / 按钮排布）需真机取证。**取得前 D3-② 结构消歧不启用**——C3 先只落 D1 容器隔离 + D2 登录门护栏 + 文字优先，非英未知语种同意条退化为 `no_target`。落 backlog 真机项。**验收标准（复验补，红线关键）：该结构标志启用前 MUST 证其「不与 D2-可绕过的 Continue-墙家族匹配」**——即未覆盖语种的「继续/注册/一键登录」插页（带 cookie 细则、当前视图无凭据输入、Continue 不在 auth-CTA 词表）绝不能命中该标志；否则 D3-② 一开红线即重开。此负向验收是启用 D3-② 的前置条件、写进 backlog 真机项。
- **auth-CTA 词表覆盖**：登录门负向护栏的 auth-CTA 词表覆盖哪些运营语种需定档；凭据输入护栏语言无关、是主防线，auth-CTA 词表为补充（漏某语种 auth-CTA 时凭据输入/URL/验证码门仍兜底）。
- 同意容器边界（非 dialog 底部条的最稳祖先判据）真机校准——落 backlog。
