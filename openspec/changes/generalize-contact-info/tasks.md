# Tasks — generalize-contact-info

> 部署波次：**Wave1** = aidcp-cloud 内部+DB+命令（含 wire 双声明/dual-emit）→ **Wave2** = aidcp-cloud panel + aidcp-console（强制同波）→ **Wave3** = aidcp-edge（wire 双读，与 cloud 协调）→ **Wave4** = 收尾切换（下一版，删旧 wire 键）。热点文件（两份 protocol.ts）单写者、同 commit 逐字同源。

## 1. aidcp-cloud — 账号存储 + 注入链改名（Wave1）

- [ ] 1.1 `account-store.ts`：`setGroupChatInfo`/`getGroupChatInfo` → `setContactInfo`/`getContactInfo`（接口 + 实现 + 参数 + 局部）；类型 `SetGroupChatInfoResult` → `SetContactInfoResult`（含内部 `groupChatInfo` 字段 → `contactInfo`）；中文注释「群聊引流码」→「联系方式」。DB 列名此步先不改（见 §2）。
- [ ] 1.2 `feishu/commands.ts`：解析改为尾部 `--contact`（trailing-only、present=on、大小写不敏感），删除 `group:on/off` 识别（干净切换）；字段/局部 `injectGroup` → `injectContact`；HELP_TEXT 与派发点、JSDoc/注释同步为 `--contact` / 联系方式。
- [ ] 1.3 `comment-agent/comment-task-runner.ts`：`CommentTaskSteps` 接口 `compose(): {text, contactInfo}` / `post(noteId, text, contactInfo?)` + displayText 合并键改名（**漏改则 cloud typecheck 挂**）。
- [ ] 1.4 `comment-agent/comment-scheduler.ts`：`getContactInfo` 调用、`injectGroup` 字段 → `injectContact`、局部 `groupChatCode` → `contactInfo`、`withGroup` → `withContact`、reason `group_code_missing` → `contact_info_missing`、飞书文案与结果卡标签「定向带群评论」→「定向带联系方式评论」。
- [ ] 1.5 `comment-agent/compose-approve.ts`：`groupChatCode` 字段/依赖/返回键 → `contactInfo`；日志「群聊引流码待注入」→「联系方式待注入」。
- [ ] 1.6 `comment-agent/edge-steps.ts`：`post()` 内部参数 → `contactInfo`；wire 生产键按 §4 **dual-emit**（发 `{ contactInfo, groupChatCode }` 同值，过渡期）。
- [ ] 1.7 `server.ts`：接线 `injectGroup` → `injectContact`、`withGroup` → `withContact`、`getGroupChatInfo`/`setGroupChatInfo` 调用改名；**结果卡写死文案** `:2313` 那句「手动 /comment group:on 不受此限」→ `/comment --contact`，及 `:2299/2319/2327` 排期群评标题 → 带联系方式评论。

## 2. aidcp-cloud — DB 列物理改名（Wave1，协调单写迁移）

- [ ] 2.1 新建 `migrations/00XX_rename_group_chat_info_to_contact_info.sql`：schema-qualified 幂等 guard（`table_schema=current_schema()`，旧列存在且新列不存在才 `RENAME`）+ `SET LOCAL lock_timeout` + 末尾 `ADD COLUMN IF NOT EXISTS contact_info TEXT`；一并含群评列 `group_comment_enabled/daily_cap → contact_comment_enabled/daily_cap` 与 `group_comment_attempts` 表族的 guarded RENAME。**不改**历史 `0027_*.sql` 文件名。
- [ ] 2.2 `account-store.ts` 自愈 DDL 与迁移文件逐字同源：列声明改 `contact_info`、**删除旧 `ADD COLUMN group_chat_info` 行**、所有 in-method SQL 与 row-shape（SELECT/UPDATE/RETURNING）改列名。
- [ ] 2.3 `config/content-schedule-store.ts`：列读 `group_chat_info` → `contact_info`（含 `has_group_code` 别名 → `has_contact_info`、`no_group_code`/`shared_group_code` reason、`hasGroupCode` 派生字段 → `hasContactInfo`）；群评列/方法 `recordGroupCommentAttempt`/`countGroupAttemptsToday` 及其 SQL 改名。
- [ ] 2.4 `panel/panel-store.ts`：row-shape 列 + `ACCOUNT_SELECT` 的 `a.group_chat_info` → `a.contact_info`。

