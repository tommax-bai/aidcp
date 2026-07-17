# Tasks — wechat-customer-api-contract

> 拥有的文件：`aidcp-cloud/src/interactions/interaction-customer-api.ts`、`aidcp-cloud/src/client-auth/client-user-store.ts`（仅 `withAuthorizedInteractionScope`）、新建契约测试与 fixture；控制仓 `docs/contracts/wechat-channels-interaction/v1/route-inventory.json`（新建）。
> 本 change 不触碰四个热点文件（两份 protocol.ts、command-bridge 动作映射、RoleName+role-catalog、risk-state-machine.ts）。
> 每条完成后按格式标注：`<!-- <repo> <commit-sha> 备注 -->`；**sha 必须取自已推送的提交**，不要编造。

## 1. 前提重验（必须先做）

- [ ] 1.1 在当前 aidcp-cloud master 上重验本 change 每条发现的前提是否仍成立（文件/行号可能已漂移，按行为而非行号核对）。任一条已被他人修复或已失去前提 → 在本文件如实登记「已失效 + 依据」并跳过，**绝不为了勾选而重复实装**。
  - H11 判据：`interaction-customer-api.ts` 的 route 里，`replies` + `PUT` 分支是否仍只匹配四段路径（无 `/draft` 段）；以五段路径打一次真 HTTP 是否仍返回「接口不存在。」。
  - M8 判据：`handle()` 是否仍把整个 `route(...)` 传给 `withAuthorizedInteractionScope`，使 `workflow.generate` 的模型调用落在 `BEGIN`/`COMMIT` 之间。
  - 契约测试判据：`test/interactions/customer-api.test.ts` 是否仍只覆盖列表/消息路径，草稿与 reply 三动作路径是否仍无用例。
- [ ] 1.2 核对 Electron 客户端仍发五段路径（`aidcp-edge/src/electron/main.cjs` 的 `interaction:draft:update`）。若客户端已被改成四段 → 说明有人从错误方向修了，**停手并在本文件登记**，不要顺着放宽云端。
- [ ] 1.3 确认 `wechat-channels-interaction-management` 的 client-customer-auth delta 是否已归档并入 `openspec/specs/client-customer-auth/spec.md`。若已并入且其中的路径要求与本 change 的 ADDED 需求重复 → 改写为 MODIFIED，避免归档时同名冲突。

## 2. aidcp — 冻结路径清单落成机器可读源

- [ ] 2.1 新建 `docs/contracts/wechat-channels-interaction/v1/route-inventory.json`，逐条录入 README Customer API 路径块的全部路径（method + path template），内容与 README 完全一致：list、detail、draft、approve、send、regenerate、ignore、escalate、sync、auth/reopen、browser、`DELETE /environments/:envKey`、`GET /offboarding/:offboardId`。这是纯粹的机器可读化，**不新增、不删除、不改写任何路径**。
- [ ] 2.2 在 README 的 Customer API 路径块旁注明：该清单为权威源，云端契约测试由其驱动，改路径必须先改清单。
- [ ] 2.3 订正台账：在 `openspec/changes/wechat-channels-interaction-management/tasks.md` 的任务 3.6 旁如实登记「客户 API 未完全按冻结契约实现：草稿路径漂移，已由 wechat-customer-api-contract 修复」，并按该 change 的标注格式写清依据。

## 3. aidcp-cloud — 契约测试（最高优先，先于修 bug 落地）

- [ ] 3.1 把 `route-inventory.json` 镜像进 `test/fixtures/wechat-channels-interaction/v1/customer-api/`（与既有 fixture 同一镜像方式）。
- [ ] 3.2 新建 `test/interactions/customer-api-contract.test.ts`：起真 HTTP server，构造一个 enabled、持权威归属、账号绑定匹配的客户 scope，按清单**逐条**真拼 URL 打真请求，断言每条返回契约规定的状态码与 envelope（`meta.requestId`/`meta.asOf` 存在）。
  - 测试 MUST 从清单文件读取路径，**不得在测试里另写一份路径字面量**——那正是漂移的根源。
  - `DELETE /environments/:envKey` 与 `GET /offboarding/:offboardId` 由 `client-auth-server` 路由，与 interaction API 不在同一 handler：这两条在 `test/client-auth-server.test.ts` 侧补覆盖，或在契约测试里组合两层 handler；**两种都行，但清单里的 13 条必须条条有人验**，缺一条即在本文件登记原因。
  - 断言判据用「返回契约规定状态码」，不要用「不等于 404」——授权失败也是 404，两者不可区分。
