# Tasks

> **⚡ 2026-08-06 事实源已翻转（`invert-split-fact-source` cutover，用户裁定不等在飞 change）**：
> `aidcp-cloud` 的 `src/` + `migrations/` 已冻结（task-preflight 会拦任何 cloud 侧源码改动），
> `sync-split-repos --apply` 已退役。**本 change 剩余的「cloud 侧」任务改为直接落对应派生仓**
> （aidcp-api / aidcp-automation / aidcp-content；逐文件属主查 `aidcp-cloud/boundaries/module-ownership.json`，
> 常见：`src/comm/**`、`src/orchestrator/**` → automation，`src/panel/**`、`src/client-auth/**` → api）。
> 已写但未推的 cloud src 改动请在派生仓重落，**勿再推 cloud**（推了会让全 fleet 任务准入变红）。
> 新迁移直接落属主仓 `migrations/`，编号取三仓并集的下一号。跨仓测试（整图/跨属主）落 cloud `test/`
> （它现在是纯集成测试仓，test/ 不冻结）。协议红线不变：edge ↔ aidcp-automation 两份 `src/comm/protocol.ts` 逐字一致。


> **本 change 零运行时行为变更**：新增的「平台留痕」维当前只被测试断言消费，不参与任何放行 / 拒绝判断。
> 因此**不需要出安装包、不需要真机验收**——它的全部价值在于阻止未来漂移，而未来的漂移是在代码里被拦住的。
> 代价：做没做**看不出来**。所以下面每一道新闸都 MUST 配一次变异验证，摘掉它必须有东西变红。

## 1. aidcp-edge — Cloud→Edge 描述符扩维

- [x] 1.1 `src/client/operation-registry.ts` 的 `OperationDescriptor` 增加一维（建议名 `platformFootprint`，取值 `'account_visible' | 'none'`）。**仅加在 Cloud→Edge 那份**；`CLIENT_OPERATION_REGISTRY` 的 29 条不动，并在类型注释里写明为什么不加（无消费方的标注必然漂移）。<!-- aidcp-edge 7f55bd1（分支 close-account-layer-operation-manual，待集成后由主 session 更新为 master sha）实现为新接口 CloudOperationDescriptor extends OperationDescriptor（含必填 platformFootprint），CLOUD 那份 satisfies 用它；CLIENT 29 条与其 OperationDescriptor 原样不动，不加的理由写在 CloudOperationDescriptor 的类型注释里 -->
- [x] 1.2 字段注释 MUST 写清三件事：判据（执行成功后平台上是否**直接**出现可归因到该账号的新对象）、按消息类型取最坏一档、**本维 MUST NOT 单独决定放行**（附反例：`edge.task.acquire` 不留痕却照拦）。<!-- aidcp-edge 7f55bd1 三件事都在 PlatformFootprint 的类型注释里，另加了「只算直接后果不算间接触发」的边界裁定（design 决策四） -->
- [x] 1.3 五个构造器（`automationControl` / `platformApiAutomation` / `browserLifecycle` / `pageAutomation` 及 `cloudData`）逐个决定默认值。**默认 MUST 落在 `account_visible` 一侧**，留痕为默认、不留痕需显式声明——漏声明的新命令因此天然进保守侧。<!-- aidcp-edge 7f55bd1 四个 Cloud→Edge 构造器都加了可选尾参 platformFootprint，默认 'account_visible'；cloudData 的裁定是**不带本维**（它只服务 CLIENT 那份，加一个无消费方的维正是本 change 反对的形态），注释已写明 -->
- [x] 1.4 **逐条判定 46 条**。下表是起点**不是结论**，每条 MUST 回到协议注释与实现确认后再落笔；与下表不符的以实读为准并在本任务里写明理由。<!-- aidcp-edge 7f55bd1 逐条对协议注释（protocol.ts MessageType 联合的逐行注释）与实现确认后落笔，**46 条最终判定与下表完全一致、零偏离**：account_visible 10 条（6 互动写 + publish.request/command + interaction.reply.send + plan.response），none 36 条。关键实读证据：plan.response 的 PlanStep.op 含 click/input、可承载点赞评论写手势（protocol.ts PlanStep 定义）⇒ 最坏一档成立；interaction.sync.request 在边缘落到 wechat-channels/connector.sync → request-descriptors.ts 全部同步端点 evidence='observed_read_only'（纯拉取，无平台写）⇒ none 成立；interaction.reply.reconcile 协议注释逐字「只核验既有 attempt，绝不发起新平台写」；interaction.offboard.command 清理的是边缘本地加密会话、result 注明可重放 -->
  - **会留痕（`account_visible`）**：`interaction.like` / `interaction.collect` / `interaction.follow` / `interaction.comment` / `interaction.like_comment` / `group.join`（直接产生可归因新对象）；`publish.request` / `publish.command`（按最坏一档，见 design 决策四）；`interaction.reply.send`（真发出私信）；`plan.response`（v1 兼容路径可携带动作，取最坏一档）
  - **不留痕（`none`）**：`ping` / `pong` / `ui.snapshot` / `pacing.update` / `interaction.sync.ack` / `interaction.reply.result.ack` / `interaction.offboard.ack` / `interaction.runtime.controls`（控制与心跳）；`interaction.sync.request`（拉取）；`interaction.reply.reconcile`（协议注释：**绝不发起新平台写**）；`interaction.offboard.command`（撤权后清理本地加密会话，协议注释：结果**可重放**）；`interaction.auth.reopen` / `interaction.browser.control`（浏览器生命周期）；`session.end` / `browse.next` / `browse.scroll` / `note.open` / `note.close` / `search.execute` / `page.scroll` / `feed.refresh` / `navigation.back` / `note.browse_images` / `note.scroll_comments` / `profile.open` / `notification.open` / `notification.browse_comments` / `notification.browse_likes` / `notification.browse_follows` / `notification.back_home`（浏览，只产生隐式行为记录）；`identity.read_current` / `identity.read_self_profile`（读身份）；`edge.task.acquire` / `edge.task.release`（租约，属准入不属留痕）；`captcha.assist.capture` / `captcha.assist.click`（协助过验证码，不产生新对象）
