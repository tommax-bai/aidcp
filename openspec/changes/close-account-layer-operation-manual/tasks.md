# Tasks

> **本 change 零运行时行为变更**：新增的「平台留痕」维当前只被测试断言消费，不参与任何放行 / 拒绝判断。
> 因此**不需要出安装包、不需要真机验收**——它的全部价值在于阻止未来漂移，而未来的漂移是在代码里被拦住的。
> 代价：做没做**看不出来**。所以下面每一道新闸都 MUST 配一次变异验证，摘掉它必须有东西变红。

## 1. aidcp-edge — Cloud→Edge 描述符扩维

- [ ] 1.1 `src/client/operation-registry.ts` 的 `OperationDescriptor` 增加一维（建议名 `platformFootprint`，取值 `'account_visible' | 'none'`）。**仅加在 Cloud→Edge 那份**；`CLIENT_OPERATION_REGISTRY` 的 29 条不动，并在类型注释里写明为什么不加（无消费方的标注必然漂移）。
- [ ] 1.2 字段注释 MUST 写清三件事：判据（执行成功后平台上是否**直接**出现可归因到该账号的新对象）、按消息类型取最坏一档、**本维 MUST NOT 单独决定放行**（附反例：`edge.task.acquire` 不留痕却照拦）。
- [ ] 1.3 五个构造器（`automationControl` / `platformApiAutomation` / `browserLifecycle` / `pageAutomation` 及 `cloudData`）逐个决定默认值。**默认 MUST 落在 `account_visible` 一侧**，留痕为默认、不留痕需显式声明——漏声明的新命令因此天然进保守侧。
- [ ] 1.4 **逐条判定 46 条**。下表是起点**不是结论**，每条 MUST 回到协议注释与实现确认后再落笔；与下表不符的以实读为准并在本任务里写明理由。
  - **会留痕（`account_visible`）**：`interaction.like` / `interaction.collect` / `interaction.follow` / `interaction.comment` / `interaction.like_comment` / `group.join`（直接产生可归因新对象）；`publish.request` / `publish.command`（按最坏一档，见 design 决策四）；`interaction.reply.send`（真发出私信）；`plan.response`（v1 兼容路径可携带动作，取最坏一档）
  - **不留痕（`none`）**：`ping` / `pong` / `ui.snapshot` / `pacing.update` / `interaction.sync.ack` / `interaction.reply.result.ack` / `interaction.offboard.ack` / `interaction.runtime.controls`（控制与心跳）；`interaction.sync.request`（拉取）；`interaction.reply.reconcile`（协议注释：**绝不发起新平台写**）；`interaction.offboard.command`（撤权后清理本地加密会话，协议注释：结果**可重放**）；`interaction.auth.reopen` / `interaction.browser.control`（浏览器生命周期）；`session.end` / `browse.next` / `browse.scroll` / `note.open` / `note.close` / `search.execute` / `page.scroll` / `feed.refresh` / `navigation.back` / `note.browse_images` / `note.scroll_comments` / `profile.open` / `notification.open` / `notification.browse_comments` / `notification.browse_likes` / `notification.browse_follows` / `notification.back_home`（浏览，只产生隐式行为记录）；`identity.read_current` / `identity.read_self_profile`（读身份）；`edge.task.acquire` / `edge.task.release`（租约，属准入不属留痕）；`captcha.assist.capture` / `captcha.assist.click`（协助过验证码，不产生新对象）
- [ ] 1.5 有疑义的条目**逐条单独记**：写明疑点、最终判定、以及为什么判在保守侧。**MUST NOT 批量套用**——这张表判错一条的代价不对称（判成不留痕才是危险方向）。
- [ ] 1.6 `npm run typecheck` 通过（`satisfies` 会强制 46 条全部声明，漏一条即编译失败——这是本维第一道机械保证）。

## 2. aidcp-edge — 身份救援清单的机械约束

