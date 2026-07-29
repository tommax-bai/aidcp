## 0. 准入与三个岔口的裁决（**未完成前不写任何代码**）

- [x] 0.1 控制仓 `./scripts/task-preflight` 通过；按 CLAUDE §7 为 cloud / kernel / transport / api /
  automation / content 各开 `../<repo>.wt/split-cloud-automation-production-runtime` worktree
  （控制仓在 `main` 上直接写本 change 目录，不切分支）。
  <!-- 2026-07-29 六个 worktree 已建，分支名 codex/split-cloud-automation-production-runtime，
       均自各仓 origin/master 切出；四仓 preflight 全绿。 -->
- [x] 0.2 重跑 `./scripts/sync-split-repos --ref origin/master --tests`，确认除组装根外零差异；
  把实测 HEAD 回写 design.md §0，**不要沿用文档里的快照**。
  <!-- aidcp-kernel d7153b3 / aidcp-transport 6cd3339 / aidcp-api 02396d8 /
       aidcp-automation 71e5299 / aidcp-content d72d653，源 aidcp-cloud@babdd84。
       cloud 期间前进 4 提交带来 4 个文件漂移，已 --apply --tests 同步；kernel 契约变更
       连带四仓 pin 快进（见 design.md §0 那段 pin 纪律）。同步后各仓 typecheck 0、
       测试 57/470/1841(+3 skip)/455 全绿。复跑对账仅剩组装根差异（按设计从不同步）。 -->
- [x] 0.2a 六仓 worktree 装依赖（`npm install --userconfig /dev/null`，绕内网 registry 对
  `@types` 域的劫持）。
  <!-- 2026-07-29 cloud / kernel / transport / api / automation / content 六个 worktree 各自独立装，
       不共享 node_modules 软链（CLAUDE §7）。 -->
- [ ] 0.3 逐条重放 12 条 blocker 的 evidence（`aidcp-cloud/boundaries/composition-root-independent-blockers.json`
  按 `file#符号` 定位），确认每条今天仍成立；不成立的当场记下并说明为何。
- [x] 0.4 **岔口 A 拍板**：模型调用出口归属。
  <!-- 2026-07-29 用户裁定 A1：提进 aidcp-transport，三家各自 new，密钥各自从 env 读。
       理由＝符合 transport 准入（三家都可能调用 + 不含任何属主表 SQL），且热路径不加内网跳。 -->
- [x] 0.5 **岔口 B 拍板**：四个内容属主角色工厂归属。
  <!-- 2026-07-29 用户裁定 B1：四个角色类改判归 automation，写 content 表走 §3 写口。
       理由＝与 §10.7 发帖调度器同形，端口包不了工厂函数。
       尾巴未决：curated_note_evaluator 的可选 textCardTranscriber 依赖仍需在实施时一并处置，
       见 0.5a。 -->
- [ ] 0.5a 处置 `curated_note_evaluator` 的**可选** `textCardTranscriber`（content 属主视觉行为类，
  旗标默认关）：一并改判、或显式走 content 调用口。**不许默默不传**——可选实参缺席不报错。
- [ ] 0.6 **岔口 C 落实**：四个 content 属主存储写走 content 内部 HTTP 写口，在既有
  `AIDCP_CONTENT_PORT` 监听上扩，不新造监听。
- [ ] 0.7 落实 B1 的归属改判：先改控制仓 `docs/cloud-service-decomposition-proposal.md` §4.x
  （**归属的唯一事实源**），再手工 Edit 增量追加 `boundaries/ownership-rules.json`，
  最后 `npm run boundaries:refresh` 生成派生物；MUST NOT 直接手改生成物，
  MUST NOT 脚本整体重序列化规则表（CLAUDE §8.2）。
- [ ] 0.8 落实 A1：模型出口进 `aidcp-transport`。核对准入判据实跑一遍
  （`test/acceptance/module-boundary.test.ts` 的真正则，别凭记忆用「四条硬禁」），
  再按 kernel → transport → 三个业务仓的顺序快进 pin。

## 1. 四条运营指令通道（api 飞书入站 → automation 处理器）

- [ ] 1.1 `aidcp-kernel`：为四条指令定义窄接口与纯类型（请求 / 结果 / 具名失败原因）；不放行为类。
- [ ] 1.2 `aidcp-transport`：四条指令的「服务端注册 + 客户端 + 路径常量」三件套各一份，两端共用同一定义。
- [ ] 1.3 `aidcp-cloud`（事实源）：按 4a paired command 形态实现 route + receiver + api 侧 client；
  自由文本委托的**意图解析留在 automation**，api 侧 MUST NOT 自己拼 intent 调结构化入口。
- [ ] 1.4 `aidcp-cloud`：面板 dispatch 启停与飞书 `:dispatch` 收敛到**同一处理器、同一幂等键空间**，
  不开第二条 route。
- [ ] 1.5 契约测试：鉴权、版本 / target 校验、幂等重放、**结果未知**（传输失败不得改写领域结局）。
- [ ] 1.6 `aidcp-automation` / `aidcp-api`：同步派生并各自跑 typecheck + 聚焦测试。