## 3. aidcp-cloud — 群评特性正名 + 精选 withGroup（Wave1/2）

- [ ] 3.1 `orchestrator/content-scheduler.ts`：`groupCommentEnabled/DailyCap` → `contactComment*`、`triggerGroupComment` → `triggerContactComment`、`groupAttemptsTodayCount` → `contactAttemptsTodayCount`、action 字面量 `'group_comment'` → `'contact_comment'`、注释同步。
- [ ] 3.2 `panel/panel-server.ts`：账号联系方式写路由 `/group-chat-info` → `/contact-info`（**过渡期新旧双认**）、`setContactInfo` 调用、请求/响应 `groupChatInfo` → `contactInfo`、reason `invalid_group_chat_info` → `invalid_contact_info`；内容排期写通道 `groupCommentEnabled/DailyCap` → `contactComment*` + reason `no_group_code`/`shared_group_code` → `no_contact_info`/`shared_contact_info`。
- [ ] 3.3 `panel/panel-server.ts` 精选评论 `withGroup` 接收端（`:1720/1754/1755`）→ `withContact`；`panel/types.ts` `CuratedActions.commentOnNote(..., withContact)` + 导入 `SetContactInfoResult` + `setContactInfo` 签名（**必须与 console `CuratedContentPage.tsx` 同波，否则静默不注入**）。
- [ ] 3.4 `panel/panel-store.ts` DTO 字段 `groupChatInfo` → `contactInfo`（注释同步）；`panel/version.ts` `PANEL_ACCOUNT_FIELDS` 的 `groupChatInfo` → `contactInfo`（**与 panel-store DTO 同 commit，`_AssertNever` 强制键一致**）。

## 4. aidcp-cloud — 协议 wire 双声明（Wave1，热点文件）

- [ ] 4.1 `comm/protocol.ts`：`InteractionCommentPayload` 同时声明 `contactInfo?` 与 `groupChatCode?`（都 optional），JSDoc 说明过渡；与 aidcp-edge `comm/protocol.ts` **同 commit 逐字同源**（AC-PROTO 穷举）。

## 5. aidcp-cloud — 测试（Wave1/2 关卡）

- [ ] 5.1 改并补 `test/feishu-commands.test.ts`：删旧 `group:on/off` 断言、加 `--contact` 用例（present=on、trailing-only、含空格昵称切分、旧写法并入昵称走诚实失败）。
- [ ] 5.2 改 `test/account-store.test.ts`（`setContactInfo`/`getContactInfo`/`{ok, contactInfo}`）、`comment-scheduler.test.ts`、`comment-scheduler-targeted.test.ts`（注意 `comment.payload.groupChatCode` 断言——dual-emit 下仍应发旧键、保持绿）、`compose-approve.test.ts`、`comment-task-runner.test.ts`、`targeted-comment-runner.test.ts`、`panel-curated-actions.test.ts`、`content-scheduler.test.ts`、`content-schedule-store.test.ts`。
- [ ] 5.3 关卡：`cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck`（AC-PROTO-* / fail-closed / AC-PUB 全过）。

## 6. aidcp-edge — 协议 + 执行 dual-read（Wave3，与 cloud 协调）

- [ ] 6.1 `comm/protocol.ts`：与 cloud 同 commit 逐字同源，双声明 `contactInfo?` + `groupChatCode?`。
- [ ] 6.2 `browse/browse-session.ts`：消费改 `payload.contactInfo ?? payload.groupChatCode`；`executeComment` 内部参数 `groupChatCode` → `contactInfo`；日志/注释「群聊引流码」→「联系方式」（`code` 局部保留）。
- [ ] 6.3 `scripts/comment-verbatim-probe.ts` 文案改名（低优先）。
- [ ] 6.4 关卡：`cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck`（含协议不漂移回归）。

