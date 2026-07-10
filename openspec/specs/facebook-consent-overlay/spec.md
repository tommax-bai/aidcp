# facebook-consent-overlay Specification

## Purpose
TBD - created by archiving change facebook-consent-overlay-auto-accept. Update Purpose after archive.
## Requirements
### Requirement: Facebook 同意浮层的独立识别

系统 SHALL 通过一个**专门的同意浮层判定**（独立于 captcha/login/unknown/none 四类浮层分类器）将 Facebook 页面内 cookie 同意浮层识别为一个独立处置类别 `consent`。识别 MUST 只依据**稳定的人类可读语义锚点**——cookie 政策语义文案 + 「允许所有 Cookie / Allow all cookies / 仅允许必要 Cookie / Only allow essential cookies」等接受/拒绝按钮的可见文案或 aria-label，MUST NOT 依赖 Facebook 的哈希 / 混淆 class 名。判定 SHALL 是本地确定性 DOM 判定，MUST NOT 依赖云端 LLM。

#### Scenario: cookie 同意浮层判为 consent
- **WHEN** 页面存在 cookie 政策语义文案与「允许所有 Cookie」类接受按钮，且当前 URL 不是登录 / 验证门
- **THEN** 同意浮层判定结果为「存在同意条」（present），进入自动接受流程

#### Scenario: 无同意浮层时不误报
- **WHEN** 页面无 cookie 同意浮层（无接受按钮或无 cookie 政策文案）
- **THEN** 判定结果为「不存在同意条」，调用方照常继续（不触发自动接受）

### Requirement: 判定优先级保证真门与验证码优先

同意浮层判定 SHALL 让验证码 / 登录门优先：当前 URL 命中登录 / 恢复 / 验证路径（`/login`、`/checkpoint`、`/recover`、`/two_step_verification`）或页面具备验证码 / 风控挑战特征时，MUST NOT 判为同意条。同意浮层正文中出现的「登录 Facebook」等字样 MUST NOT 导致自动接受被误用于真登录门——真登录门（无 cookie 接受按钮）与验证码 MUST 保持既有 fail-closed 处置。

#### Scenario: 含「登录 Facebook」字样的同意浮层不被当作登录门
- **WHEN** cookie 同意浮层正文包含「…应用到你登录 Facebook 的任何地方」这类字样，但当前 URL 非登录/验证门、且存在「允许所有 Cookie」接受按钮
- **THEN** 判为同意条并自动接受，MUST NOT 当作 login 门中止动作

#### Scenario: 真登录 / 验证 URL 永不判为同意条
- **WHEN** 当前 URL 命中 `/login` 或 `/checkpoint`（即使正文含 cookie 文案）
- **THEN** 判定「不存在同意条」，交既有登录 / 验证处置

#### Scenario: 验证码优先于同意
- **WHEN** 页面同时具备验证码特征与 cookie 同意特征
- **THEN** 判定「不存在同意条」，交既有验证码 fail-closed / 远程协助路径

### Requirement: 边缘本地拟人自动接受同意浮层

在 Facebook 评论 / 加群等动作提交前的浮层复检卡点，若判为同意条，系统 SHALL 在**边缘本地**自动接受：以拟人方式（复用既有拟人点击基建，含移动轨迹 / 落点抖动 / 偶发 overshoot）点击接受按钮。默认点击「允许所有 Cookie」（accept-all）；系统 SHALL 提供配置开关（env `AIDCP_FB_COOKIE_CONSENT`）切换为「仅必要 Cookie」（necessary-only）。此动作 MUST NOT 依赖云端下发命令、MUST NOT 新增边云协议消息类型、MUST NOT 引入云端角色。

#### Scenario: 判为同意条时自动接受并放行动作
- **WHEN** Facebook 动作提交前判为同意条，默认策略 accept-all，且点击后横幅消失
- **THEN** 边缘拟人点击「允许所有 Cookie」按钮，随后继续原动作前的流程

#### Scenario: 配置为仅必要时点必要按钮
- **WHEN** `AIDCP_FB_COOKIE_CONSENT=necessary_only` 且判为同意条
- **THEN** 边缘拟人点击「仅允许必要 Cookie」按钮

### Requirement: 只清同意浮层，绝不误点真门 / 验证码

自动接受 SHALL 只对被判为同意条的浮层触发。系统 MUST NOT 以「关闭任意模态 / 点击任意主按钮」的方式清理浮层。对 `captcha`、真登录门、`unknown` 等阻断浮层，MUST 保持既有 fail-closed 行为（中止动作 / 暂停 / 升级 / 交既有验证码远程协助），MUST NOT 自动点击。当策略所需的接受按钮未能定位时，MUST NOT 改点另一个按钮。

#### Scenario: 验证码浮层不被自动点击
- **WHEN** 浮层复检判为 `captcha`
- **THEN** 系统不执行同意自动接受，保持既有 `blocked_by_captcha` / 远程协助路径

#### Scenario: 策略所需按钮缺失时不乱点
- **WHEN** 判为同意条但策略所需接受按钮未能定位（文案 / 布局漂移）
- **THEN** 系统不点击任何其他按钮，如实回报失败（见诚实回执要求），MUST NOT 改点非策略按钮

### Requirement: 点击后后置校验与诚实回执

自动接受后，系统 SHALL 复探确认同意浮层已消失方可判定接受成功。若接受后浮层仍在，或接受按钮未能定位，系统 MUST 如实回报（`no_target` / `blocked_by_consent` 等命名原因），MUST NOT 静默假成功、MUST NOT 在浮层仍阻断时继续原动作并谎报成功。

#### Scenario: 接受成功需浮层确已消失
- **WHEN** 点击接受按钮后复探仍检出同意条
- **THEN** 不判成功，进入有界重试或如实回报失败，不继续原动作

#### Scenario: 接受失败诚实回报
- **WHEN** 同意浮层无法被清理（重试到上限仍在，或按钮定位失败）
- **THEN** 系统回报 `blocked_by_consent` / `no_target` 等诚实原因，不谎报 `ok`

### Requirement: 有界重试与升级

自动接受 SHALL 有明确的重试次数上限，MUST NOT 无界空转点击。连续尝试到上限仍无法清理同意浮层时，系统 MUST 停手并以诚实回执升级，交由上层 / 运营处理。

#### Scenario: 到重试上限停手升级
- **WHEN** 自动接受连续尝试达到配置上限仍未清除同意浮层
- **THEN** 系统停止继续点击，回报诚实失败原因（`blocked_by_consent`），不继续原动作