## 2. content 属主 authority（automation → content）

- [ ] 2.1 `aidcp-content`：在既有内部 HTTP 服务端上注册四组写口——草稿精修 / FB 发帖素材 /
  概念池 / 精选库；每组独立注册，**一组初始化失败不得连带关闭其它组**（照 content 现有纪律）。
- [ ] 2.2 `aidcp-content`：token 用量记账写口。成本 MUST 由厂商账单反算，
  **禁止**在这一层硬编码价目表。
- [ ] 2.3 `aidcp-transport`：上述各口的三件套；`aidcp-kernel`：对应窄接口与失败原因联合类型。
- [ ] 2.4 `aidcp-automation`：新增 content 客户端组与 `AIDCP_CONTENT_URL` /
  `AIDCP_CONTENT_INTERNAL_TOKEN`（本仓第一次有 content 方向的出边）。
- [ ] 2.5 按岔口 A 的裁决落地模型调用出口；按岔口 B 的裁决落地四个角色工厂。
- [ ] 2.6 处置 `ReplyWorkflow` 的 content 属主具体类实参（与模型出口是两件事，单独处置）。
- [ ] 2.7 **传递性检查**：逐个构造点核对跨属主实参，**特别点名 optional 参数**
  （`PublishDispatcher` 的 `FacebookPublishMediaStore` 漏传不报错、三个写静默消失）。
  写一条会红的用例钉住它。
- [ ] 2.8 失败语义测试：写口只报真态行数；跨进程错误识别用**结构化守卫**，不用 `instanceof`。

## 3. automation 生产运行时真接线

- [ ] 3.1 `aidcp-automation`：在 `createAutomationCompositionRoot` 之上写真 `main()`——
  边-云 WebSocket 服务端、事件总线 + 角色调度器、风控单写者、各调度器与监测体。
- [ ] 3.2 启动 readiness gate 与 api 同形：同步读镜像首次装载完成、readiness 到 `ready` 之前
  **不放行业务入口**。
- [ ] 3.3 缺依赖时**停在具名原因上**：MUST NOT 用空数组 / `false` / 未绑定 / 代码默认放行。
  现在那个 fail-closed 壳守的东西，接线后必须仍然守得住——为此写回归用例。
- [ ] 3.4 持久任务仍按 `AIDCP_DEPLOY_ENV` 写 `execution_target`；target 缺失或非法时
  **不启动那个 worker**。
- [ ] 3.5 逐段对着 cloud `segCAutomation` 核对装配清单，确认没有「本进程里根本没有消费者」的对象
  被顺带 new 出来（判据：先问它的结果在本进程有没有去处）。
- [ ] 3.6 `aidcp-automation`：`npm run typecheck` + 全量 `npm test` 全绿。

## 4. 台账清零与门禁

- [ ] 4.1 `aidcp-automation/src/automation-composition-root.ts` 的
  `AUTOMATION_ROOT_READINESS_BLOCKERS` 逐条删除并同批下调；**只许下降，不留空位**。
- [ ] 4.2 `aidcp-cloud/boundaries/composition-root-independent-blockers.json` 同批收缩；
  两份 MUST 在同一批次内一致，任一单改都会让门禁与现实对不上。
- [ ] 4.3 台账清零后，`runAutomationEntry()` 从 fail-closed 切到真启动；
  切换本身要有测试证明「台账非空时仍然拒绝启动」这条闸没被删掉。
- [ ] 4.4 `npm run boundaries:refresh` + 逐条对账 `git diff boundaries/`；
  `crossBoundaryEdges` / `crossLayerReads` / `crossLayerWrites` / `exemptionEntries` 保持 0。
- [ ] 4.5 acceptance 全过：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权绝不静默发布）、
  `AC-RISK-*`（绝不自残）、`AC-OWN-*`、`AC-BOUND-*`、`AC-SPLIT-CROSSSEG`。

## 5. 派生对账、验收与收尾

- [ ] 5.1 `./scripts/sync-split-repos --ref <cloud sha> --apply --tests`；
  共享包 pin 按 kernel → transport → 三个业务仓的顺序快进，逐仓 `npm install` 刷 lock。
- [ ] 5.2 六仓各自 typecheck + 全量测试；**红项不得写成绿色**，逐条说明是既有还是本 change 新增。
- [ ] 5.3 **分层验收如实分开记**：loopback 契约测试证明 route/client；dev 单体部署只证明现网零回归；
  **三进程真跑属批次 5，本 change 不声称**。
- [ ] 5.4 dev 部署按 CLAUDE §5 安全序列（先备份 → rsync → restart → healthcheck → 失败即回滚）；
  **绝不碰同机 isales**。ol 一律等用户明确要求且走发布分支。
- [ ] 5.5 本地桩验不了的登记 `docs/real-machine-acceptance-backlog.md`（簇 60）。
- [ ] 5.6 回写 `docs/cloud-composition-root-trisection.md` §0.0 与
  `docs/cloud-split-next-session-handoff.md` §0.1/§0.2 的实测现状。
- [ ] 5.7 `openspec validate split-cloud-automation-production-runtime --strict` 通过后归档；
  删除 worktree 与分支。