- [x] 1.5 有疑义的条目**逐条单独记**：写明疑点、最终判定、以及为什么判在保守侧。**MUST NOT 批量套用**——这张表判错一条的代价不对称（判成不留痕才是危险方向）。<!-- aidcp-edge 7f55bd1 存疑六条逐条记（判定依据也已写进登记表行注释）：
  ① publish.request——疑点：协议墓碑、生产无处理器，今天物理上留不了痕；判 account_visible（保守侧）：本表按消息类型语义编址，不因「今天恰好没接处理器」降档，且并行批次正在删它、集成时自然消失。
  ② plan.response——疑点：v1 兼容路径，现役主路径不用；判 account_visible（保守侧）：PlanStep.op 含 click/input，一条 plan 可承载点赞/评论写手势，最坏一档。
  ③ search.execute——疑点：平台会存搜索历史（账号自见）；判 none：判据是「平台上直接出现**可归因到该账号的新对象**」，账号自见的隐式行为记录不是新对象（与浏览类命令同一口径），且本维用途是重放决策——重发一次搜索无重复对外写入风险。
  ④ captcha.assist.click——疑点：它真的往页面里点（人工点位）；判 none：点位只作用于验证码浮层（协议注释「captcha 暂停期间唯一允许穿透的恢复指令」），解开阻断不产生该账号名下新对象；若误判此条为留痕，救援清单断言会把唯一自救通道标成危险命令，恰是反向错误。
  ⑤ interaction.sync.request——疑点：视频号拉私信/评论会不会顺带在平台侧标已读（对方可见）；实读 request-descriptors.ts：全部同步端点（postList/commentList/dmHistory/dmSessionInfo）evidence='observed_read_only'，无任何写端点参与 ⇒ 判 none 有实证，非猜测。
  ⑥ notification.browse_likes / browse_follows——疑点：「看一眼清未读」改变平台侧未读状态；判 none：清的是本账号自己的通知已读位，不产生可归因新对象。 -->
