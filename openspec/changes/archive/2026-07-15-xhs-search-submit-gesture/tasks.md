# Tasks

## 1. aidcp — OpenSpec 规格

- [x] 1.1 在 `comment-search-command` 规格新增要求：搜索提交 MUST 用真实用户手势（真实指针点击聚焦 + 携带字符文本的回车），未确认跳转 MUST 有界重试，MUST NOT 仅依赖程序化聚焦 / 裸回车 / 不可见提交按钮；保留既有诚实失败契约。 <!-- aidcp: specs/comment-search-command ADDED 一条要求 + 三 scenario；本收尾提交 -->

## 2. aidcp-edge — 搜索提交手势与重试（独立 worktree）

- [x] 2.1 `cdp-util.ts`：`dispatchKey` 增加可选 `text` 参数；`pressEnter` 传 `text:'\r'`（keyDown 携带字符文本，产生真实 keypress 形态）；不改 `pressEscape` 等其它调用方行为。 <!-- aidcp-edge cb9aeba -->
- [x] 2.2 `search-handler.ts` `executeSearch`：聚焦前先取**可见搜索框**中心坐标并派发一次真实指针点击（复用 `dispatchClick`），再执行既有 focus/clear；取不到坐标时回退旧的程序化聚焦（诚实降级）。 <!-- aidcp-edge cb9aeba -->
- [x] 2.3 `search-handler.ts` `executeSearch`：输入完成到回车之间设一个**停顿地板**（`SEARCH_SUBMIT_SETTLE_FLOOR_MS=700`，与既有 `action` 抖动取 max）。 <!-- aidcp-edge cb9aeba -->
- [x] 2.4 `search-handler.ts` `executeSearch`：将「回车未跳转 → 点提交按钮」兜底改为「有界重试回车（`SEARCH_SUBMIT_MAX_RETRY=3`，每次等一个 `waitForSearchNavigation` 窗口）」；提交按钮点击仅在其可见时作附加尝试；全部失败仍返回未确认（调用方回 `not_on_search_page`）。 <!-- aidcp-edge cb9aeba -->
- [x] 2.5 补单测：`executeSearch` 提交前有真实鼠标按下、Enter keyDown 携带 `text:'\r'`、首次未跳转会重试回车（桩 CDP）。 <!-- aidcp-edge cb9aeba: search-handler.test 15→18，全过 -->

## 3. aidcp-edge — 验证

- [x] 3.1 `npm run typecheck` + 全量 `npm test` 全过。 <!-- aidcp-edge cb9aeba: land-change 跑 test:acceptance + npm test 1356/1356 + typecheck 全过 -->
- [x] 3.2 真机验证（搜索提交这一步）：用**真机 CDP 驱动仓库实际 `executeSearch`** 打 dev 工程师大白 AI 搜索账号，warm 页 5/5、cold-navigate 4/5（唯一失手为冷启首搜、经重试与云端换词自愈）连续命中 `/search_result_ai`；对照现状约 0%。 <!-- 2026-07-15：shipped executeSearch 经真实 CDP adapter 驱动，warm 5/5 / cold 4/5。全闭环(真实排期评论把评论发出)见 4.3 backlog。 -->

## 4. 集成与收尾

- [x] 4.1 提交并推送 `aidcp-edge`（master）与 `aidcp`（main）默认分支；edge 收尾只到 commit/push（不出桌面安装包）。 <!-- aidcp-edge cb9aeba pushed origin/master + 主 checkout 已 ff 同步；aidcp 本收尾提交推 main -->
- [x] 4.2 `openspec validate xhs-search-submit-gesture --strict` 通过。
- [x] 4.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：全闭环真实排期评论（工程师大白）把评论真发出、搜索连续命中不再 `not_on_search_page`。 <!-- 登记入簇34（XHS 搜索 flakiness 根因/修复）；搜索提交侧已本 change 修复+验证，剩全链闭环观察。 -->
