# Tasks — loosen-group-comment-shared-code

## 1. aidcp-cloud — 放行共用群码 + 透传警告
- [x] `content-schedule-store.setAccount`：共用群码不再硬拒，置 `sharedGroupCodeWarning` 放行；`no_group_code` 仍硬拒；结果类型成功变体带 `sharedGroupCodeWarning?`、失败 union 去 `shared_group_code` <!-- aidcp-cloud 5d86b95 -->
- [x] `panel-server` PUT `/api/content-schedule/:id`：成功响应透传 `sharedGroupCodeWarning` <!-- aidcp-cloud 5d86b95 -->
- [x] `content-schedule-store.test`：群码闸改为「无码硬拒 / 共用放行+警告 / 异码无警告」；全量 `npm test` 1640 pass、`typecheck` 通过 <!-- aidcp-cloud 5d86b95 -->
- [x] deploy dev（backup + rsync clean snapshot + restart + healthcheck：8787/feishu/PG 均绿） <!-- 2026-07-09 deployed -->

## 2. aidcp-console — 放行 + 风险提示 toast
- [x] `ContentSchedulePage.patchAccount`：响应类型带 `sharedGroupCodeWarning?`；新增 `onSuccess` 弹防关联风险 `message.warning` <!-- aidcp-console 61b57e4 -->
- [x] `errorText`：去 `shared_group_code` 映射（已非 error）、保留 `no_group_code`；`errorText.test` 收敛为只断言 `no_group_code`；全量 `vitest` 69 pass、`typecheck` 通过 <!-- aidcp-console 61b57e4 -->
- [x] deploy dev（backup + clean-snapshot build + rsync no-delete + assets/backup 保留 + nginx 8088 healthcheck、bundle md5 一致） <!-- 2026-07-09 deployed -->

## 3. openspec specs delta（本控制仓）
- [x] `console-write-operations`：MODIFIED「内容排期群评字段写入与开启硬校验（一码一号）」——共用改放行+警告、无码仍硬拒
- [x] `content-schedule`：MODIFIED「本能力覆盖发帖、评论与群评，声明已知缺口」——一码一号从硬阻断改为「无码硬拒、共用放行+提示」
- [x] `group-chat-injection`：MODIFIED「注入仅经命令式评论任务机器…」——排期侧刹车列举里的「一码一号硬阻断」改为放松后语义

## 4. 收尾
- [ ] `openspec validate loosen-group-comment-shared-code --strict`
- [ ] archive（与 `generalize-contact-info-change` 协调；archive 撞并发 spec 合并则移回 active 重跑）