- [x] 1.6 `npm run typecheck` 通过（`satisfies` 会强制 46 条全部声明，漏一条即编译失败——这是本维第一道机械保证）。<!-- aidcp-edge 7f55bd1 typecheck 0 错误。注：因构造器带默认值，「漏一条即编译失败」的机械保证实际由「CloudOperationDescriptor.platformFootprint 必填 + satisfies」提供——手写内联对象漏字段即编译失败；经构造器的条目字段恒在、默认落保守侧 -->


## 2. aidcp-edge — 身份救援清单的机械约束

- [x] 2.1 `test/client/operation-registry.test.ts`（或身份闸自己的用例）新增断言：`IDENTITY_RESCUE_OPERATIONS` 每一条在登记表中 MUST 声明为 `none`。失败时 MUST 点名具体条目，不只报「不一致」。<!-- aidcp-edge 7f55bd1 断言落在 operation-registry.test.ts（deepEqual violations=[] 形式，失败消息点名具体条目）；IDENTITY_RESCUE_OPERATIONS 为此导出（导出注释写明仅供成员资格断言消费） -->
- [x] 2.2 **只断言这一个方向**。MUST NOT 反过来断言「所有 `none` 命令都该在救援清单里」——反例现成（`edge.task.acquire` 是 `none` 但照拦）。在用例注释里把这条反例写下来，防止后来人"补全"成双向。<!-- aidcp-edge 7f55bd1 用例注释含 ⚠️ 反例段（edge.task.acquire 准入判据） -->
- [x] 2.3 `identity-command-gate.ts` 的模块注释更新：救援清单那一段今天写的判据是「读 / 收尾 / 救援，且不在平台留痕」，现在其中「不在平台留痕」这半已由登记表机械保证，另半仍是人工策略——两半 MUST 在注释里分开写明，别让后来人以为整条都被闸守住了。<!-- aidcp-edge 7f55bd1 模块注释改为「判据是合取，两半保证方式不同」：①留痕半＝登记表+断言机械保证；②更难救半＝人工策略无闸，增删成员仍要人判 -->
- [x] 2.4 **变异验证**：把一条会留痕的命令（如 `interaction.comment`）加进救援清单 → 2.1 的断言 MUST 变红并点名它；同时确认**原有用例全绿**，坐实这条断言抓的是既有闸抓不到的那一类。<!-- 已验：interaction.comment 加进清单后跑全部 test/client（116 用例）——唯一红的就是 2.1 断言且点名 interaction.comment，其余 115 全绿（既有闸对这类错误零反应）。验后还原 -->
- [x] 2.5 反向变异：把 `identity.read_current` 的留痕维改成 `account_visible` → 断言同样 MUST 变红（证明它比对的是登记表实际取值，不是一份写死的期望名单）。<!-- 已验：registry 侧 pageAutomation('none')→pageAutomation() 后断言变红并点名 identity.read_current（清单本身未动）⇒ 断言读的是登记表实际取值。验后还原 -->

## 3. aidcp-edge — 删掉第三份手抄清单（先验证，再删）

> 顺序不可颠倒：**先跑变异坐实两个方向都已被覆盖，再删**。验不出来就保留，并在用例注释里写明它守的是哪个方向。

