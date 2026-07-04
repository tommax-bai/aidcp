# Design — console-cloud-panel-hardening

> 26 条治理项的关键设计决策与分波依赖。务实优先，按 YAGNI 砍超前抽象，留干净扩展缝。

## 分波依赖图（集成串行、组内可并行）

```
波1（高危止血，无前置）：
  #20 WS背压   #27 nginx-autoindex   #28 存在性校验   #29 requestId白名单
  #21 risk_counters索引+保留   #22 token_usage-purge接线   #23 interaction_feed索引
  #3  ECS-TTL（运维，与代码解耦）
波2（漂移，#4 解锁 #36；#6 收口机制）：
  #4 补评论赞列+修哨兵  →  #36 QuotasPage复用枚举
  #5 图片厂商（前后端同修）
  #6 DTO单源+diff测试（吸收 #4/#5 为其首批受保护面）
波3（前端体验，纯前端接线）：
  #30 QueryGate  +  #31 reason中文映射（同改 client，一起做）
  #17 URL深链   #18 队列快照+待审筛选
波4（质量债，#32 先行给安全网）：
  #32 审批CAS链测试  →  #34 useConfigMutation  →  #35 删/接 honest-write-result
  #33 WeekActiveGrid去重   #37 routes.ts合并
波5（登录会话，设计最重、影响鉴权全链）：
  #24 401提示+回原页+续签  +  #25 WS首帧鉴权+到期断连  +  #26 jti撤销+存储缝
  （三条同改鉴权链，串行一波做完，避免鉴权半态）
```

集成顺序：波1→波2→波3→波4→波5。每波在 worktree 内完成 + `npm test`/`typecheck` 绿后，`land-change` rebase 集成到 master，再进下一波。波5 单独最后，因其触及鉴权全链、回归面最大。

## 决策 1：登录续签与撤销（#3/#24/#25/#26）

**约束**：现状是无状态签名 JWT（`jwt.ts` 只验 alg/签名/exp，payload 无 jti），令牌存 localStorage，服务端无任何会话态。诉求是既「不踢活跃用户」又「泄露后能收回」，二者靠拉长 TTL 无法兼得。

**方案：短 TTL + 滑动续签 + 轻量撤销表**
- **续签**：TTL 保持短（默认仍可 1h，ECS 设 12h 只作过渡止血），新增 `POST /api/auth/refresh`：持有未过期令牌者可换发一枚新令牌（滑动窗口）。前端 client 在响应头看到「临近过期」（或收到软过期标记）时静默续签，活跃使用永不被踢。这样 TTL 可以调**短**（缩泄露窗口）而不牺牲体验——与 #3 的「拉长 TTL」张力就此解除，#3 降级为纯过渡运维。
- **撤销**：payload 加 `jti`（令牌唯一标识）。撤销 = 把 jti 记入服务端黑名单（内存 Set + 可选 PG 持久化跨重启）。`verifyJwt` 增查黑名单。「退出登录」调 `POST /api/auth/logout` 把当前 jti 拉黑。黑名单按 exp 自动过期清理（令牌自然过期后无需再记），故表恒小。
- **YAGNI 边界**：不引入 refresh-token/access-token 双令牌体系（单管理后台、用户数个位数，过度设计）。滑动续签用单令牌换发即可。httpOnly cookie 迁移留缝但本波不做（跨 8088/8090 端口 cookie 作用域需 Nginx 配合，独立评估）。
- **WS（#25）**：token 改**首帧**传（既有 spec 已允许「query 或首帧」，本 change 收紧为首帧），止血 Nginx 日志明文。连接建立后起一个定时器，到 token exp 时主动 `close(4401)`。前端辨识 4401 = 鉴权失效，停止无限重连、触发续签或跳登录（不再每 2s 盲重试）。

## 决策 2：DTO 单一来源 + 逐字 diff 测试（#6，含 #4/#5）

**约束**：两仓无共享 npm 包、无 monorepo，跨仓 TS 互不感知。不能引入构建期跨仓依赖（会破坏各自独立 CI/部署）。

**方案：cloud 为权威源 + 生成物快照 + console 侧 diff 断言**（对齐 protocol.ts 范式）
- cloud 面板 DTO 收敛到 `src/panel/dto/`（零运行时依赖的纯类型 + 一份运行时可序列化的「契约清单」：枚举值集合、字段名集合）。
- `/api/version` 扩展为暴露这份契约清单的**结构指纹**（枚举值 + 关键 DTO 字段名，已部分存在——它本就是漂移哨兵）。
- console 侧保留手抄镜像（无法消除跨仓边界），但哨兵测试从「副本对副本」改为**对 live `/api/version` 真值断言**：CI 里跑一个对拍——把 console 镜像的枚举/字段集合与 cloud 导出的契约指纹逐一比对（cloud 契约清单作为测试 fixture 由 cloud 导出、console 引入其快照）。漂移 = 测试红。
- **#4** 是这套机制的首个修复实例：补 console 公用枚举的评论赞动作 + 让哨兵对 7 动作真值断言（不再写死 6）。**#5** 是第二个：图片厂商字段纳入契约指纹。
- **YAGNI 边界**：不搭 codegen 流水线（openapi/protobuf）——面板 DTO 面虽在扩张但仍是十几个类型，人工镜像 + diff 测试的成本远低于引入 codegen 工具链。留「未来可换 codegen」的缝（DTO 集中在一处）。

