# Design — client-login-credential-persistence

## Decisions

### D1. 主进程负责存取，渲染层只负责显示

登录页通过 preload 暴露的窄 IPC 读取和清除记忆内容；渲染层不使用 `localStorage`、`sessionStorage` 或明文文件保存客户访问密钥。登录成功时，现有 `client-auth:login` handler 在收到已经校验过的凭据后保存记忆内容。

### D2. 使用 Electron `safeStorage` 加密

账户名和访问密钥作为一个 JSON 小对象交给 `safeStorage.encryptString`，以 base64 写入当前实例的 `userData/client-login-prefill.json`。读取时只有主进程解密并校验字段类型后，才把回填值返回登录页。加密能力不可用或文件损坏时，按无记忆内容处理，不写明文回退文件，也不阻塞正常登录。

### D3. 清除条件与会话边界一致

- 输入框的 `input` 事件只要发现任一字段变为空白，就调用清除 IPC；因此用户手动删除账号名或访问密钥后，下一次打开登录页不会回填旧值。
- `clearClientSession()` 统一调用凭据记忆清除，使显式退出、服务端判定会话失效和启动后发现会话失效都不会留下旧凭据。
- 登录失败不主动清除当前输入，便于用户修正后重试；下一次成功登录会覆盖旧记忆。

### D4. 记忆文件不参与客户鉴权

记忆内容只用于登录页回填。客户鉴权请求仍只发送用户当前提交的值，session 文件仍只保存 token/name/expiresAt；不会把访问密钥放进 session JSON、日志、协议或云端。

## Risks and mitigations

- `safeStorage` 在某些系统环境可能暂不可用：不生成明文替代物，登录功能继续可用但本次不记忆，并在代码中保持静默降级。
- 登录页被关闭或应用异常退出：已经清空的记忆通过 IPC 删除，不依赖页面关闭回调。
- 会话失效路径有多处：将清除动作放进现有 `clearClientSession()`，覆盖统一登出和启动/刷新失效分支。
