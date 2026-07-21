## 1. 隔离环境与模块骨架

- [x] 1.1 创建 `aidcp-edge.wt/tiktok-cdp-interaction-probes` 与 `codex/tiktok-cdp-interaction-probes` 分支，确认独立依赖目录和工作树基线。
<!-- 2026-07-21: control and edge worktrees created from origin/main@6ed4b43 and origin/master@7b98245; both branches are codex/tiktok-cdp-interaction-probes. Edge node_modules is absent and is not a symlink. -->
- [x] 1.2 新增独立的 TikTok 探针模块与导出入口，不注册生产 `PlatformId`、协议或命令路由。

## 2. TikTok 页面探针

- [x] 2.1 实现页面阻断分类、当前可见视频稳定标识和虚拟列表安全重探，并以 fixture 单测覆盖登录/挑战/目标歧义。
- [x] 2.2 实现有界信息流滚动与滚动前后变化证明，未变化时诚实返回 `no_change`。
- [x] 2.3 实现双重授权、单向且最多一次点击的点赞探针，覆盖 `shadow`、`already_liked`、`ui_confirmed` 与 `ambiguous`。
- [x] 2.4 实现只有 fill 能力的评论编辑器探针，验证源码路径不包含发送按钮点击、Enter 或表单提交。

## 3. 手动运行器与证据

- [x] 3.1 新增 AdsPower 手动运行脚本，严格绑定显式 profile，默认保持浏览器打开，并输出不含 cookie/token/完整评论文本的结构化报告。
- [x] 3.2 补齐运行门、报告脱敏、目标一致性与评论不可发送边界的聚焦测试。
<!-- 2026-07-21: edge module, manual runner, and 16 focused tests added under src/tiktok, scripts, and test/tiktok. Navigation follows the existing Facebook Reels ArrowDown then single-wheel fallback; CDP/AdsPower primitives are reused and no production PlatformId, protocol, command route, or cloud file changed. -->

## 4. 本地静态验证

- [x] 4.1 在 Edge 工作树运行 TikTok 聚焦测试与 `npm run typecheck`，记录命令和结果。
<!-- Validation: `npx tsx --test test/tiktok/*.test.ts` PASS 16/16; `npm run typecheck` PASS; `git diff --check` PASS. -->
- [x] 4.2 运行 `openspec validate tiktok-cdp-interaction-probes --strict`，修正全部规范问题。
<!-- Validation: `openspec validate tiktok-cdp-interaction-probes --strict` PASS. -->

## 5. `k1eu5amn` 真机验证与交付

- [x] 5.1 先以只读模式运行浏览探针，确认环境登录状态、当前视频、滚动变化和阻断分类，不执行任何写动作。
<!-- Live read-only evidence on k1eu5amn: login=logged_in, block=none; browsing confirmed 7646842677748845844 -> 7636316950477507848 -> 7656791346400808200. Like remained shadow/unexecuted. The live feed lacked /video/ anchors, so the bounded React item-id fallback was added and fixture-tested. AdsPower API later returned empty/timeout while the browser stayed alive; direct port 52068 was accepted only after an exact start.adspower.net?id=k1eu5amn marker self-proof. -->
- [x] 5.2 在同一环境显式打开点赞双门，最多真实点赞一条此前未点赞的视频，并记录同一 video id 的前后 UI 状态；若目标不安全则诚实跳过。
<!-- Live like evidence on k1eu5amn: video 7661993431920676116, before=unliked, exactly one click dispatched, after=liked, result=ui_confirmed, confirmation=ui_only. No server-persistence claim. -->
- [x] 5.3 只向唯一评论编辑器输入无敏感测试文本，回读匹配后保持未发送状态和浏览器打开，记录文本长度而不记录全文。
<!-- Live draft evidence on k1eu5amn: video 7663490008363420948, textLength=42, matched=true, status=filled_not_submitted, submitted=false. Read-only screenshot inspection confirmed the text remained in the editor and the send arrow was untouched; the temporary screenshot was not retained as a deliverable. Browser remained open. -->
- [x] 5.4 将真机结论、未证明边界、Edge/控制仓提交 SHA 与验证结果回写本任务清单，并推送两个 feature 分支；不部署、不归档。
<!-- Commits: aidcp-edge c5e0fa0 (pushed), aidcp control OpenSpec 9695885 (followed by this ledger-only closeout commit). Final validation: TikTok focused tests 16/16 PASS, Edge typecheck PASS, whitespace/diff checks PASS, OpenSpec strict PASS. Boundaries: probe-only, like confirmation is UI-only, comment remains an unsent local draft, no production registration, no deployment, no archive. -->
