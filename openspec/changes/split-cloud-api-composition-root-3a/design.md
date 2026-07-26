## Context

批次 2 已证明“属主服务端先在单体注册并部署验证，再交付消费端客户端”可以把契约正确性与三进程启动问题分开验收。批次 3/4 的对抗性复核又证明 api 与 automation 之间约有 40 条新契约，不能把它们当成批次 2 的机械复制；本 change 只处理 §10.4 的 3a 单向子集。

当前 `aidcp-api` 所需的 automation 事实分为两类：

- 请求路径可自然异步化的面板读写：automation 面板投影、四类配置、Facebook 群运营、群路由与告警勾销；
- 同步热路径或需要 api 事实回调的依赖：`weekActiveMask()`、边缘在场镜像、今日用量、实时事件等。

本 change 只收第一类。第二类分别留给 3b、4a、4b，避免把镜像、新鲜度和双向调用混进普通 HTTP 客户端。

四个限频 facade 的归属不是新岔口：`module-ownership.json` 与 facade 文件头均已定稿为 automation；kernel 只持 `PanelQuotaConfig` / `PanelPacingConfig` / `PanelSessionLimits` / `PanelResumeConfig` 的纯接口。

## Goals / Non-Goals

**Goals:**

- 让 automation 在内部 HTTP 面上提供 api 所需的第一批单向 owner 能力。
- 交付相同契约的客户端，保证未来 api 组装根不打开 automation 数据库连接。
- 保持面板现有 DTO、校验、写后真态回读、默认值与错误原因语义。
- 让每条远端失败在调用方可辨，绝不把计数/告警/互动读失败变成零或空成功。
- 先用真实 loopback HTTP 契约测试证明服务端 route/client 可达，再在单体 dev 证明现网零回归；单体 MUST NOT 为验收额外打开 automation listener。

**Non-Goals:**

- 不在本 change 重写或启动 `aidcp-api/src/server.ts`。
- 不处理风控命令、审批后触发、面板实时事件通道（3b）。
- 不处理 automation 反向读取 api 的发布台账、授权台账、人设等（4a）。
- 不处理 Facebook 群 scope 写所需的 api 账号花名册刷新；`importTargets` / `replaceTargetScopes` 与该 4a 端口配对落地。
- 不处理 `weekActiveMask()`、边缘在场、在途发布等同步镜像（4b）。
- 不改变 `group_route`、四类配置表或 facade 的属主，不增加数据库 migration。
- 不改协议 v2、Edge、Console DTO，不部署 OL。

## Decisions

### D1. 一条方向、五个契约簇

共享传输层新增五个独立成员：

1. `panel-automation-http.ts`：复用 `PanelAutomationReader` 六个异步只读方法。
2. `panel-config-http.ts`：复用四个 `Panel*Config` 接口，提供四组读写 route。
3. `facebook-group-ops-http.ts`：提供列表/筛选面/启停、账号进度、分配列表、陈旧分配回收，以及目录组装所需的 scope 计数和最近排期结果单条/批量读。`importTargets` / `replaceTargetScopes` 不在本成员内。
4. `group-route-http.ts`：按 `groupLabel` 读目标 chat、列出全部映射、upsert/清除映射。
5. `alert-resolution-http.ts`：按 `alertId` 勾销并返回真实更新行数。

分文件而不是一个“panel mega-port”，因为属主对象、失败语义和后续消费方不同；每个成员可独立注册、测试、版本对账。

### D2. 群路由端口按 `groupLabel`，不按 `accountId`

`accounts.group_label` 是 api 事实，`group_route` 是 automation 事实。automation route 若接收 `accountId` 并自行解析，会反向依赖 api；因此客户端先用 api 本地账号存储解析 `groupLabel`，再调用 `getRoute(groupLabel)`。`resolveAccountChatId` / `resolveCardChatId` 的默认群回落与 config-gap 日志仍留在 api 组合层。

备选方案“把 `group_route` 改判 api”会改变既有属主法条和写者，本 change 不采用。

### D3. 四类配置保留 facade 整体归 automation，面板读改为可等待

automation 继续构造现有四个 facade，HTTP route 直接调用 facade：

- 写前校验、整块拒绝与稳定 reason 不搬到 api；
- 写仍经 owner store 推进镜像版本；
- 成功响应仍是 owner 写后回读的真态。

四个 `getCatalog()` / `getView()` 当前是同步接口，但仅在异步面板请求处理器中使用。kernel 接口统一改为 `Promise<T>`，本地 facade 明确异步返回，面板处理器统一 `await`，远端客户端直接请求 owner。MUST NOT 使用 `T | Promise<T>` 兼容联合类型，否则调用方仍可能漏掉 `await` 并把 Promise 序列化成 `{}`。

不采用轮询镜像：这些读不是调度热路径，直接请求更简单，也保证可见配置来自当前 owner。owner 不可达时请求原样失败，MUST NOT 回代码默认或陈旧缓存。`sessionConfigStore.weekActiveMask()` 是真正的同步业务读，仍留 4b。

### D4. Facebook 账号自动化目录在 api 本地组装

目录工厂和 `facebook_group_join_automation_config` 属 api；automation 只提供自身事实：

- group target scope 单条/批量计数；
- group join audit 最近结果单条/批量读；
- 风控日配额继续复用既有 `risk-read`。

