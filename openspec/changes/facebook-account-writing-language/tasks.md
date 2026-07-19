## 1. Edge Facebook 人设语言设置

- [x] 1.1 在 aidcp-edge 人设向导中增加仅 Facebook 可见的中文/英文/越南语单选，按环境回显与隔离，未选择时诚实阻止生成
- [x] 1.2 同步 Edge/Cloud `protocol.ts` 的 `writingLanguage` 与 `personaWritingLanguage` 类型，接通 Edge IPC/状态投影且不把语言混入 `keywordSelections`
- [x] 1.3 为 Facebook-only 可见性、环境切换隔离、请求形状和缺选择拒绝补 Edge 聚焦测试

<!-- Edge implementation: aidcp-edge 4355d42. Current-source validation: focused persona/protocol tests 83/83, full suite 1864/1864, typecheck passed. -->

## 2. Cloud 人设模型与权威回显

- [x] 2.1 为 Soul 增加可选受控 `writing_language`、loader/serializer round-trip 与公共语言提示/三态守卫
- [x] 2.2 让 `persona.generate` 按已验证平台校验独立语言字段并确定性注入草稿，非法/缺失/非 Facebook 使用均返回具名拒因
- [x] 2.3 让 UI snapshot 按账号投影已保存语言或显式缺失状态，并补人设生成、持久化与协议测试

<!-- Cloud persona implementation is included in aidcp-cloud 3e9e1be. Legacy souls remain parseable; missing FB language is projected as null and public text generation fails closed instead of guessing. -->

## 3. Facebook 帖子与评论产文

- [x] 3.1 让 Facebook ContentCreator 使用账号写作语言和 Facebook 正文语境，保持 XHS prompt 逐位兼容并在待审前执行语言守卫
- [x] 3.2 让通用 CommentComposer、Facebook 定向 composer 与 CommentDeAiFlavor 从首次生成/重写起保持账号写作语言，缺失或不匹配时 fail-closed
- [x] 3.3 补中文/英文/越南语帖子与评论、改写回退、存量缺语言、小红书不受影响的聚焦测试

<!-- Cloud text implementation: aidcp-cloud 3e9e1be. Tests cover zh-CN/en/vi drafts and comments, rewrite fallback, missing config, final pre-approval rejection, and unchanged XHS prompt branching. No real Facebook write was performed. -->

## 4. 契约、验证与交付

- [x] 4.1 更新 `docs/protocol.md` 并运行协议漂移、发布/评论安全验收、Edge/Cloud 全量测试与 typecheck
- [x] 4.2 严格校验 OpenSpec，逐仓提交并记录 commit SHA、验证结果、偏差与真实写入边界
- [ ] 4.3 串行集成并推送 Edge/Cloud/control 默认分支，从 eligible canonical checkout 部署 dev，检查服务/监听/health/log 且不宣称未执行的真实 Facebook 写入

<!-- Validation: Edge/Cloud protocol.ts byte-identical; Cloud full suite 2571 passed + 8 gated skips, Edge full suite 1864 passed, both typechecks passed, openspec validate --strict passed. Runtime boundary: model/stub and deterministic guard validation only; no real-account post/comment submission was attempted. -->
