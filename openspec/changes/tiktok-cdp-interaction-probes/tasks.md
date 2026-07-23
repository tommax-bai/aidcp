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

## 6. TikTok 发布机制探针（不提交）

- [x] 6.1 在 `k1eu5amn` 只读识别 TikTok 上传入口、实际路由、页面阻断状态、唯一文件输入接受类型和编排字段，不选择文件。
<!-- 2026-07-21 live read-only evidence: the current video page exposed one visible `a[data-e2e="nav-upload"]` to `/tiktokstudio/upload?from=webapp&tab=video`. TikTok Studio settled at `/tiktokstudio/upload` with blockReason=none, one enabled `input[type=file][accept="video/*"]`, `multiple=false`, and semantic nodes `select_video_container` / `select_video_button`. No file was selected; no composer fields exist before upload. -->
- [x] 6.2 参考 Facebook/XHS 探针，在 `src/tiktok/probes/` 实现独立且可单测的发布编排器探针；复用现有 CDP/AdsPower 原语，不注册生产平台、协议或命令路由。
- [x] 6.3 新增手动运行器，以显式 profile 和可选合成素材路径为输入；代码路径不查询或点击最终发布控件，不派发提交快捷键，不调用 form submit。
- [x] 6.4 增加聚焦测试，覆盖入口/文件输入唯一性、阻断、上传确认、文案回读、报告脱敏和静态 no-submit 边界。
<!-- Edge implementation: `src/tiktok/probes/publish-composer-probe.ts`, export, `scripts/tiktok-publish-composer-probe.ts`, and focused fixture/behavior/source-boundary tests. The probe reuses CDP file-input setting but contains no final-control lookup or final-submit path. -->
- [x] 6.5 运行 TikTok 聚焦测试、Edge typecheck、diff 检查与 OpenSpec strict validation。
<!-- Initial validation after implementation: `npx tsx --test test/tiktok/*.test.ts` PASS 24/24; `npm run typecheck` PASS; Edge/control `git diff --check` PASS; `openspec validate tiktok-cdp-interaction-probes --strict` PASS. Final validation is rerun after live calibration. -->
<!-- Final validation after live calibration: TikTok focused tests PASS 25/25; Edge typecheck PASS; Edge/control diff checks PASS; OpenSpec strict validation PASS. -->
- [x] 6.6 用临时生成的无敏感合成视频在 `k1eu5amn` 验证文件选择、平台上传确认与文案填写，停在 `composer_ready_not_submitted` 并保持浏览器打开；若页面或目标不明确则诚实停止。
<!-- Live evidence on k1eu5amn: a 2-second 720x1280 solid-color MP4 was set on the unique video input. The input then disappeared and TikTok Studio exposed a blob thumbnail plus canvas preview, one `contenteditable=true role=combobox` caption seeded with the 20-character filename, and a separate Vietnamese location search input. A first-use editing tutorial was acknowledged only by an exact `role=alertdialog` + `Đã hiểu` match. The caption was replaced with a 38-character probe marker and read back exactly: status=composer_ready_not_submitted, uploadAcknowledged=true, matched=true, submitted=false. Read-only settings evidence included publish-now/schedule radios, audience=`Mọi người`, location, high-quality upload, music copyright check, and quick content check. The browser remains open on the composer; no final publish control was queried or activated. -->
- [x] 6.7 回写真机结论、未证明边界、提交 SHA 与验证结果，提交并推送 Edge/控制仓 feature 分支；不部署、不归档。
<!-- Delivery: aidcp-edge a6b0ee0; aidcp control OpenSpec artifact 6ff0fbe followed by this ledger-only closeout commit. Both remain on `codex/tiktok-cdp-interaction-probes`. Proven boundary is browser UI upload/composer readiness only: no final publish control lookup, no submission, no server-publication proof, no production platform registration, no deployment, and no archive. -->

## 7. Douyin 差异能力调研（只读）

