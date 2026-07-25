# 云端拆分 · 可执行分批计划

> 2026-07-23 定。前提(用户拍板):**时间第一、目标全拆完、dev 可暂时不可用、ol 必须一直活**(跑旧代码、与 dev 共库)。四路扫描后的可执行编排。配合 `cloud-decomposition-roadmap.md`(节奏)与 `cloud-service-decomposition-proposal.md`(架构)读。

## 剩余收口全集(扫描坐实)

剩余跨服务表写 = **恰好 12 处严格跨层直写 + 2 处方法触发型**,全部集中在**离场 + 保留清理**域,全部 ol 无感、可逆。其余 90 表归属已由边界门禁覆盖。

## 8 个批次

| 批 | 内容 | 并行 | ol 影响 | 依赖 |
|---|---|---|---|---|
| **A** | 配置/用量写路径收口(四类限频配置走窄链路;用量批量上报) | 是 | none | 进行中 |
| **B** | retention-sweeper 拆各服务本地 purge(risk_counters/interaction_feed/llm_token_usage) | 合一 | none | 无 |
| **C** | 飞书合同抽取(automation 不再直 import api 的 feishu):建 seam→5 文件 | 是 | none(真拆那刻生效) | 无 |
| **D** | automation↔content 60 条边收口(五簇) | 是 | none | 无 |
| **E** | 拆库前置加固(6 跨 owner 外键→应用层校验;7 硬编码 public.收口;扫描器补复合键) | 是 | none | 无 |
| **F** | 跨 owner 单事务拆 saga + 离场双向直写收口 | 串行 | none(不删结构) | 无 |
| **G** | CommandActions 收敛到 api 命令面(server.ts 热点) | 串行队列 | none | 无 |
| **H** | 风控写者锁跨库替代 | 串行 | none until 拆库 | 阶段2跑稳 |

## server.ts 单 writer 队列(唯一真串行瓶颈)

client_env 握手回写 + Batch G 命令面收敛 + 组合根拆分(Track1)都撞 `server.ts`(5529 行)。**专派一条队列独占它**,顺序:G 命令面 → Track1 拆三入口。

## 拆进程串行大链(前置全绿后)

1. 组合根 `server.ts` 拆 api/content/automation 三入口(先同仓三入口、可保持同进程跑通)
2. 进程间通信(进程内直连→内部 HTTP/持久事件)
3. 活状态归属固化(风控注册表 automation 独占、连接表、定时器归属)
4. `deploy-target` 多服务化(三目录/三 systemd/三 URL;红线:绝不碰同机 isales)
5. 逐进程出仓 + 建 aidcp-api/content/automation 三仓
6. **拆库(最后、不可逆、单独真机验收)**

## ol 硬线(会弄坏 ol,押最后 + 给兼容层)

删/改共享结构(DROP COLUMN/TABLE、改类型、加 NOT NULL)、拆 publish_log、物理拆独立库、删跨 owner 外键约束——**共库期一律不做**。拆库对 ol 兼容:旧库结构原样保留 + 逻辑复制/双写/视图,ol 连旧库跑到用户拍板迁移;逐表『双写→切读→观察→关旧写→删旧位』每张单独真机验收,绝不批量。

## 最快编排

第一波并行全铺:A(除 client_env)‖ B ‖ C ‖ D ‖ E ‖ F;server.ts 队列单独串行走 G→拆分。跑稳 enforce + deploy-target 多服务化后,走拆进程 6-track。最后拆库 + ol 兼容层。真串行瓶颈只有 server.ts 队列和拆库逐表验收两段。
