## ADDED Requirements

### Requirement: Ads CLI 运行时模板按内容身份刷新

Edge MUST 为完成全部兼容补丁后的 Ads CLI 运行时模板生成稳定内容身份，并把该身份纳入用户目录暂存判定。模板内容身份变化时，即使 Edge 应用版本与 Ads CLI 包版本未变，Edge 也 MUST 刷新用户目录副本；开发态 MUST 以当前 `build/ads-runtime` 模板为准，MUST NOT 让历史用户目录副本遮蔽当前兼容补丁。若旧 daemon 正从待替换副本运行，Edge MUST 先有界停止它再交换目录；停止、复制或交换失败 MUST 诚实阻断启动，MUST NOT 继续接管身份不符的旧运行时。

#### Scenario: 同版本兼容补丁变化触发刷新

- **WHEN** Edge 应用版本和 Ads CLI 包版本未变，但随包运行时模板的内容身份发生变化
- **THEN** Edge 刷新用户目录运行时副本并从新模板启动，MUST NOT 因旧二元版本 stamp 相同而继续运行旧 hook

#### Scenario: 开发态当前模板优先于历史副本

- **WHEN** 开发态 `build/ads-runtime` 与用户目录中的历史运行时副本内容身份不同
- **THEN** Edge 以当前 build 模板刷新用户目录副本，随后运行当前兼容补丁

#### Scenario: 旧 daemon 阻碍刷新时诚实失败

- **WHEN** 内容身份变化且旧 Ads CLI daemon 无法有界停止或运行时目录无法安全交换
- **THEN** Edge 明确报告运行时暂存失败并阻断环境核心启动，MUST NOT 静默复用旧模板

### Requirement: Ads CLI daemon 生命周期归属 Edge 真正退出

Edge 在本次进程中启动或接管 Ads CLI daemon 后，MUST 记录其管理会话。Edge 真正退出时 MUST 先有界停止各环境核心并等待既有浏览器清理，再有界停止所管理的 Ads CLI daemon，最后退出 Electron；无环境核心运行时也 MUST 执行 daemon 停止。普通窗口关闭到托盘不属于真正退出，MUST NOT 因此停止 daemon。

#### Scenario: 真正退出停止所管理 daemon

- **WHEN** Edge 已启动或接管 Ads CLI daemon，随后用户执行真正退出
- **THEN** Edge 在环境停机后执行 Ads CLI stop，确认或有界等待 daemon 停止后再退出

#### Scenario: 无运行环境仍清理 daemon

- **WHEN** Ads CLI daemon 已由本次 Edge 管理，但当前没有环境核心子进程
- **THEN** `before-quit` 仍进入运行时清理流程，MUST NOT 因环境列表为空直接放行并留下 daemon

#### Scenario: 关闭窗口到托盘保持运行时

- **WHEN** 用户只关闭桌面窗口而应用按既有语义常驻托盘
- **THEN** Edge 与所管理 Ads CLI daemon 继续运行，不执行真正退出清理