## 决策 3：面板 WS 背压（#20，客户端侧 #19）

**约束**：面板 WS 与浏览编排**同进程**，慢客户端的无界缓冲会 OOM 连坐整个云端。

**方案：发送前查 `bufferedAmount` 阈值 + 慢客户端丢帧/断连 + 大载荷截断 + 零客户端短路**
- 每次广播前，对每个客户端查 `ws.bufferedAmount`：超阈值（如 1MB）则**跳过该帧**（面板是只读监控流，丢几帧可接受，优于 OOM）；持续超阈值（连续 N 帧）则 `close` 该慢客户端（它可重连拿最新态）。
- 单帧序列化后若超大小上限（如 256KB，`page.cards`/`note.detail` 大对象），**截断**为摘要帧（带「载荷过大已截断」标记），前端按需另拉。
- **零客户端短路**：`onAny` handler 进入即查「有无活跃面板订阅」，无则直接 return，不做序列化（省编排热路径 CPU）。
- 客户端 #19：panelWs 收帧改 `requestAnimationFrame`/微批合并后单次 setState；监控页事件列表限渲染条数（截断到最新 N 条 DOM，内存缓冲仍 500）；修「暂停」文案（现状暂停是丢帧，文案却说「已缓冲」）。

## 决策 4：DB 索引 + 数据保留（#21/#22/#23）

**约束**：schema 启动自建（`CREATE ... IF NOT EXISTS` 内嵌）+ migrations 同源双写，加索引须两处同步；ECS 生产库需上机执行或随重启自建。表与边云闭环、isales 同机，扫描成本外溢。

**方案：补 `occurred_at` 打头索引 + 三表每日保留清理**
- 索引：`risk_counters`、`interaction_feed` 各补一个 `(occurred_at)` 单列（或 `occurred_at DESC` 覆盖面板全局/时间窗查询）索引。llm_token_usage 视窗口查询计划补 `(occurred_at)`（其已有 account 打头索引服务不了纯时间窗）。建表内嵌 + 新 migration 文件双写。
- 保留：一个轻量周期任务（进程内 setInterval，日频），`risk_counters` 保留 7d（风控只回读 1d，7d 足够容错）、`interaction_feed` 保留一个合理窗（如 30d）、`llm_token_usage` 接线其**已存在但未调度**的 `purgeOlderThan`（保留窗对齐用量页 31d 上限，如 45d）。清理 DELETE 走新 occurred_at 索引，不全表。
- 修 `panel-server.ts:148` 「无全表扫描」的错误注释。
- **YAGNI 边界**：不引入分区表/TimescaleDB（数据量级日增数百到数千行，普通索引 + 保留窗完全够，分区是过度工程）。

## 决策 5：QueryGate 统一读错误呈现（#30，写侧 #31）

**约束**：现状 13 页里 11 页读失败呈现为「加载中」（永久骨架屏）或「暂无数据」（误导空态）——UI 层的静默假成功。

**方案：一个 `<QueryGate>` 包装组件 + client 保留 reason**
- `<QueryGate queries={[...]} loading={<Skeleton/>} error={(e,retry)=><ErrorPanel/>}>{children}</QueryGate>`：统一三态（loading/error/success），error 态呈现可读文案 + 重试按钮，杜绝「失败=永久 loading/空态」。10 个页面接入。
- client（#31）：解析错误响应时把 `body.error` + `body.reason` 合并进抛出的异常对象；配一份集中的 reason→中文映射（吸收内容页那份孤例映射，扩为全站共用）。排期页等不再上屏英文机器码。
- 两条同改 client 层，合并一波做。

## 决策 6：质量债重构次序（#32→#34/#35/#33/#37）

**约束**：写路径零测试，任何去重/抽 hook 无安全网。

**方案：先补测试再重构**
- **#32 先行**：审批 CAS 链（带 expectedVersion 编辑 + 带 contentVersion 授权发布 + 版本冲突/已决策拒因映射）补前端测试（mock HTTP 层，照 `DashboardPage.test.tsx` 模式）。cloud 侧 CAS 语义已实装，前端只需覆盖调用与拒因映射。`npm test` 进部署序列（README + 部署脚本）。
- 拿到安全网后做机械重构：**#34** 抽 `useConfigMutation`（收口「提交→失败诚实拒因→成功重取」20 处样板）；**#35** 删死代码 `honest-write-result.ts` 或让 useConfigMutation 真正用它（二选一：若其文案规范有价值则接线，否则删）；**#33** WeekActiveGrid 去重（QuotasPage 内嵌版改用共享组件）；**#37** 路由表 + 导航合并为 `routes.ts` 单源。
