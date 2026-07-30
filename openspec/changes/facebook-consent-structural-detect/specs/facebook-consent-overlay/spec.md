## MODIFIED Requirements

### Requirement: Facebook 同意浮层的独立识别

系统 SHALL 通过一个**专门的同意浮层判定**（独立于 captcha/login/unknown/none 四类浮层分类器）将 Facebook 页面内 cookie 同意浮层识别为一个独立处置类别 `consent`。判定 SHALL 是本地确定性 DOM 判定，MUST NOT 依赖 Facebook 的哈希 / 混淆 class 名，MUST NOT 依赖云端 LLM。

**核心不变量（评审坐实、绝不放松）：自动点击只点「正向识别为接受/拒绝的同意动作」，识别不出即诚实 `no_target`、绝不盲点任何未识别按钮。** cookie 文案只是「存在性」信号、**不是**「这是同意条」的充分判别器——带 cookie 细则的登录 / 注册 / 「继续」墙（正文常含「继续即表示你同意 Facebook 使用 Cookie」且出现在 `/groups/xxx` 等非 `/login` URL）绝不能因容器内含 cookie 子串就被结构点击其主按钮（那是真登录门）。

判定分三步：

- **同意容器隔离（present 门作用域）** SHALL 先定位一个**其自身文本携带 cookie 政策语义锚点的有界容器**（cookie 文案节点最近 `[role="dialog"]`/`[aria-modal="true"]` 祖先或紧致 fixed/overlay 容器）。全页 `document.body` 级 cookie 文案（页脚 Cookie Policy 链接、群简介）**不构成**同意容器。
- **语言无关的登录门负向护栏** SHALL 在容器 / 页面命中以下任一时**判非同意条、绝不自动点击**：存在凭据输入（`input[type="password"]` / `type="email"` / 登录表单等——凭据输入是登录 / 注册面的语言无关标志，同意条从不含）；或容器内存在命中 auth-CTA 词表（log in / sign up / continue / create account / 登录 / 注册 / 继续 等，覆盖运营语种）的按钮。这是对「登录墙含 cookie 细则」case 的防线。
- **只点正向识别的同意动作** SHALL 要求被点按钮是**正向识别的接受 / 拒绝动作**：① 其可见文案 / aria 命中既有 accept/decline 词表（**文字优先**，英中既有路径逐字零回归）；或 ② **仅当**容器另外命中一个**真机坐实的 FB 同意条结构标志**（consent-specific structural marker，落 backlog 真机取证）时，在该同意动作对内按结构角色（主=accept-all，次=necessary-only）消歧。**未取得真机坐实的结构标志前，结构兜底 MUST NOT 点击任何未被文案命中的按钮**——无正向识别即诚实 `no_target`（既有安全行为，非回归）。

本要求 MUST NOT 放松登录门 / 验证码优先：结构选取的前提永远是已通过 present 门（含 cookie 锚点、非登录 / 验证 URL、非验证码、且通过登录门负向护栏）。

#### Scenario: cookie 同意浮层判为 consent 并点正向识别的接受按钮
- **WHEN** 存在自身文本含 cookie 锚点的有界容器、无凭据输入、容器内无 auth-CTA 按钮、且有一个文案命中 accept/decline 词表的接受按钮，当前 URL 非登录 / 验证门、非验证码
- **THEN** 判为同意条，点该文案命中的接受按钮（文字优先）

#### Scenario: 登录 / 「继续」墙含 cookie 细则不被误点（红线）
- **WHEN** 页面在 `/groups/xxx`（非 `/login`）弹出登录 / 「继续」墙，其容器自身文本含 cookie 细则（「继续即表示你同意…Cookie」），主按钮是「登录 / 继续 / 注册」（不命中 accept/decline 词表），或页面含凭据输入
- **THEN** 登录门负向护栏命中（凭据输入 / auth-CTA 按钮）→ 判非同意条，MUST NOT 自动点击任何按钮

#### Scenario: 无正向识别的同意动作时不盲点
- **WHEN** 已隔离同意容器、无登录门负向信号，但容器内按钮文案均不命中 accept/decline 词表，且未取得真机坐实的 FB 同意条结构标志
- **THEN** 系统 MUST NOT 结构盲点任何按钮，诚实回报 `no_target`（既有安全行为）

#### Scenario: 文案命中时文字判据优先、英中零回归
- **WHEN** 已隔离同意容器、通过登录门护栏，且容器内某按钮文案正向命中 accept/decline 词表（英文 / 中文既有路径）
- **THEN** 系统按文案命中选按钮（文字优先于结构角色），行为与既有实现逐字一致

#### Scenario: 取得结构标志时在同意动作对内按结构消歧
- **WHEN** 已隔离同意容器、通过登录门护栏、容器另命中真机坐实的 FB 同意条结构标志，但两个接受 / 拒绝按钮文案是词表未覆盖语种
- **THEN** 系统在该同意动作对内按结构角色选主按钮作 accept-all（necessary-only 策略选次按钮）

#### Scenario: 无同意浮层时不误报
- **WHEN** 页面无 cookie 同意浮层（无 cookie 政策文案，或无任何按钮）
- **THEN** 判定「不存在同意条」，调用方照常继续（不触发自动接受）