api 后续用本地 content schedule/config + 上述远端事实组装目录。automation MUST NOT 为生成目录反向调用 api，也不新增 `listAccountAutomationCatalog` mega-route。

`importTargets` / `replaceTargetScopes` 暂不开放。它们在 scope 标签未命中时会同步调用 `refreshAccountProjection()`，该刷新源是 api 的 `AccountRosterSourcePort.listAccountIdentities()`；把它们塞进 3a 会形成未声明的反向调用，删掉刷新则会改变“判否前再刷新一次”的既有语义。两条方法留到 4a 账号花名册端口落地后配对接入；交付记录 MUST 明说完整 FB 群运营面尚未就绪。

跨 JSON 边界的 `Map` MUST 转为稳定数组条目，客户端再重建 `Map`；Date 统一为 epoch ms，`undefined` 可选字段不得被补成伪值。

### D5. 失败语义由 owner route 原样保留

- 面板计数、批量风控态、告警和互动读失败：抛错；MUST NOT 回零/空数组冒充成功。
- 四类配置读失败：抛错；MUST NOT 回默认或陈旧值。写失败同样抛错；校验拒绝仍按既有 `{ok:false, reason}` 返回。
- Facebook 群写和群路由写失败：抛错；owner 的稳定业务拒绝/真实回读保持原形。
- 群路由未命中是合法 `null`；网络/owner 错误不是“未配置”，不得在 transport 内吞掉。默认群回落只由 api 的既有解析链决定并记录原因。
- 告警勾销返回真实 `0 | 1`；不得把 0 染成成功更新。

内部 HTTP 继续使用 `InternalHttpServer` / `InternalHttpClient` 的结构化错误与有界超时，不另加 retry、fallback 或兼容分支。

### D6. 服务端先行，客户端后发

先在 `aidcp-cloud` 事实源实现 transport、注册到 automation internal API，并以直接 loopback HTTP 契约测试覆盖全部方法和失败路径。现役 dev 是 `AIDCP_SERVICE` 未设的 monolith；按既有红线它不启动 automation internal listener，因此单体 dev 部署只验证 owner 初始化、既有业务零回归，并确认 8093 仍未开放。ECS loopback route 探针留到后续真正启动 automation 进程时执行，不把“源码已注册”写成“运行时已监听”。

服务端验证后，才把五个成员发布进 `aidcp-transport`，固定消费仓 pin 并验证客户端契约。`aidcp-api` 的 `main()` 尚未重写，因此本 change 不声称三进程互通或 api 已消费这些客户端。

### D7. 共享包准入与派生同步

契约实现先落 `aidcp-cloud/src/transport/`，加入 `TRANSPORT_MEMBERS` 后由 `scripts/sync-split-repos` 派生到 `aidcp-transport`。只有真实 import 五个成员的仓才 pin transport；automation 本地 owner 源码仍使用自己的 `src/transport`，不安装同一模块的第二份副本。

每个新成员必须有：

- route 与 client 同形测试；
- 非 2xx/坏载荷/业务拒绝不染绿测试；
- package exports/build layout 与消费方 pin 对账；
- `AC-BOUND-*` / `AC-OWN-*` 零新增边与跨属主 SQL。

## Risks / Trade-offs

- [方法面漏掉传递依赖，api main 后续仍编译不过或静默降级] → 以 survey verdict 逐方法对账；Facebook 目录明确补单条/批量 scope 与 audit 读，scope 写明确延期而非伪装完成；群路由按 api/automation 事实拆开。
- [配置读改成网络请求增加面板延迟] → 只发生于人工面板请求，不进入调度热路径；沿用内部 HTTP 超时，失败直接可见，不加缓存。
- [JSON 序列化破坏 `Map`、Date 或可选字段] → route 显式归一为数组/epoch，客户端显式重建，并做逐字段往返测试。
- [服务端与共享包版本漂移] → `TRANSPORT_MEMBERS` + 精确 pin + `sync-split-repos --check` 机械对账。
- [新增 route 被误当成三进程已可用] → 验收记录分开写“单体服务端 route”“客户端契约”“三进程运行”；后者明确不在本 change。
- [新增内部 route 扩大暴露面] → 继续只绑定 automation internal API 的既有 loopback/内部监听边界，不复用面板公网端口，不增加新外部端点。

## Migration Plan

1. 在事实源实现五个 transport 成员、owner adapter 与契约测试。
2. 在单体组装根的 automation internal API 注册 route；跑 focused tests、acceptance、全量测试和 typecheck。
3. 按 dev 门槛部署事实源，验证 monolith service/listener/health/log、现有 Feishu/PostgreSQL 与 schema gate，并确认未额外开放 automation internal listener；route/client 可达性取直接 HTTP 契约测试证据。
4. 加入 `TRANSPORT_MEMBERS`，同步 `aidcp-transport`，发布精确版本并更新真实消费仓 pin。
5. 运行共享包构建、客户端往返测试、七仓对账与严格 OpenSpec 校验；回写 §10 和 tasks 证据。

回滚时先回退 route 注册与共享包 pin 到上一已知版本；本 change 无 schema/data migration。若直接 HTTP 契约测试或现有单体健康检查失败，立即回滚事实源部署，不进入客户端发布。

## Open Questions

无。验证码协助、实时事件、今日用量、Facebook scope 写/账号花名册与所有同步镜像均已明确排除，后续按 3b/4a/4b 单独设计。
