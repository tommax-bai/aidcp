# Tasks — generalize-contact-info

> **实装状态（2026-07-09）**：代码全部 land 到三仓 master（cloud `2f0ef2a`、console `49d4203`、edge `7699be8`），控制仓 spec/design/tasks 在 main。**wire 采 Method A**：物理 wire 字段 `groupChatCode` **保留不改**（protocol.ts 两份零改动），只改内部变量为 `contactInfo`；用户「wire 也物理改名」诉求下沉为 **Wave4 收尾**（需协调 edge/cloud 同波 + dual-declare，属 §7 热点，另起）。**尚未部署**（DB 列改名为手动协调迁移，见 §9）。
> 部署波次：Wave1 cloud 内部+DB+命令 → Wave2 cloud panel + console 同波 → Wave3 edge → Wave4 wire 物理改名收尾。

## 1. aidcp-cloud — 账号存储 + 注入链改名（Wave1）

- [x] 1.1 `account-store.ts`：`setContactInfo`/`getContactInfo`、`SetContactInfoResult`、注释。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 1.2 `feishu/commands.ts`：尾部 `--contact`（trailing-only/present=on，删 `group:on/off`）、`injectContact`、HELP。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 1.3 `comment-agent/comment-task-runner.ts`：`CommentTaskSteps` 接口字段 → `contactInfo`。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 1.4 `comment-agent/comment-scheduler.ts`：`getContactInfo`/`injectContact`/`contactInfo`/`withContact`/`contact_info_missing`/文案。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 1.5 `comment-agent/compose-approve.ts`：`contactInfo` + 日志。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 1.6 `comment-agent/edge-steps.ts`：`post()` 参数 → `contactInfo`；**wire 采 Method A**——发键仍 `groupChatCode`（`{ groupChatCode: contactInfo }`），未 dual-emit `contactInfo` 键（偏离原计划，见状态头）。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 1.7 `server.ts`：接线 + 结果卡文案（`/comment --contact`、排期带联系方式评论标题）。 <!-- aidcp-cloud 2f0ef2a -->

## 2. aidcp-cloud — DB 列物理改名（Wave1，协调单写迁移）

- [x] 2.1 `migrations/0036_rename_group_chat_info_to_contact_info.sql`：schema-qualified 幂等 guard + `lock_timeout` + fresh-DB 兜底；含 `accounts.contact_info`、`account_content_schedule.contact_comment_enabled/daily_cap`、表 `contact_comment_attempts`(+索引)。不改历史 `0027_*.sql`。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 2.2 `account-store.ts` 自愈 DDL 改新名 + 删旧 `ADD COLUMN group_chat_info` 行 + in-method SQL。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 2.3 `config/content-schedule-store.ts`：列/reason/`hasContactInfo`/`sharedContactInfoWarning`（**携带一码一号放松、无 shared 硬拒**）/`recordContactCommentAttempt` 等。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 2.4 `panel/panel-store.ts`：row-shape + `ACCOUNT_SELECT` 列名。 <!-- aidcp-cloud 2f0ef2a -->

## 3. aidcp-cloud — 群评特性正名 + 精选 withGroup（Wave1/2）

- [x] 3.1 `orchestrator/content-scheduler.ts`：`contactComment*`/`triggerContactComment`/`contactAttemptsTodayCount`/action `'contact_comment'`。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 3.2 `panel/panel-server.ts`：路由 `/contact-info`（**+ 旧 `/group-chat-info` 双认**）、请求/响应 `contactInfo`（+ 旧 `groupChatInfo` 双认 body）、reason `no_contact_info`/`invalid_contact_info` + 成功侧 `sharedContactInfoWarning`（放松）。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 3.3 `panel/panel-server.ts` 精选 `withContact` 接收端 + `panel/types.ts` 签名（与 console 同波）。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 3.4 `panel/panel-store.ts` DTO `contactInfo` + `panel/version.ts`（`PANEL_ACCOUNT_FIELDS` 一致，`PANEL_API_VERSION` 3→4）。 <!-- aidcp-cloud 2f0ef2a -->

## 4. aidcp-cloud — 协议 wire（Method A：不改）

- [~] 4.1 `comm/protocol.ts` **未改动**（Method A）：wire 字段保留 `groupChatCode`。物理 wire 改名（dual-declare `contactInfo?`+`groupChatCode?`）下沉 Wave4，需 edge/cloud 同 commit 逐字同源 + dual-read，属 §7 热点、另起协调。 <!-- 偏离：Method A，protocol.ts 零改动 -->