- [x] 7.1 对照抖音 OpenSpec、探针实现和 TikTok 官方资料，明确多 surface、社交 shadow、消息/直播入口、回复语言和官方 API readiness 的最小范围。
<!-- 2026-07-23: comparison captured in `docs/research/tiktok-web-and-douyin-comparison-2026-07-23.md`. Reused principles are surface-specific adapters, independent write authorization, exact target binding, UI-only evidence, and official API preference; Douyin selectors and its DM/live outcomes are not treated as TikTok proof. -->
- [x] 7.2 在 `k1eu5amn` 另开临时 TikTok 标签，只读盘点当前 surface、For You/Following/作者主页及搜索、标签/音乐、消息、通知、直播入口，不破坏现有 Studio 草稿。
  <!-- 2026-07-23: 通过 AdsPower API 绑定 profile 后仅创建、激活并关闭自己的临时标签。For You 水合后存在稳定 video id，并发现 Following、主页、搜索、标签/音乐、消息、通知、直播入口；Following 与主页为不同 DOM surface。后台标签仅 readyState 完成但未水合，必须激活并有界轮询。未点击、未输入、未发送。 -->
- [x] 7.3 在 `src/tiktok/probes/` 实现独立能力差异 snapshot：surface、入口候选、当前 video id、关注/收藏/分享 shadow、`uiLocale`、`replyLanguage=unconfigured` 和官方 API 静态 readiness；不新增真实动作方法。
  <!-- 2026-07-23: Edge `src/tiktok/probes/capability-research-probe.ts` 使用 TikTok 精确 data-e2e 做只读 inventory；动态主页/标签/音乐路径不进入 snapshot，官方 API readiness 不读取凭证、不发网络请求。 -->
- [x] 7.4 新增手动 runner，严格绑定显式 profile，使用临时标签完成只读盘点并关闭自己的标签；不得选择会话、打开通知内容、搜索、输入或发送。
  <!-- 2026-07-23: Edge `scripts/tiktok-capability-research-probe.ts` 仅走 AdsPower API，并限定 Target.createTarget/activateTarget/closeTarget；不会进入消息、通知、直播、搜索或编辑器。 -->
- [x] 7.5 增加 fixture、行为和源码边界测试，覆盖 surface 歧义、抖音 selector 不复用、社交状态 unknown、消息/通知只入口、UI/回复语言分离及零输入/零点击。
  <!-- 2026-07-23: `npx tsx --test test/tiktok/capability-research-probe.test.ts` 8/8；`npm run typecheck` 通过。 -->
- [x] 7.6 在 `k1eu5amn` 运行只读 runner，记录真实入口、可识别/缺失 surface 和未证明边界；所有社交/回复/发布动作保持未执行。
  <!-- 2026-07-23: 正式 runner 通过 AdsPower API 附着。For You 有唯一 stable video id；Following 与个人主页已水合。For You 精确识别 follow/favorite/share 各 1 个，均 shadow_ready/state unknown；搜索 2 候选为 ambiguous，消息/通知/直播/音乐入口存在，标签入口缺失。UI locale=vi-VN，replyLanguage=unconfigured/replyBlocked=true。report actionsExecuted=[]/submitted=false，临时标签均关闭。 -->
- [x] 7.7 运行 TikTok 聚焦测试、Edge typecheck、diff 检查和 OpenSpec strict validation，回写提交 SHA 并推送两个 feature 分支；不合并、不部署、不归档。
  <!-- 2026-07-23: Edge 0a1dac1；control 435fdde。`npx tsx --test test/tiktok/*.test.ts` 34/34，`npm run typecheck`、两仓 `git diff --check`、`openspec validate tiktok-cdp-interaction-probes --strict` 均通过。两个现有 feature 分支使用普通 fast-forward push；未合并、未部署、未归档。 -->

## 8. 后续系统设计输入

- [x] 8.1 基于 TikTok 真机证据、Douyin 偏差和现有 Facebook/XHS 平台边界，形成一份面向后续正式 OpenSpec 的系统设计输入文档；区分可复用机制、TikTok 专属适配、最小切片和明确不做，避免预先发明完整协议或数据库模型。
  <!-- 2026-07-23: 新增 `docs/design/tiktok-system-design-input-2026-07-23.md`。文档以 For You 只读浏览为首个生产切片，复用 PlatformDriver/Cloud registry/EventBus/RiskController/审批/语言边界，保持 TikTok selector、surface、成功语义和官方授权专属；评论、互动、官方发布分开立项，私信/通知回复/直播暂不设计。 -->
- [ ] 8.2 更新研究证据索引，运行文档 diff 检查与 OpenSpec strict validation，提交并推送 control feature 分支；不合并、不部署、不归档。