- [ ] 2.1 `test/client/operation-registry.test.ts`（或身份闸自己的用例）新增断言：`IDENTITY_RESCUE_OPERATIONS` 每一条在登记表中 MUST 声明为 `none`。失败时 MUST 点名具体条目，不只报「不一致」。
- [ ] 2.2 **只断言这一个方向**。MUST NOT 反过来断言「所有 `none` 命令都该在救援清单里」——反例现成（`edge.task.acquire` 是 `none` 但照拦）。在用例注释里把这条反例写下来，防止后来人"补全"成双向。
- [ ] 2.3 `identity-command-gate.ts` 的模块注释更新：救援清单那一段今天写的判据是「读 / 收尾 / 救援，且不在平台留痕」，现在其中「不在平台留痕」这半已由登记表机械保证，另半仍是人工策略——两半 MUST 在注释里分开写明，别让后来人以为整条都被闸守住了。
- [ ] 2.4 **变异验证**：把一条会留痕的命令（如 `interaction.comment`）加进救援清单 → 2.1 的断言 MUST 变红并点名它；同时确认**原有用例全绿**，坐实这条断言抓的是既有闸抓不到的那一类。
- [ ] 2.5 反向变异：把 `identity.read_current` 的留痕维改成 `account_visible` → 断言同样 MUST 变红（证明它比对的是登记表实际取值，不是一份写死的期望名单）。

## 3. aidcp-edge — 删掉第三份手抄清单（先验证，再删）

> 顺序不可颠倒：**先跑变异坐实两个方向都已被覆盖，再删**。验不出来就保留，并在用例注释里写明它守的是哪个方向。

- [ ] 3.1 变异（方向一）：摘掉 `edge-client.ts` 里某条命令的路由分支 → `align-cloud-edge-operation-registries` 落地的反向结构断言 MUST 变红并点名该条命令。
- [ ] 3.2 变异（方向二）：构造一条未登记的消息类型走到 `onMessage` → MUST 在入口 fail-closed 闸（`edge-client.ts:707`）被拒为 `operation_unclassified`，**且根本走不到路由分支**（`:738` 起）。坐实"源码路由了一条未登记命令"结构上不可能。
- [ ] 3.3 两条都验出来 ⇒ 删除 `routedActiveCommands`（46 条手抄）及仅依赖它的那条用例。删除说明写进用例文件注释：**为什么删是安全的**，指向 3.1 / 3.2 两条变异。
- [ ] 3.4 任一条没验出来 ⇒ **不删**，改为在用例注释里写明它实际守着哪个方向、以及 3.1/3.2 为什么没能覆盖。**MUST NOT 因为"设计里说能删"就删**。
- [ ] 3.5 `npm run test:acceptance` + `npm test` + `npm run typecheck` 全过。

## 4. aidcp-cloud — 同维度、逐字一致

- [ ] 4.1 `src/comm/operation-registry.ts` 的 `AutomationOperationDescriptor` 加同名同取值的维度，46 条取值与边缘**逐字相同**。构造器默认值同样落在 `account_visible` 一侧。
- [ ] 4.2 补验收用例：期望值**按引用**取自同类命令的描述符，不另抄字面量（沿用 `align-cloud-edge-operation-registries` 1.2 的做法）。
- [ ] 4.3 云端侧写清这一维**将来**的消费方是重放决策（重试上限 / 升级 / 绝不重放都在云端），本 change 不接线。注释 MUST 写明「尚未接线」，避免被后来人当成已生效的闸。
- [ ] 4.4 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。

## 5. aidcp（控制仓）— 对表闸扩到全部字段

- [ ] 5.1 `scripts/operation-registry-parity` 的比对从写死四字段改为**遍历描述符全部字段**；实现与输出措辞 MUST NOT 出现字段数量。
- [ ] 5.2 **变异验证**：只在一份副本里改某条命令的留痕维 → 闸 MUST 报出该键在该维上的差异。这一条是本任务的要害——扩维时最容易的失败正是「新维不参与比对，闸照报一致」。
- [ ] 5.3 确认闸仍保留既有的两条硬性行为：解析不了的条目判失败（绝不跳过）、参与方 < 2 判失败（绝不把「没得比」报成「比过了」）。
- [ ] 5.4 `scripts/README.md` 相应更新（那里若写了字段数量，一并去掉）。

## 6. 派生仓同步