## 5. aidcp-cloud — 测试（Wave1/2 关卡）

- [x] 5.1 `test/feishu-commands.test.ts`：`--contact` 用例（旧 `group:on` 并入昵称走诚实失败）。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 5.2 account-store/comment-scheduler(+targeted)/compose-approve/comment-task-runner/targeted-comment-runner/panel-curated-actions/content-scheduler/content-schedule-store 测试改名。 <!-- aidcp-cloud 2f0ef2a -->
- [x] 5.3 关卡：test:acceptance 47/47、test 1655/1655、typecheck 全绿（AC-PROTO 因 protocol.ts 零改动天然绿）。 <!-- aidcp-cloud 2f0ef2a -->

## 6. aidcp-edge — 执行内部改名（Wave3；wire Method A）

- [~] 6.1 `comm/protocol.ts` **未改动**（Method A，与 cloud 一致）。 <!-- 偏离：Method A -->
- [x] 6.2 `browse/browse-session.ts`：`executeComment` 参数 `contactInfo`、日志/注释改名；**仍读 `payload.groupChatCode`**（wire 键未改，无需 dual-read）。 <!-- aidcp-edge 7699be8 -->
- [x] 6.3 `scripts/comment-verbatim-probe.ts` 文案（`--contact`/联系方式）。 <!-- aidcp-edge 7699be8 -->
- [x] 6.4 关卡：test 788/788、test:acceptance 16/16、typecheck 绿；protocol.ts diff 空。 <!-- aidcp-edge 7699be8 -->

## 7. aidcp-console — DTO + UI + 文案（Wave2，与 cloud panel 同波）

- [x] 7.1 `types/api.ts`：`contactInfo`/`hasContactInfo`/`contactComment*`。 <!-- aidcp-console 49d4203 -->
- [x] 7.2 `components/AccountsTable.tsx`：列「联系方式」、`onEditContact`、局部态、`多账号同联系方式`、placeholder/title。 <!-- aidcp-console 49d4203 -->
- [x] 7.3 `pages/AccountsPage.tsx`：路由 `/contact-info`、`contactInfo`、文案、接线。 <!-- aidcp-console 49d4203 -->
- [x] 7.4 `api/errorText.ts`：`invalid_contact_info`/`no_contact_info`。 <!-- aidcp-console 49d4203 -->
- [x] 7.5 `pages/ContentSchedulePage.tsx`：`sharedContactInfoWarning`（**保留共用放行+提示**）、`no_contact_info`、列/键/文案。 <!-- aidcp-console 49d4203 -->
- [x] 7.6 `pages/CuratedContentPage.tsx`：`contact_info_missing`、`withContact`、`commentKind 'contact'`、文案。 <!-- aidcp-console 49d4203 -->

## 8. aidcp-console — 测试（Wave2 关卡）

- [x] 8.1 FacebookSearchConfig/CuratedContentPage/ContentSchedulePage/errorText 测试 fixture 与断言改名。 <!-- aidcp-console 49d4203 -->
- [x] 8.2 关卡：typecheck 绿、test 69 passed / 1 skipped。 <!-- aidcp-console 49d4203 -->

## 9. aidcp（控制仓）— 文档 + 部署 + 归档

- [x] 9.1 `docs/protocol.md`：为 `interaction.comment` 补记注入字段（wire 名 `groupChatCode`、语义=联系方式；Method A 说明）。 <!-- aidcp <sha> -->
- [ ] 9.2 部署 Wave1：cloud 到 dev。**含手动协调迁移**：迁移前库备份 → 手动跑 `migrations/0036` → deploy 新构建 → restart → healthcheck（8787 + 飞书长连 + PG select 1 + `accounts.contact_info` 存在且数据保全）→ 失败回滚。绝不碰同机 isales。**⚠️ DB 列改名为高风险操作、部署前先探 ECS 现状。**
- [ ] 9.3 部署 Wave2：cloud panel + console **同波**（先 cloud、console 紧随；console rsync 绝不 --delete）。
- [ ] 9.4 部署 Wave3：edge 发版、运营机 pull（wire 键未改，旧 edge 与新 cloud 天然兼容，非阻塞）。
- [ ] 9.5 Wave4 收尾（另起 change）：物理 wire 改名（dual-declare + dual-read + edge/cloud 同波）。
- [x] 9.6 真机验收项登记 `docs/real-machine-acceptance-backlog.md`。 <!-- aidcp <sha> -->
- [ ] 9.7 部署+验证后回写勾选 + `openspec validate --strict` → archive。