## 7. aidcp-console — DTO + UI + 文案（Wave2，与 cloud panel 同波）

- [ ] 7.1 `types/api.ts`：`PanelAccount.groupChatInfo` → `contactInfo`（注释同步镜像 cloud panel-store）；`hasGroupCode` → `hasContactInfo`；`groupCommentEnabled/DailyCap` → `contactComment*`（含 PATCH-body 字段）。
- [ ] 7.2 `components/AccountsTable.tsx`：列标题「群聊引流」→「联系方式」、列 key/回调 `onEditGroupChat` → `onEditContact`、局部态 `draftChat`/`editingChatId`/`beginEditChat`/`commitChat`、多账号同码告警 `codeCounts`/`isDupCode`「多账号同码」文案、placeholder/title 全部改「联系方式」。
- [ ] 7.3 `pages/AccountsPage.tsx`：路由/命令 `/group-chat-info` → `/contact-info`、请求体与成功读键 `groupChatInfo` → `contactInfo`、toast 文案、prop 接线。
- [ ] 7.4 `api/errorText.ts`：`invalid_group_chat_info` → `invalid_contact_info`（过渡期可同时匹配新旧串）。
- [ ] 7.5 `pages/ContentSchedulePage.tsx`：`no_group_code`/`shared_group_code` → `no_contact_info`/`shared_contact_info`、「未配群码」→「未配联系方式」、「自动群评」列/`commitCap('group')`/`key:'group'` → contact、tooltip。
- [ ] 7.6 `pages/CuratedContentPage.tsx`：`group_code_missing` → `contact_info_missing`、POST `withGroup` → `withContact`、`commentKind 'group'` 与文案「带群评论」→「带联系方式评论」。

## 8. aidcp-console — 测试（Wave2 关卡）

- [ ] 8.1 改 `FacebookSearchConfig.test.tsx`、`CuratedContentPage.test.tsx`、`ContentSchedulePage.test.tsx` 中 `groupChatInfo`/`hasGroupCode`/`groupComment*`/「自动群评」fixture 与断言。
- [ ] 8.2 关卡：`cd ../aidcp-console && npm run typecheck && npm test`（AntD Popconfirm 测试坑照既有约定）。

## 9. aidcp（控制仓）— 文档 + 部署 + 归档

- [ ] 9.1 `docs/protocol.md`：为 `interaction.comment` **补记**注入字段（过渡期 `contactInfo`（新）+ `groupChatCode`（旧兼容）），头部计数与 §2 表同步（ADD，非 find/replace）。
- [ ] 9.2 部署 Wave1：cloud 到 dev（迁移前 `.env`/库备份 → rsync → restart → healthcheck：8787 监听 + 飞书长连 + PG select 1 + 迁移后 `contact_info` 列存在），失败回滚。绝不碰同机 isales。
- [ ] 9.3 部署 Wave2：cloud panel + console **同波**（先 cloud、console 紧随；console rsync 绝不 --delete、保留备份策略）。
- [ ] 9.4 部署 Wave3：edge 发版，运营机 pull；确认 dual-read 生效。
- [ ] 9.5 收尾切换 Wave4（下一版，另起任务）：确认运营机全升级 → cloud 只发 `contactInfo` → 再下一版删两份 protocol.ts 的 `groupChatCode` 与边缘旧键兜底 + `docs/protocol.md` 去旧字段。
- [ ] 9.6 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（`/comment <昵称> --contact` 真发带联系方式、缺配 fail-closed、后台联系方式列编辑回真态）。
- [ ] 9.7 回写本 tasks.md 勾选（`<!-- <repo> <sha> 备注 -->` + 部署后 `<!-- <date> deployed -->`）→ `openspec validate --strict` → archive。
