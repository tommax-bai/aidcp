## Context

Electron 主进程已经有统一的 `maybeRenameEnvToNickname`：收到核心 stdout 的结构化 `identity` UI 事件后，对 AdsPower 环境执行 name-only `user/update`，并负责同名幂等、在途去重、串行节流与失败降级。XHS 核心会发该事件；视频号 `WechatAuthCoordinator` 虽然在冷启动恢复会话或首次扫码后得到 `AuthSnapshot.identity.displayName`，目前只把身份放进 Cloud auth status，Electron 没有收到本地身份事件。

视频号身份状态有明确的安全边界：只有 `identityMatches=true` 才说明昵称由当前环境会话验证；`identity_verifying`、身份漂移和未登录状态均不得驱动本地改名。

## Goals / Non-Goals

**Goals:**

- 冷启动恢复已保存会话和首次扫码绑定后，都把已验证的视频号昵称送入既有本地改名链。
- 未验证、空昵称或身份不匹配时不发身份事件、不改环境名。
- 左栏账号来源按实际平台标记，避免把视频号误标为 XHS。
- 保持现有改名的幂等、限速与诚实失败语义。

**Non-Goals:**

- 不新增 Cloud 消息或修改 protocol v2。
- 不修改账号主键、环境绑定或视频号身份校验规则。
- 不做存量环境批量改名，不调用真实账号写接口验证。
- 不构建或发布 Edge 安装包。

## Decisions

### D1: 在视频号认证状态监听器中发本地结构化身份事件

运行时订阅 `auth.onChange`，仅当快照同时满足 `identityMatches=true`、有非空 `identity.externalId` 和非空 `identity.displayName` 时输出 `[ui-event] {"kind":"identity",...}`。这复用 Electron 已有的 stdout 事件桥和改名链，不新增跨进程 IPC 或 Cloud 依赖。

备选是在 Cloud auth status 回流后再更新环境名；否决，因为改名本来就是 Edge 本地事实，增加网络依赖会拖慢冷启动并扩大协议面。

### D2: 由认证验证状态而非“读到昵称”单独授权事件

事件门槛使用 `identityMatches`，不在 `identity_verifying` 阶段使用加密存储中的旧昵称。这样环境名只跟随当前会话已验证身份，身份漂移或验证失败继续 fail closed。

备选是在加载本地存储时立即发昵称；否决，因为当前会话尚未证明仍属于该身份。

### D3: 主进程按环境平台记录真实昵称来源

身份事件处理继续复用同一个 `evt.account` 分支和 `maybeRenameEnvToNickname`，但 `status.account.source` 从固定 `xhs` 改为当前 handle 的真实平台标记。真实昵称是否存在仍由结构化事件的非空 name 决定。

备选是新增视频号专用改名分支；否决，因为会复制幂等、限速和失败处理，并容易产生平台行为漂移。

## Risks / Trade-offs

- **[认证状态会多次切换，重复发同一身份事件]** → 主进程已有 `handle.name` 同名跳过和 `handle.renamingTo` 在途去重；测试锁定相同昵称不会扩大写面。
- **[结构化日志包含昵称]** → 该 stdout 通道已承载账号身份 UI 事件；只发送显示昵称和平台 external id，不含 cookie、token 或会话材料。
- **[改名写失败]** → 沿用现有 warn、保持旧名、不阻塞运行；后续冷启动或新的身份事件自然重试。

## Migration Plan

- 在隔离 Edge worktree 实现并跑视频号身份事件、Electron UI 事件、改名写口相关 focused tests，再跑 typecheck 与适用全量测试。
- 集成后该行为随下一次视频号环境冷启动生效；无需数据迁移。
- 回滚只需撤销身份事件桥和平台来源标记；已经成功更新的 AdsPower 环境名保留昵称，不影响账号绑定。

## Open Questions

（无。）
