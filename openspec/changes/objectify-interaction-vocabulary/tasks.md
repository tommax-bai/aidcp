# Tasks

> 词汇蓝图批 5。**迁移＝直接切换**：旧名从两份穷举表直接删，typecheck 即守卫；名表唯一权威＝design §1（9 条）。
> **关联键红线：只换键、值不动**（design §2）——任何触碰 `like`/`collect`/`follow`/`comment`/`comment_like` 值本身的 diff 都是走错了。
> **双仓锁步批**：照批 4 工序「各 worktree rebase → 全量测试 + gate:native → 成对 ff push → 立即 protocol-parity + operation-registry-parity + action-key-parity 复验全绿」。
> **同形异义不改**：design §7 清单（EventBus 事件名、IM 族、关联键值、能力串、nativeKind、渠道/任务族/LLM 词表）。
> **并行冲突预案**：`restore-native-facebook-residual-parity` / `blocking-overlay-dom-capture` 在飞；批 7 并行开发、集成串行且本批先落。

## 0. 前置核实（已完成，2026-08-07 本 session）

- [x] 0.1 两仓关联键消费面全量探查（交接前置第 1 件事）：cloud ~120 消费点 + 9 张 DB CHECK + kernel 两枚举坐实「值不动」决策；edge 三张裸 string 表 + `?? type` 回落点 + 两个绕 bridge 直发点 + bridge 互动零回归网缺口全部定位。
- [x] 0.2 「批 5 必须动值」预判修正为「只换键、值不动」（design §2 证据链）；FB 视频点赞对象事实（云端 0.25 概率决策 + 边缘 listMode 分流→改名字声明）坐实。
- [x] 0.3 规格引用分诊：2 个 capability 语义真变手写 delta；12 个引用旧名的走机械批（6.1）。

## 1. aidcp-edge（worktree `../aidcp-edge.wt/objectify-interaction-vocabulary`）

- [x] 1.1 `src/comm/protocol.ts`：`MessageType` 删 5 增 9；`PayloadMap` 同步（载荷接口共享保留、接口名不动）；文内 prose 引用同步。
- [x] 1.2 `src/client/operation-registry.ts`：5 → 9 条，描述符逐条继承（均 `pageAutomation()`），共 56 条。
- [x] 1.3 `src/client/edge-client.ts`：主动命令白名单 if-链 5 → 9 条（typecheck 不可见，逐条对名表核）。
- [x] 1.4 `src/client/command-diagnostics.ts`：`ACTIVE_COMMAND_TYPES` 5→9 / `FIXED_SUMMARIES` 换键 / `interaction.comment` 动态摘要分支换双平台新名。
- [x] 1.5 `src/native-page-engine/command-mapper.ts`：信封→kind 表 5→9 条（kind 仍 5 个不动）；`actionNames` 键 5→9、**值原样**；新增 like 对象解析（`facebook.video.like`→object=video 下传）；互动族禁 `?? type` 回落（显式表项断言见 1.10）。
- [x] 1.6 `src/native-page-engine/browse-session.ts`：删 `FACEBOOK_UNSUPPORTED_COMMANDS` Set 与消费点（design §4）。
- [x] 1.7 引擎：`command-manifest.json` 5 条目 `edgeTypes[]` 换 9 新名（kind 1:1 守恒、算术闸不变）；FB like 臂按下传对象分派 Reels/帖级执行器、对象不符诚实失败（`90-dispatch.js`）；JS 路由裸串动作名是值、不动；`node scripts/build-native-page-engine.mjs` 重建重钉 digest 五位点（**含生产常量 `native-page-engine-artifact.cjs:19`**）。
- [x] 1.8 UI 面：`renderer.js:2573-2577` 标签表 5→9 键；`ui-events.cjs:180` 评论正则换新名 + **顺手修批 4 遗留 4 条失效正则**（`:136/:140/:225/:229`）。
- [x] 1.9 退役但仍编译代码同步改名：`src/browse/browse-session.ts` 5 case、`src/facebook/facebook-session.ts`（5 case + `FB_COMMAND_ACTION_NAMES` 键 + `:617-618` 两 case 臂删除）、`src/facebook/comment-handler.ts`（case + `:135` 三元归一键）。
- [x] 1.10 测试：protocol-contract 穷举表 + 计数 103→107；operation-registry / manifest / digest 夹具；白名单路由回归断言 5→9 逐条；`actionNames` 互动族 9 条显式表项断言（新增，杀回落）；FB 表 parity 断言随键更新；`facebook.video.like` 对象分派 + 对象不符诚实失败用例；平台段闸拒收用例（`xiaohongshu.note.collect` 发 FB 会话）；ui-events 正则测试随改。
- [x] 1.11 `npm run typecheck` + `npm test` + `npm run test:acceptance` + `npm run gate:native` 全绿；变异验证按「先 commit 再变异→红→复原→复跑回绿」（变异项：删 actionNames 一条 / 删白名单一条 / 删 manifest 一条 edgeTypes）。

