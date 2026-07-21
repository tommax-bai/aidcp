## Context

Edge 经主进程调用 AdsPower `user/list`，再由 `normalizeProfile()` 把非敏感代理摘要投影给渲染层；该全量列表必须继续删除 `proxy_password`。最新主干已经增加按精确 `profileId` 读取单个环境完整代理配置的主进程能力，用于 Facebook 启动前预检，但尚未向渲染层提供受限编辑读取。当前代理编辑浮层仍只使用全量列表投影，因此密码框为空；保存时 `normalizeProxyInput()` 重建完整 `user_proxy_config`，对已有鉴权代理只修改其他字段时，旧密码不会随 `user/update` 提交。

用户已明确允许客户端在本地代理编辑界面回显密码。约束仍是：凭据只在 AdsPower 响应、Electron IPC、渲染层当前内存和写请求中短暂存在，不进入 `settings.json`、花名册、日志、诊断或代理摘要。

## Goals / Non-Goals

**Goals:**

- AdsPower 返回现有 `proxy_password` 时，在对应环境的代理编辑输入框中直接显示该值。
- 用户只修改 host、port、类型或用户名后保存时，现有密码仍随受限 `user/update` 请求提交。
- 用户可编辑或清空回显密码，提交结果与表单当前值一致。
- 继续保持写请求键集限制和日志脱敏边界。

**Non-Goals:**

- 不新增本地密码存储、OS keychain 缓存或 Cloud 同步。
- 不尝试恢复 AdsPower 未返回的密码，也不从代理商或其他环境推断凭据。
- 不改变代理生效时机、环境归属模型或 AdsPower API 端点。

## Decisions

1. 全量 `ads:listProfiles` 投影继续剥离 `proxy_password`。运营点击某一行“代理”时，新增具名 IPC 只接收该行 `userId`，主进程在客户鉴权开启时先校验有效会话和 `allowedProfileIds`，再复用最新主干的 `getProfileProxyConfig()` 精确读取该环境。这样不会把其他环境密码批量送进渲染层，也不会引入任意 URL 或原始响应能力。
2. 精确读取成功后才打开代理浮层，把返回的 `proxyPassword` 写入输入框，并把输入类型改为普通文本以满足“直接回显”。读取失败保持浮层关闭并显示真实原因；陈旧响应在目标环境已不在当前列表时丢弃。
3. 保存继续复用现有 `readProxyForm()` → `ads:updateEnvProxy` → `normalizeProxyInput()` 链，因此未改密码时自然原样提交，修改或清空时也按当前表单值提交。
4. 不把 profile 或密码写入 settings。环境花名册持久化只提取 `profileId/name/platform`，代理摘要继续只含类型、host、IP 和国家信息。
5. AdsPower 精确读取未返回 `proxy_password` 时，表单显示空值，客户端不声称已保留未知密码。该边界保持数据诚实；本变更只修复“API 已返回但编辑链未使用”的路径。

## Risks / Trade-offs

- [本地肩窥或渲染层脚本可看到明文代理密码] → 这是用户明确选择的本地运维体验；仍限制在已归属环境、当前本地页面内存中，不落盘、不进日志，并保持 Electron 上下文隔离边界。
- [AdsPower 某版本不返回密码] → 不伪造成功或缓存旧值；表单如实为空，用户需重新填写后再保存。
- [敏感读取 IPC 被越权调用] → IPC 只接受精确 `userId`，客户模式必须通过有效会话与 `allowedProfileIds`，本地 API 返回也必须匹配同一 `profileId`；全量列表继续不含密码。
- [对象传播扩大意外日志泄露面] → 精确响应只挑代理字段，保持现有代码无 profile 整体日志，回归检查摘要、设置和写客户端脱敏逻辑不包含密码。
- [清空密码会移除鉴权] → 表单当前值即提交意图；用户主动清空后保存会下发不含 `proxy_password` 的完整代理配置。

## Migration Plan

1. 先合入 Edge 源码和回归测试，不需要数据迁移。
2. 用户已在实现完成后明确授权合并与部署；本次升版为 `0.3.24`，从合并后的 Edge `master` 构建签名、公证且烘焙 `dev` 连接的 macOS 安装包，只发布到 dev 下载目录，不触碰 `ol`。
3. 回滚可恢复旧的非密投影和空密码表单，不影响 AdsPower 中已保存的代理配置。

## Open Questions

无。