- [x] 3.1 变异（方向一）：摘掉 `edge-client.ts` 里某条命令的路由分支 → `align-cloud-edge-operation-registries` 落地的反向结构断言 MUST 变红并点名该条命令。<!-- 已验：临时删掉 env.type === 'profile.open' 那条路由分支 → 反向结构断言当场红，消息点名 profile.open。验后 git checkout -- 还原 -->
- [x] 3.2 变异（方向二）：构造一条未登记的消息类型走到 `onMessage` → MUST 在入口 fail-closed 闸（`edge-client.ts:707`）被拒为 `operation_unclassified`，**且根本走不到路由分支**（`:738` 起）。坐实"源码路由了一条未登记命令"结构上不可能。<!-- 已验，用的是**最强形态**：把 note.open（源码里有路由分支）临时从登记表摘掉，向连好的 EdgeClient 投递 note.open——browseHandler 零调用、日志出现 operation_unclassified type=note.open ⇒ 入口闸位于路由分支之前坐实。另有常驻用例「unclassified active message fails closed before any handler」（future.command）守同一入口。临时用例与登记表变异验后删除/还原 -->
- [x] 3.3 两条都验出来 ⇒ 删除 `routedActiveCommands`（46 条手抄）及仅依赖它的那条用例。删除说明写进用例文件注释：**为什么删是安全的**，指向 3.1 / 3.2 两条变异。<!-- aidcp-edge 7f55bd1 已删（清单+仅依赖它的首条用例）；原位注释写明两条变异结论，并如实记下手抄清单唯一多守的场景（登记表被删一条、源码还路由）在运行时是响亮 fail-closed 拒绝而非静默错执行、且跨仓对表闸抓单侧删除 -->
- [x] 3.4 任一条没验出来 ⇒ **不删**，改为在用例注释里写明它实际守着哪个方向、以及 3.1/3.2 为什么没能覆盖。**MUST NOT 因为"设计里说能删"就删**。<!-- 不适用：两条都验出来了（见 3.1/3.2） -->
- [x] 3.5 `npm run test:acceptance` + `npm test` + `npm run typecheck` 全过。<!-- aidcp-edge 7f55bd1 acceptance 39/39；全量 3194 用例 3192 过 1 跳过（常规 gated）1 红——红的是 test/electron/interaction-workspace.test.ts「Cloud offline/stale 禁止 save/approve/send」（58s 超时形），与本 change 零交集，单独重跑该文件 48/48 全绿 ⇒ flaky；typecheck 0 错误 -->

## 4. aidcp-cloud — 同维度、逐字一致

- [x] 4.1 `src/comm/operation-registry.ts` 的 `AutomationOperationDescriptor` 加同名同取值的维度，46 条取值与边缘**逐字相同**。构造器默认值同样落在 `account_visible` 一侧。<!-- aidcp-cloud aeeb98c（分支 close-account-layer-operation-manual，待集成后由主 session 更新为 master sha）46 条取值逐字同边缘（对表闸 fixture 实跑对账 OK，见 5.2） -->
- [x] 4.2 补验收用例：期望值**按引用**取自同类命令的描述符，不另抄字面量（沿用 `align-cloud-edge-operation-registries` 1.2 的做法）。<!-- aidcp-cloud aeeb98c 新用例以 interaction.comment / note.close 两条为参照锚点、其余各族按引用比对同侧；用例注释写明绝对取值由边缘字面量用例+跨仓对表闸钉死、本用例守「分侧不塌」 -->
- [x] 4.3 云端侧写清这一维**将来**的消费方是重放决策（重试上限 / 升级 / 绝不重放都在云端），本 change 不接线。注释 MUST 写明「尚未接线」，避免被后来人当成已生效的闸。<!-- aidcp-cloud aeeb98c PlatformFootprint 类型注释明写「当前尚未接线…MUST NOT 被当成已生效的闸」 -->
- [x] 4.4 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。<!-- aidcp-cloud aeeb98c acceptance 198/198；全量 4318 用例 4307 过 0 红 11 跳过（全部为 AIDCP_E2E / 真库 PG gated 常规跳过）；typecheck 0 错误 -->

## 5. aidcp（控制仓）— 对表闸扩到全部字段