## 2. aidcp-automation（worktree `../aidcp-automation.wt/objectify-interaction-vocabulary`）

- [x] 2.1 `src/comm/protocol.ts`：与 edge 逐字一致（同 1.1）。
- [x] 2.2 `src/comm/operation-registry.ts`：同 1.2 共 56 条（头注计数同步）。
- [x] 2.3 `src/comm/command-bridge.ts`：互动 5 条从硬编码直返迁入 (action, platform[, object]) 穷举组合表；`satisfies` 钉 `MessageType`；不存在组合响亮 throw。
- [x] 2.4 `src/orchestrator/role-dispatcher.ts`：`EdgeCommand` 增可选 `likeObject`；Reels 随机点赞两路径（`:3914/:4034`）标 `video`；其余发送点零改动（关联键值不动）。
- [x] 2.5 `src/comm/handler.ts`：`LEGACY_ACTION_COMPLETION_ALIASES` 键 22→26（删 5 加 9）、**值不动**。
- [x] 2.6 直发点改名：`comment-agent/edge-steps.ts:352` → `xiaohongshu.note.comment`；`facebook-edge-steps.ts:419` → `facebook.note.comment`。
- [x] 2.7 测试：protocol-contract 计数 107；**bridge 互动组合逐条断言（新增，补零回归网缺口：9 合法组合 + 代表性非法组合 throw）**；别名表 26 键穷举断言（新增）；comment-agent 系列（comment-scheduler 约 40 处字面、edge-steps、facebook-edge-steps）、reels-random-like、rule/consumption-mode 等按新名更新——**其中 `action:'like'` 等值断言不动**；`npm run typecheck` + `npm test` + `npm run test:acceptance` 全绿；变异验证同 1.11 纪律（变异项：改别名表一个值 / 删 bridge 一个组合）。

## 3. 控制仓

- [x] 3.1 新脚本 `scripts/action-key-parity`（design §5）：三张关联键表语义对账；跑通并纳入本批复验序列。
- [x] 3.2 `docs/protocol.md`：§2 表 5 行 → 9 行、载荷节改名、bridge 映射段（`like→{platform}.note.like / facebook.video.like（对象维）` 等）、`interaction.follow` Reels 注记随新名。
- [x] 3.3 `docs/edge-command-grammar.md`：批 5 行标 ✅ + 落地名表 + 「关联键只换键值不动」的据实修正记录（含对交接预判的推翻理由）。

## 4. 集成（双仓锁步）

- [ ] 4.1 两 worktree 各自 rebase 最新 master → 全量测试 + gate:native 绿。
- [ ] 4.2 成对 ff push（`git push origin <branch>:master` ×2，中间不跑闸）→ 立即 `python3 scripts/protocol-parity` + `python3 scripts/operation-registry-parity`（各 56 条）+ `python3 scripts/action-key-parity` 复验全绿。
- [ ] 4.3 清 worktree。

## 5. 部署与切换窗口

- [ ] 5.1 部署 `dev`（§5 安全序列：备份 → rsync → restart → healthcheck）。**绝不碰 aidcp-cloud 单体与 isales。**
- [ ] 5.2 部署后观察日志：新名命令拒收计（旧客户端 fail-closed 属预期，车队本就停摆待出包）；无其他新增 error。
- [ ] 5.3 批 5 并入既有出包提请（打包动作用户显式触发）；真机验收项登记 `docs/real-machine-acceptance-backlog.md` 簇 153（登记前先 grep 最大簇号防撞）。

