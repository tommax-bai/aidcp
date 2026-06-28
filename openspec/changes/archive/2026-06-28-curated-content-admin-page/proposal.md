## Why

精选创作灵感语料（`curated_content`，能力 `curated-inspiration-corpus`）目前是一个「自动沉淀 + 自动取材」的黑盒：内容按门槛自动纳入、发帖时自动召回，但**没有任何运营入口能看见里面沉淀了什么、也无法干预**。运营既无法核对「这账号到底攒了哪些素材、是否对题」，也无法清掉误纳入 / 没正文 / 涉他人隐私的脏数据。本 change 给这层语料补一个后台管理面：**能看、能管**。

## What Changes

> 范围 = Phase 1「看 + 管」。纯 aidcp-cloud 面板层 + aidcp-console 前端，**零 edge、零协议改动、不改 `curated_content` 表结构**。

- **新增「精选」管理页（console）**：顶部导航加一项、新路由 `/curated`。按账号**严格隔离**（账号必选、默认选第一个、绝不跨账号合并）的分页只读列表 + 详情抽屉。列展示标题 / 正文预览（默认折叠）/ 作者 / 类型（笔记·评论）/ 赞·藏·评计数（诚实区分「未抓到」与 0）/ 机器人点赞·收藏双标记 / 纳入原因 / 采集·更新时刻 / 来源外链（`rel=noopener`）。可按内容类型与纳入原因筛选（筛选项来自该账号实际出现的值、不硬编码）。
- **新增只读面板接口（cloud）**：按账号分页查列表、查筛选面（facets）。
- **新增两类管理操作（cloud + console）**：
  - **删单条**（误纳入 / 低质 / 隐私）：经拥有该表的进程内存储对象删，回真实删除行数；确认文案如实告知「删的是当前快照，之后再浏览到且仍达标会重新纳入；历史点赞 / 收藏标记不恢复」——不谎称永久移除。
  - **一键清「空正文壳行」**：按「正文为空」清理（**非**按纳入原因），回真实清理条数。
- **明确不做（推迟 Phase 2）**：门槛阈值后台可配热加载、纳入率 / 拒因统计、手动翻转双标记、全文搜索、人工置顶打标、永久压制（tombstone）。详见 design.md「非目标」。

> 设计要点（对抗评审坐实，写入 spec 作约束）：`curated_content` **只存「已纳入」行**——被拒的 `off_topic` / `below_resonance` 从不写库，故「按纳入原因批量清理」是坏设计（空正文壳行恰带「机器人已收藏」标记会被默认保护、反而只让删好素材），因此清理走「按正文为空」一条确定性谓词。

## Capabilities

### New Capabilities
- `panel-curated-content`: 精选创作灵感语料的后台管理面——按账号隔离的只读检索（分页列表、筛选面、详情）+ 受约束的治理写（删单条、清空正文壳行），全程诚实置空 / 诚实回真态 / 账号隔离防越权 / 缺存储优雅降级；删除语义为「清当前快照、不持久压制」并如实告知。

### Modified Capabilities
<!-- 无。本能力遵守既有 console-panel-api（面板 BFF 契约、JWT、账号隔离）与 console-write-operations（写只经拥有者对象、绝不 raw UPDATE、绝不乐观假成功）的 requirement，不改它们的 spec 行为，故不列 modified delta。curated-inspiration-corpus 的捕获/召回/消费契约本 change 也不动。 -->

## Impact

- **aidcp-cloud（面板层，主体之一）**
  - `src/cache/curated-content-store.ts`：新增只读 `listForPanel`（动态 WHERE + 参数化 LIMIT/OFFSET + `COUNT(*) OVER()` 取 total，按 `account_id` + 可选类型 / 原因过滤，缺表 `42P01` 降级）、`facetsForPanel`（按账号去重纳入原因 + 各自计数 + 携双标记的高权重行数 + 笔记 / 评论计数）、`deleteOne`（`WHERE id=$1 AND account_id=$2` 防越权）、`clearEmptyBody`（`WHERE account_id=$1 AND (body IS NULL OR body='')`）。不改建表 DDL、不加列。
  - `src/panel/types.ts`：新增精选内容行 DTO / 列表结果 / facets DTO；`PanelDeps` 加可选 `curatedContent?`（仿 `notificationContact?` 先例）。
  - `src/panel/panel-server.ts`：switch 追加 4 条路由——`GET /api/curated/contents`（读列表，照搬 `/api/notification/contacts` 范式：未注入→503、账号必填缺失→400、`numOf` 解析分页）、`GET /api/curated/facets`、`DELETE /api/curated/contents/:id`、`POST /api/curated/contents/clear-empty`；静态后缀路由排在 `:id` 动态匹配之前；每分支开头 `if(!deps.curatedContent){503}`。
  - `src/server.ts`：面板注入块把已实例化的 `curatedContentStore` 挂进 `curatedContent`（init 失败留 undefined 时面板自然 503）。
- **aidcp-console（前端，主体之一）**
  - `src/api/client.ts`：补 `apiDelete` 助手（当前仅 GET/POST/PUT）。
  - `src/types/api.ts`：手工镜像 cloud DTO（注释标注两处同步防漂移）。
  - `src/api/queries.ts`：新增按账号读列表 / 读 facets 的 query hook + 删除 / 清理 mutation（`onSuccess`→`invalidateQueries` 重取真态，非乐观）。
  - `src/pages/CuratedContentPage.tsx`：新建（套 `ContentPage` 表格 / 空态范式 + `QuotasPage`/`DispatchControl` 写反馈范式）；账号名走 `accountDisplayName`/`makeAccountNamer` 禁裸 ID。
  - `src/App.tsx` 加路由、`src/pages/AppShell.tsx` 导航加一项。改完需重 build dist 再覆盖部署。
- **DB（ECS PostgreSQL 库 `aidcp`）**：不新增表、不改 `curated_content` 结构、无 migration。仅新增只读查询与按 `account_id` 约束的 DELETE。
- **edge / 协议**：零改动。
- **红线**：账号隔离不串味（每条增删 SQL 强制带 `account_id`、读接口账号必填）、honest-write（删 0 条与删 1 条可区分、清理回真实 N，绝不乐观假成功）、诚实置空（计数 null≠0、缺链不渲染死链）、缺存储 503 不崩边-云闭环、写只经拥有 `curated_content` 表的存储对象（不在面板层 raw UPDATE/DELETE 绕过）。部署守 committed-only、本地并发 WIP 时外科式提交 / 单文件 scp。
