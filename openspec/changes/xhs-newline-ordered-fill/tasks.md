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

- [x] 4.1 提交并推送控制仓与 Edge 变更，记录仓库、SHA、验证和偏差
  <!-- Edge: `aa77762` (feature + `master` pushed). Control artifacts: initially pushed as `8fe8487`, then rebased onto current `origin/main` as `b5651d5`; this ledger commit records final integration status. Validation: focused 56/56, acceptance 25/25, full 1964/1964, typecheck, strict OpenSpec and both diff checks passed. Deviation: real-machine write E2E stayed gated because no disposable publish target was authorized; dev validation was source-process/load evidence only and no installer was built. -->
- [x] 4.2 同步最新默认分支后以 fast-forward 集成并推送 `main`/`master`；确认 dev 源码客户端加载新 Edge 构建，不打包安装程序
  <!-- Edge `master` fast-forwarded/pushed to `aa77762`; control `main` was rebased over concurrent default-branch updates, strict-validated, then fast-forwarded/pushed. Canonical Edge `dist` rebuilt at 2026-07-20 14:40:31 +08:00 contains `xhs-content-caret-state`, and Electron spawned canonical `dist/main.js` processes from that build at 14:40:45. No desktop installer, CI release, Cloud deploy, or production action was performed. -->

## 5. 实机回归修复（dev record #159）

- [x] 5.1 将 selection 末端判断改为最后顶层段落内的语义末端，并把归尾 Range 收口到该段落内部
- [x] 5.2 增加真实嵌套 `<p>` DOM 回归：末段空段 caret 直接通过、前段 caret 归尾后通过，保留既有数字 fake 错序/吞 Enter 用例
  <!-- Focused handler suite: 58 passed, including two JSDOM tests that execute the production probe expression against nested ProseMirror paragraphs. -->
- [x] 5.3 运行发布处理器聚焦测试、验收、完整测试与 `npm run typecheck`
  <!-- Focused: 58 passed; acceptance: 26 passed with real-machine E2E explicitly gated; full: 1988 passed, 0 failed; typecheck passed after making JSDOM eval's unknown return explicit in the test. -->
- [x] 5.4 运行 OpenSpec strict validation 与 control/Edge 差异检查，记录 record #159 的真实边界和验证偏差
  <!-- Dev record #159 failed at 2026-07-20 15:18:20 +08:00, seq=4 fill_field, error=`engine_error: content_newline_unstable`; DB stayed `failed` with no platform id/url and no submit. Root boundary was nested last-`p` caret vs outer-editor Range equality. Strict validation and both diff checks passed. Deviation: no automatic real-draft retry or submit probe was performed; real-machine E2E remains operator-gated. -->
- [ ] 5.5 提交、推送并同步最新默认分支后 fast-forward 集成；重建 canonical Edge `dist`，不打包安装程序、不自动重试真实稿件