- [x] 5.1 `scripts/operation-registry-parity` 的比对从写死四字段改为**遍历描述符全部字段**；实现与输出措辞 MUST NOT 出现字段数量。<!-- 控制仓（由主 session 提交）：删 DESCRIPTOR_FIELDS 常量；跨仓按两侧实际声明字段的**并集**遍历（一侧独有字段报 <缺字段>）；同表内条目字段集不一致按解析失败拦（一条漏声明新维绝不静默）；解析器升级支持多参工厂/多实参调用（新维带来的 automationControl('bound_account','none') 形态），对 canonical master 的旧四字段格式仍向后兼容（实跑 OK 3 份各 46 条） -->
- [x] 5.2 **变异验证**：只在一份副本里改某条命令的留痕维 → 闸 MUST 报出该键在该维上的差异。这一条是本任务的要害——扩维时最容易的失败正是「新维不参与比对，闸照报一致」。<!-- 已验但须说明验法：脚本硬编码只读 canonical checkout，而 canonical master 还没有新维——为不假装验过，把脚本拷到 scratchpad 仅改 ROOT 指向 fixture（内容＝两个 worktree 的真实新维文件），比对逻辑一行未动。结果：①基线两份新维文件对账 OK；②仅在 cloud 侧把 session.end 的留痕维改成 account_visible → FAIL 点名「session.end 描述符不一致：platformFootprint: aidcp-edge='none' vs aidcp-cloud='account_visible'」exit 1（同时坐实工厂默认值解析）；③一侧整仓缺新维（canonical 旧格式 vs 新维）→ 逐键报 platformFootprint <缺字段>；④旧字段（identity）变异仍被抓。**canonical 路径的实跑留待集成后**：6.3 三方一致那步天然就是它 -->
- [x] 5.3 确认闸仍保留既有的两条硬性行为：解析不了的条目判失败（绝不跳过）、参与方 < 2 判失败（绝不把「没得比」报成「比过了」）。<!-- 已验（同 5.2 的 fixture 验法）：伪造 mysteryFactory(someVar) 条目 → FAIL「工厂实参解析不了（绝不跳过）」；只留一份副本 → FAIL「参与方少于两份，对账不成立」 -->
- [x] 5.4 `scripts/README.md` 相应更新（那里若写了字段数量，一并去掉）。<!-- 控制仓（由主 session 提交）：「描述符四字段」→「描述符全部字段（按实际声明的并集遍历；任一份漏字段即失败）」 -->

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

- [ ] 9.0 **七条命令的类别是错的，救援清单是这个错误的补丁**（2026-08-06 用户指出后重查坐实，详见 design 决策一的「修正」节）：`identity.read_*`（翻译层）/ `captcha.assist.*`（环境层）/ `edge.task.acquire` `edge.task.release` `session.end`（执行权与编排）今天全登记为 `page_automation` / `page_account`，唯一共同点是**都需要浏览器**——分类被「怎么执行」污染了。**本 change 只止血不根治**（重新归类会改变身份闸实际拦什么，属行为变更）。根治 MUST 等「新增页面命令按什么维度编址」的规则立起来之后再做，否则改完仍无判据挡住下一次归错。**该规则已立**：change `establish-edge-command-grammar`（判据 `docs/edge-command-grammar.md`），根治即其蓝图批 2（7 条改类 + 类别词汇扩容 + 身份闸摘救援补丁）。本任务只负责**登记**，MUST NOT 在本 change 内动类别。
- [ ] 9.1 **视频号 API 写入路径不经过页面身份闸**：`interaction.reply.send`（真发私信）是 `platform_api_automation` / `bound_account`，而身份闸只拦 `page_account`。即身份未落定时页面动作被拦、API 私信照发。本 change 只登记不修（修它属行为变更，与「零运行时变更」的边界冲突）。**实装 1.4 时若确认该条判为 `account_visible`，这个缺口的严重度就被本 change 的数据坐实了**——届时 MUST 单独提 change 或登记 backlog，不得只留在本文件里。<!-- 1.4 已确认：interaction.reply.send 判为 account_visible（46 条里 API 族唯一直写），且是全表唯一「留痕 + 不经页面身份闸」的组合——缺口严重度已被数据坐实。**登记动作（单独提 change 或落 backlog）留给主 session**，本条在此之前不得勾选 -->
