# Tasks — comment-keep-open-through-approval

## 1. aidcp-cloud — runTask keep-open 重构

- [x] 1.1 `comment-scheduler.ts` `runTask`：把「搜索发现 → pick → readNote → composeAndApprove → dedup → post」收进**单个持有租约**（`withLease`，`leaseMs=KEEP_OPEN_LEASE_MS≈240000`），删除 prepare 复搜与 commit 复搜。 <!-- aidcp-cloud 1fd65c9 -->
- [x] 1.2 换词只在「fresh 空 / pick 无 index」时 `continue`；选中一篇后无论成败一律 `break`（不复搜、不换词、不评他篇）。 <!-- aidcp-cloud 1fd65c9 -->
- [x] 1.3 `composeAndApprove` 移进持锁回调；人审超时/被拒 → `compose_skipped` 结束。 <!-- aidcp-cloud 1fd65c9 -->
- [x] 1.4 浏览器保护靠边端租约（EdgeTaskCoordinator：持锁期 `canExecute(undefined)=false`、活跃租约不被抢占）——单持有租约天然覆盖审批窗口，无需改 takeover；`withManualCommitMarker` 保持人工评论风控配额跳过语义（human-only，不动）。 <!-- aidcp-cloud 1fd65c9 校订：takeover 标记是风控配额跳过、非浏览暂停，故不扩到 automatic -->
- [x] 1.5 `edge-steps.ts`：`readNote` 保持当前页 `note.open{noteId}`；`searchAndHarvest` 的「无 page.cards」日志去掉「离线」断言，改中性措辞。 <!-- aidcp-cloud 1fd65c9 -->
- [x] 1.6 保留新鲜度不变量：发布前依赖边端就地核对（见 2.1），云端 `post` 据回执 ok 判成败；`recordInteraction` 仅在 `ok:true` 后。 <!-- aidcp-cloud 1fd65c9 -->

## 2. aidcp-edge — 发布前就地核对 + 发现搜索判据加固

- [x] 2.1 `browse-session.ts` `interaction.comment`：提交前读当前详情页 `noteId`（`parseNoteIdFromUrl`）与目标核对，明确不符诚实回 `note_page_mismatch` 不提交；取不到宽松放行（持锁为主保护）。 <!-- aidcp-edge 4576a2a -->
- [x] 2.2 `search-handler.ts` `waitForSearchNavigation`：抽共享 `SEARCH_RESULT_URL_RE`（browse-session import 同一常量）替换宽松 `includes('search')`。 <!-- aidcp-edge 4576a2a -->
- [x] 2.3 `search-handler.ts`：确认到达后核对 URL `keyword` 参数解码 == 本次词（trim/大小写/双重编码容错），不等回未到达（关 Bug C）；browse-session 采卡权威闸同校验。 <!-- aidcp-edge 4576a2a -->
- [x] 2.4 `clickSearchSubmit` 找不到按钮时补 warn 日志。 <!-- aidcp-edge 4576a2a -->

## 3. aidcp-cloud — 回执区分来源

- [x] 3.1 终态结果卡区分「排期评论（自动）」与人工 `/comment`（`commentSourceLabel(priority)` → `postResultCard(…, source)` → server 卡 command 字段）。 <!-- aidcp-cloud 1fd65c9 -->
- [x] 3.2 `compose_skipped` 回执按判别原因诚实分文案：`composeAndApprove` 返回 `{approved}` 判别式（带 `ComposeSkipReason`）取代裸 `null`；`composeSkipDetail(reason)` 把「撰写为空 / 撞参考 / 人审口未接线 / 审批卡发送失败 / 送审后未获批(超时或被拒)」映射成人话，两个回执构造器共用。根治「已出稿送审却写『撰写为空』」的假归因（07-11 大白《Agentic RAG》即此例：真机日志 17:12:52 出稿→17:14:22 人审超时 90000ms 未获批，非撰写为空）。「拒绝」「超时」授权口层不可分，合并为「超时或被拒」。reason 缺省回落旧措辞、向后兼容。 <!-- aidcp-cloud 409ee4f 2026-07-11 deployed dev -->

