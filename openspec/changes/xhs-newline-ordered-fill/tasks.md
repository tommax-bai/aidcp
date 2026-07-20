## 1. Edge 输入实现

- [x] 1.1 将小红书正文构造成普通文本块与独立 newline 单元，保证所有 `Input.insertText` 参数不含 CR/LF，并以真实 Enter 保留单换行与连续空行
- [x] 1.2 增加 Enter 后的已写前缀与末端 selection 有界确认；不稳定、异常或抢占时复用现有清场路径诚实失败

## 2. 回归测试

- [x] 2.1 扩展发布 Fake CDP，建模正文光标、Enter 建段及换行后 selection 回退
- [x] 2.2 覆盖多段正文、连续空行、禁止含换行 `insertText`、尾字不再倒序积累、确认失败清场及既有单行行为

## 3. 验证

- [x] 3.1 在 `aidcp-edge` 运行发布处理器聚焦测试
- [x] 3.2 在 `aidcp-edge` 运行完整测试与 `npm run typecheck`
  <!-- `npm test`: 1964 passed, 0 failed; `npm run typecheck`: passed; `npm run test:acceptance`: 25 passed, real-machine E2E remained explicitly gated. -->
- [x] 3.3 运行 `openspec validate xhs-newline-ordered-fill --strict` 与差异检查
  <!-- Strict validation passed; `git diff --check` passed in both control and Edge worktrees. -->

## 4. 集成与 dev 收口

- [ ] 4.1 提交并推送控制仓与 Edge 变更，记录仓库、SHA、验证和偏差
- [ ] 4.2 同步最新默认分支后以 fast-forward 集成并推送 `main`/`master`；确认 dev 源码客户端加载新 Edge 构建，不打包安装程序