- [ ] 3.3 验证契约测试确实有效：在**不修实现**的前提下先跑一次，草稿路径用例必须失败（红）。红不了说明测试没打到真 URL 组装，回 3.2 重做。

## 4. aidcp-cloud — H11 草稿路径

- [ ] 4.1 `interaction-customer-api.ts`：草稿保存改为匹配五段 `parts[2]==='replies' && parts.length===5 && method==='PUT' && parts[4]==='draft'`，jobId 取 `parts[3]`。body 校验（`expectedVersion` + `finalText`）与既有一致，不放宽。
- [ ] 4.2 删除四段 PUT 分支。四段路径从未出现在任何契约里，保留别名等于把漂移固化。
- [ ] 4.3 跑 3.2 的契约测试，草稿用例转绿。

## 5. aidcp-cloud — M8 事务边界

- [ ] 5.1 `withAuthorizedInteractionScope` 拆成两段能力：一段「取 scope」（短事务：校验 enabled user + 权威 ownership + account binding，取回 accountId 后立即提交并释放连接）；一段「落库前复核」（短事务：同样的边界复核，供写入路径在提交前调用）。保留原方法给确实需要「鉴权+快速写」同事务的调用点，**不要为了统一而把已经正确的短路径也改掉**。
- [ ] 5.2 `handle()` 改为：先取 scope（短事务）→ 提交 → 在事务外调用 `route(...)`。授权失败的语义与状态码保持不变（disabled→401、其余→不可枚举 404）。
- [ ] 5.3 长耗时写入路径（至少 `workflow.generate` / `workflow.approve` / `workflow.edit`）：落库前调用 5.1 的复核，复核失败即拒绝写入并返回 404/409，不留部分写入。既有的 `expectedVersion` CAS 与 accountId/envKey 行级 scope 保留，不得削弱。
- [ ] 5.4 `isMissingTable(err) → not_authorized` 的处理：确认它是「功能未部署」还是「依赖暂时缺失」。若属后者 → 改为可重试的服务不可用（`retryable: true`），不得洗成 404「资源不存在」。若确属前者（该部署确实不启用互动功能）→ 在代码注释里写清依据并保留，同时在本文件登记结论。
- [ ] 5.5 数据库暂时不可用/连接取不到：确认走的是可重试错误路径而非 404。恢复即自动放行，不需要客户重新登录或人工介入。

## 6. 验证

- [ ] 6.1 `cd ../aidcp-cloud && npm run test:acceptance`
- [ ] 6.2 `cd ../aidcp-cloud && npm test`（契约测试全绿）
- [ ] 6.3 `cd ../aidcp-cloud && npm run typecheck`
- [ ] 6.4 并发事务行为（多 regenerate 不打满连接池、生成期间解绑不被阻塞）桩层验不了 → 转真机 backlog（`docs/real-machine-acceptance-backlog.md`），不要在单测里堆假验证。

## 7. 集成与收口

- [ ] 7.1 合回 aidcp-cloud master 前 `fetch` + rebase，重跑 `test:acceptance` + `typecheck`，ff 合并。push 遇 non-ff 一律 rebase 重来，绝不 force。
- [ ] 7.2 部署 dev（按 CLAUDE.md §5 安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。
- [ ] 7.3 真机验收项登记进 `docs/real-machine-acceptance-backlog.md`：客户端内改稿保存走通、改稿后批准走通、生成期间解绑不卡。
- [ ] 7.4 `openspec validate wechat-customer-api-contract --strict` 通过 → archive。
