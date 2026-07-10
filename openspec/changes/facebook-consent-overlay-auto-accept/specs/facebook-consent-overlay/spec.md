## ADDED Requirements

### Requirement: Facebook 同意浮层识别为独立类别

边缘 Facebook 浮层分类器 SHALL 将 Facebook 页面内 cookie 同意浮层识别为一个独立类别 `consent`，区别于 `captcha` / `login` / `unknown` / `none`。识别 MUST 只依据**稳定的人类可读语义锚点**——cookie 政策标题文案与「允许所有 Cookie / Allow all cookies / 仅允许必要 Cookie / Only allow essential cookies / 允许使用 Cookie」等接受/拒绝按钮的可见文案或 aria-label，MUST NOT 依赖 Facebook 的哈希 / 混淆 class 名。

#### Scenario: cookie 同意浮层判为 consent
- **WHEN** 页面展示带 cookie 政策标题与「允许所有 Cookie」按钮的同意浮层，且当前 URL 不是登录 / 验证门
- **THEN** 分类器返回 `consent`

#### Scenario: 无同意浮层时不误报
- **WHEN** 页面无 cookie 同意浮层
- **THEN** 分类器不返回 `consent`（按其余规则返回 `none` 或对应阻断类别）

### Requirement: 判定优先级保证真门与验证码优先

分类 SHALL 按 `captcha` > 真登录门 > `consent` 的优先级判定。真登录门以 URL 命中 `/login`、`/checkpoint`、`/recover`（或等价登录/恢复路径）为准。同意浮层正文中出现的「登录 Facebook」等字样 MUST NOT 导致其被误判为 `login`；只有真正的登录 / 恢复门（命中登录 URL、且不具备 cookie 接受按钮特征）才判 `login`。验证码 / 风控挑战 MUST 始终优先于 `consent`。

#### Scenario: 含「登录 Facebook」字样的同意浮层不误判为 login
- **WHEN** cookie 同意浮层正文包含「…应用到你登录 Facebook 的任何地方」这类字样，但当前 URL 非登录/验证门、且存在「允许所有 Cookie」按钮
- **THEN** 分类器返回 `consent`，不返回 `login`

#### Scenario: 真登录门仍判 login
- **WHEN** 当前 URL 命中 `/login` 或 `/checkpoint`、且不具备 cookie 接受按钮特征
- **THEN** 分类器返回 `login`（或 `captcha`，若命中验证码特征），不返回 `consent`

#### Scenario: 验证码优先于同意
- **WHEN** 页面同时具备验证码特征与 cookie 同意特征
- **THEN** 分类器返回 `captcha`

### Requirement: 边缘本地拟人自动接受同意浮层

在 Facebook 评论 / 加群等动作提交前，若浮层探针判为 `consent`，系统 SHALL 在**边缘本地**自动接受同意浮层：以拟人方式（复用既有拟人点击基建，含移动轨迹 / 落点抖动 / 停留）点击接受按钮。默认点击「允许所有 Cookie」（accept-all）；系统 SHALL 提供配置开关切换为「仅必要 Cookie」（necessary-only）。此动作 MUST NOT 依赖云端下发命令、MUST NOT 引入云端 LLM 决策。

#### Scenario: 探针判 consent 时自动接受并放行动作
- **WHEN** Facebook 动作提交前探针判为 `consent`，且默认策略为 accept-all
- **THEN** 边缘拟人点击「允许所有 Cookie」按钮，随后继续原动作前的流程

#### Scenario: 配置为仅必要时点必要按钮
- **WHEN** 配置开关设为 necessary-only 且探针判为 `consent`
- **THEN** 边缘拟人点击「仅允许必要 Cookie」按钮

### Requirement: 只清同意浮层，绝不误点真门 / 验证码

自动接受 SHALL 只对被识别为 `consent` 的同意浮层触发。系统 MUST NOT 以「关闭任意模态 / 点击任意主按钮」的方式清理浮层。对 `captcha`、真登录门、`unknown` 等阻断浮层，MUST 保持既有 fail-closed 行为（中止动作 / 暂停 / 升级 / 交既有验证码远程协助），MUST NOT 自动点击。

#### Scenario: 验证码浮层不被自动点击
- **WHEN** 浮层探针判为 `captcha`
- **THEN** 系统不执行同意自动接受，保持既有 `blocked_by_captcha` / 远程协助路径

#### Scenario: 找不到接受按钮不乱点
- **WHEN** 探针判为 `consent` 但接受按钮未能定位（文案 / 布局漂移）
- **THEN** 系统不点击任何其他按钮，如实回报失败（见诚实回执要求）

### Requirement: 点击后后置校验与诚实回执

自动接受后，系统 SHALL 复探确认同意浮层已消失、页面可交互，方可判定接受成功。若接受后浮层仍在，或接受按钮未能定位，系统 MUST 如实回报（`no_target` 或 `blocked_by_consent` 等命名原因），MUST NOT 静默假成功、MUST NOT 在浮层仍阻断时继续原动作并谎报成功。

#### Scenario: 接受成功需浮层确已消失
- **WHEN** 点击接受按钮后复探仍检出 `consent` 浮层
- **THEN** 不判成功，进入有界重试或如实回报失败，不继续原动作

#### Scenario: 接受失败诚实回报
- **WHEN** 同意浮层无法被清理（重试到上限仍在，或按钮定位失败）
- **THEN** 系统回报 `blocked_by_consent` / `no_target` 等诚实原因，不谎报 `ok`

### Requirement: 有界重试与升级

自动接受 SHALL 有明确的重试次数上限，MUST NOT 无界空转点击。连续尝试到上限仍无法清理同意浮层时，系统 MUST 停手并以诚实回执升级，交由上层 / 运营处理。

#### Scenario: 到重试上限停手升级
- **WHEN** 自动接受连续尝试达到配置上限仍未清除同意浮层
- **THEN** 系统停止继续点击，回报诚实失败原因并升级，不继续原动作