- [ ] 6.1 `scripts/sync-split-repos --repo aidcp-automation` 先不带参数 dry-run 对账，确认唯一内容差异是登记表文件、零删除、kernel pin 已对齐 → 再 `--apply`。**MUST NOT 手工搬文件**（CLAUDE.md §8.1）。
- [ ] 6.2 `aidcp-automation` 侧 `npm run typecheck` 通过。
- [ ] 6.3 `scripts/operation-registry-parity` 三方一致。

## 7. 集成与部署

- [ ] 7.1 起手自检：控制仓在 `main`、四个 canonical checkout 都停在各自默认分支；edge / cloud 改动在各自 worktree 里做（本 change 的控制仓部分是 additive 目录，可在主 checkout 直接写）。
- [ ] 7.2 `scripts/land-change` 分别集成 edge / cloud（rebase → 全量测试 → 两道跨仓对表闸 → ff 推 master）。
- [ ] 7.3 部署 `dev`（走 CLAUDE.md §5 安全序列）。部署的是 `aidcp-automation` 派生服务；**MUST NOT 部署 `aidcp-cloud`**（§8.0）。
- [ ] 7.4 dev healthcheck：服务 active、8787 监听、写者锁 target=dev、`NRestarts=0`。
- [ ] 7.5 **不出安装包**（§6 长期授权：出包属用户显式触发）。**边缘侧改动不出包也不影响本 change 的价值**——新维零运行时消费，它守的是代码里的漂移，不是运营机上的行为。这一条 MUST 写清楚，避免被后来人当成"和另外两条 change 一样卡在出包上"。

## 8. 归档前置

- [ ] 8.1 **措辞对账（有前科，MUST NOT 靠归档顺序的运气）**：`align-cloud-edge-operation-registries` 的未归档 delta 写着「（类别 / 传输 / 身份 / 浏览器前置）四个字段 MUST 逐字相同」。两条 change 无论谁后归档，都会用自己那份措辞覆盖主 spec。归档前 MUST 确认最终并入 `openspec/specs/` 的措辞是「全部描述符字段」，不是写死数量的那一版。
- [ ] 8.2 若 `align-cloud-edge-operation-registries` 仍未归档：在它的 tasks.md 里就地登记这条耦合（写明本 change 名与要点），别让它归档时把措辞改回去。
- [ ] 8.3 `openspec validate close-account-layer-operation-manual --strict` 通过。
- [ ] 8.4 确认本 change **未产生任何新的归属表 / 归属清单文件**——`edge-addressing-layers` 的 MUST NOT 禁令对本 change 同样生效。本 change 的净效果 MUST 是手抄副本**减少**（四份 → 三份，或验证未通过时四份但每份都写明所守方向），MUST NOT 增加。

## 9. 实装期发现（不属于本 change，但别忘了登记）

- [ ] 9.0 **七条命令的类别是错的，救援清单是这个错误的补丁**（2026-08-06 用户指出后重查坐实，详见 design 决策一的「修正」节）：`identity.read_*`（翻译层）/ `captcha.assist.*`（环境层）/ `edge.task.acquire` `edge.task.release` `session.end`（执行权与编排）今天全登记为 `page_automation` / `page_account`，唯一共同点是**都需要浏览器**——分类被「怎么执行」污染了。**本 change 只止血不根治**（重新归类会改变身份闸实际拦什么，属行为变更）。根治 MUST 等「新增页面命令按什么维度编址」的规则立起来之后再做，否则改完仍无判据挡住下一次归错。本任务只负责**登记**，MUST NOT 在本 change 内动类别。
- [ ] 9.1 **视频号 API 写入路径不经过页面身份闸**：`interaction.reply.send`（真发私信）是 `platform_api_automation` / `bound_account`，而身份闸只拦 `page_account`。即身份未落定时页面动作被拦、API 私信照发。本 change 只登记不修（修它属行为变更，与「零运行时变更」的边界冲突）。**实装 1.4 时若确认该条判为 `account_visible`，这个缺口的严重度就被本 change 的数据坐实了**——届时 MUST 单独提 change 或登记 backlog，不得只留在本文件里。