## 4. 测试

- [x] 4.1 cloud：happy-path 改单租约贯穿人审断言 + 新增「人审拒绝→只搜一次、单租约、不复搜不换词」。 <!-- aidcp-cloud 1fd65c9 -->
- [x] 4.2 edge：`search-handler` 关键词一致/旧关键词页(Bug C)/双重编码 三例。 <!-- aidcp-edge 4576a2a -->
- [x] 4.3 edge：`interaction.comment` 就地核对不符→note_page_mismatch、一致→正常发布。 <!-- aidcp-edge 4576a2a -->
- [x] 4.4 回归：cloud `test:acceptance` 47 + 全量 1803 + typecheck 全过；edge `test:acceptance` 16 + 全量 997 + typecheck 全过。 <!-- 1fd65c9 / 4576a2a -->
- [x] 4.5 回执文案回归：`compose-approve.test.ts` 断言各 reason（empty_compose/approval_not_wired/approval_unapproved/approval_send_failed/overlaps_reference）；`comment-scheduler.test.ts` 断言 compose_skipped 回执「送审未获批 ≠ 撰写为空」+ reason 缺省回落。cloud `test:acceptance` 47 + 全量 1811 + typecheck 全过。 <!-- aidcp-cloud 409ee4f -->

## 5. 集成 / 部署 / 验收

- [x] 5.1 `openspec validate comment-keep-open-through-approval --strict` 通过。
- [x] 5.2 集成：cloud/edge 各 rebase origin/master（未漂移，ff）+ ff 推送 + 主 checkout 同步 + 清 worktree/分支。 <!-- cloud 7655b00..1fd65c9 / edge 7d7d758..4576a2a on origin/master -->
- [x] 5.3 部署 dev（cloud）：备份 `cloud.bak.20260711-155913.tar.gz` → 校验和 rsync 仅 4 文件 → restart → healthcheck 全绿（active、8787 监听、PG 全 store 就绪、CommentScheduler 就绪、飞书长连接已建立）；ECS comment-scheduler.ts md5=83d3557 与本地一致。 <!-- aidcp-cloud 1fd65c9 2026-07-11 deployed dev -->
- [x] 5.5 部署 dev（cloud，回执文案 409ee4f）：备份 `cloud.bak.20260711-174118.tar.gz`（校验含 src、node_modules 0 条）→ itemized checksum dry-run 揪出并绕开一处非我 test 文件漂移（`facebook-group-join-judge.test.ts`，ECS 07-10 旧版，非并发 WIP）→ 手术式 rsync 仅我 4 文件（ECS md5==快照）→ restart → healthcheck 全绿（active、8787、PG 全 store、CommentScheduler 就绪、飞书长连接已建立）。 <!-- aidcp-cloud 409ee4f 2026-07-11 deployed dev -->
- [~] 5.4 真机验收（backlog 簇 55）：dev 对 Tmax（ads-k1e0awu5）重跑排期/手动评论——审批期浏览器停详情页不漂走、无复搜、通过后原地发成、超时/被拒诚实结束、发现搜索不再被旧页假成功；观察边端空闲看门狗是否在 ~90s 持锁期误杀（edge 需运营机 pull master + 重建生效）。**部分已被生产真机自证（07-11 大白 ads-k1e0ero8 自动排期评论《Agentic RAG》）**：换词只在搜空时触发（17:12:01 词1 搜空释放→17:12:18 词2 命中）、选中即定单次搜索、审批期持锁 124s（17:12:18→17:14:22，在 240s TTL 内）**无看门狗误杀/无断连/无浏览命令偷浏览器**、17:12:52 出稿→17:14:22 人审 90000ms 超时诚实不发。**仍待运营机验**：通过后原地真发成、发现搜索旧页假成功堵住、新回执文案（送审未获批 ≠ 撰写为空）呈现正确。