## 6. spec delta

- [ ] 6.1 手写 2 个语义 delta（native-facebook-behavior-parity、facebook-reels-browse）；机械改名 delta 覆盖 grep 实测 12 个 capability，逐条人审「机械 vs 语义」，同形异义按 design §7 红线。
- [ ] 6.2 归档前对当时最新 spec 文本重生成一遍（防并行 change delta 撞车），`openspec validate objectify-interaction-vocabulary --strict` 过。

## 7. 归档

- [ ] 7.1 全部 task 勾完 → validate --strict → archive；蓝图 §6.3 批 5 行终态回写。

## 8. 实装偏离与实录（2026-08-07）

<!-- edge 9fabff6 / automation d3e520e（worktree 提交，集成 sha 待 pair push 后回写） -->

- **落点**：edge worktree 提交 `9fabff6`（改名主提交，rebase 到 `dad4017` 之上）、automation `d3e520e`；
  控制仓 `18b91ddd`（立案）+ 本次 docs/脚本提交。协议 103→107、登记表 52→56、别名表 22→26；
  关联键三表 worktree 预对账 OK（mapper 36 / fb 25 / aliases 33，豁免 3）。
- **发现一（video 对象两个位置都合法，修正 design §3 的单臂表述）**：0.25 概率赞的对象是 **feed 里的
  视频帖**（`facebook_feed_video_probability_hit` 发送点），不是 Reels——「按对象拆不按位置拆」意味着
  引擎对象核对只有一个不可能组合：**note 对象 × Reels 面**（`object_mismatch_observed_reels`）；
  video 对象在列表面走精确目标帖级执行器、在 Reels 走视频执行器。云端两类 video 发送点
  （Reels 节奏赞 + feed 视频概率赞）标 `likeObject:'video'`，有界重试保留对象维（否则 Reels like
  重试会以缺省 note 撞诚实拒收）。facebook-reels-browse 的 delta 已按此修正。
- **发现二（退役 FB 会话的规范失败回执防线保留）**：批 4 给 xhs 深读/巡视名保留的「规范 action 名
  失败回执」case 臂，collect / comment-like 的 xiaohongshu.* 新名照此并入（防两份清单分叉的处理方式
  ＝并入既有防线而非再造清单）；`FACEBOOK_UNSUPPORTED_COMMANDS` Set 与其生产消费点删除，其测试职责
  移交 edge-client 平台段闸真实新名用例（`xiaohongshu.note.collect` / `xiaohongshu.comment.like` 发
  FB 会话 → `platform_mismatch`）+ Rust 能力账本纵深。
- **顺手清账（ui-events 批 4 遗留）**：4 条失效命令名正则与其唯一发射端（退役 xhs 会话的旧短形日志串）
  一并对齐到平台段名（`${env.type}` 形），测试随改——修正则不修发射端＝把「失效」换成另一种失效。
- **计划外发现（Rust 集成测试结构体字面量）**：`NoteInteractionParams` 加 `object` 字段后
  `native/page-engine/tests/` 四处字面量构造缺字段编译红（首轮 gate:native 抓住），补 `object: None`。
- **变异验证实录（先 commit 再变异，五项全红/复原全绿）**：①删 `actionNames` 一条→direct-routing
  穷举断言红；②删白名单一条→edge-client 路由断言红；③删 manifest 一条 edgeTypes→manifest 对账红；
  ④改别名表一个值→26 键穷举红；⑤删 bridge 一个组合→组合网断言红。
- **全量口径**：edge typecheck 0 / npm test 3225(0 fail) / acceptance 40 / gate:native OK
  （fmt+clippy+test，toolchain 1.97.1）；automation typecheck 0 / npm test 2412(0 fail) / acceptance 300。
  AC-PROTO-02 计数 103→107（两仓同步）。digest 重钉五位点
  `b5da30fbaf752614b977f899cf6fa38953a9c5c4e697813e058553c68da782a1`。
