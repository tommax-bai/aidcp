# Proposal — client-login-credential-persistence

## Why

客户每次启动客户端都需要重复输入相同的客户账户名和访问密钥，登录门没有利用用户已经成功输入过的内容。与此同时，退出客户端登录或用户主动删除输入框内容后，旧凭据不应继续被自动回填。

## What changes

- 登录成功后，客户端在当前实例的 `userData` 目录保存账户名和访问密钥的本地加密副本。
- 登录页打开时，从主进程读取并回填已保存的账户名和访问密钥；凭据不通过未加密的渲染层存储暴露。
- 用户把账户名或访问密钥输入框清空时，立即删除本地记忆；重新成功登录后保存新的完整输入。
- 客户端退出登录、会话失效或回到登录门时，同时清除本地记忆，避免旧账户凭据残留。
- 不改变客户鉴权接口、会话 token 生命周期或平台账号登录逻辑。

## Impact

- Affected specs: `edge-client-login-gate`
- Affected code: `aidcp-edge/src/electron/main.cjs`, `src/electron/preload.cjs`, `src/electron/renderer/login.html`
- Validation: edge login-prefill contract tests, acceptance tests, typecheck
