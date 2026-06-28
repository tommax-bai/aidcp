## Context

精选语料 `curated_content`（能力 `curated-inspiration-corpus`，P1/P2/P2b 均已上线）是发帖创作的正向素材来源。一行 = 一条被纳入的内容（笔记或评论），字段含正文 / 作者 / 赞藏评计数 / 机器人点赞·收藏双标记 / 纳入原因 / 账号 / 时间。写入有三口（观测过门槛纳入、机器人自有动作标记 / 自动建行、确认点赞评论归档），召回有一口（按账号 + 类型加权选 top-K 注入发帖 prompt）。**当前没有任何运营读写入口**：`CuratedContentStore` 只有写、召回读、自动裁剪；`aidcp-console` 对其零引用。

关键现状约束（决定本设计形态，均已坐实代码）：
- **表只装「已纳入」行**：观测路径仅在过门槛时落库；被拒原因 `off_topic`/`below_resonance` 从不写库。表内真实纳入原因只有 `collect_floor` / `collect_ratio` / `bot_collect` / `bot_collect(content_missing)` / `confirmed_like[:reason]`。
- **空正文壳行带最高权重标记**：机器人收藏但同访问没观测到正文时，落 `body=''`、`admit_reason='bot_collect(content_missing)'`、`bot_collected=true`。它对创作零贡献（正文空），却带召回权重 2。
- **召回排序**：机器人收藏(2)+点赞(1) 优先，再收藏数，再更新时刻；删一行 = 该灵感不再进下次发帖素材。
- **准入不查历史**：删行后下次再浏览到同一篇且仍达标，会经 upsert 重新建行（新 id、`first_seen_at` 重置）——删除天然非持久。
- **存储可缺失**：`curatedContentStore` init 失败留 undefined，所有调用点先判存在。

面板层是进程内 BFF（HTTP `/api` + 浏览器 WS，独立端口），路由是单一巨型 switch 顺序 `if` 匹配，JWT 在公开端点之后统一拦截。已有 `/api/notification/contacts` 是「按账号隔离的分页只读」现成范本；写接口（session-limits/notification PUT）是「readJsonBody→逐字段校验→经拥有者对象写→回真态」现成范本。console 是 React+Vite+AntD 静态 SPA，`ContentPage` 是列表 / 表格 / 空态范本、`QuotasPage`/`DispatchControl` 是 honest-write 反馈范本。

## Goals / Non-Goals

**Goals:**
- 运营能按账号**看见**某账号精选语料里沉淀了什么（分页列表 + 详情 + 按类型 / 纳入原因筛选）。
- 运营能**清理**脏数据：删单条（误纳入 / 低质 / 隐私）、一键清空正文壳行。
- 全程守既有红线：账号隔离防越权、诚实置空（计数 null≠0、缺链不渲染死链）、honest-write（删 / 清回真实条数、可区分成功与无效）、写只经拥有 `curated_content` 表的存储对象、缺存储 503 不崩闭环。
- 改动是对既有成熟范式的整段克隆，零 edge、零协议、不改表结构、无 migration。

**Non-Goals（明确推迟 / 不做）:**
- **门槛阈值后台可配热加载**（`collectFloor`/`ratioMin`/`ratioLikeFloor`/`minTopicOverlap`）：改动面大、反馈有时延（只影响未来捕获）、当前数据少无从标定。留 Phase 2，走 `session_config_global`→`/api/session-limits` 配置链（仿 `engagement-ratio-config`）。
- **纳入率 / 拒因分布统计**：表不存被拒行，需另建埋点表 + 在准入处 best-effort 记一笔，且要积累浏览流量才有信号。留 Phase 2。
- **手动翻转机器人双标记**：语义上是篡改「机器人真实做过什么」，且即时改召回权重、顶进 / 挤出 top-K。删除已覆盖破坏性管理需求，故不做。
- **永久压制（tombstone）**：用户已拍板「删除够用就好」。若日后确有隐私永久移除需求，再加「已删除指纹」小表在准入处查重——会改 schema，届时单独决策。
- 全文搜索、人工置顶 / 打标、跨账号运维合并视图。

## Decisions

**D1. 作为新能力 `panel-curated-content`，不改既有能力的 requirement。**
它遵守 `console-panel-api`（BFF 契约、JWT、账号隔离）与 `console-write-operations`（写经拥有者对象、绝不 raw UPDATE、绝不乐观假成功）已有 requirement，不改其行为。对齐 `panel-interaction-feed` 的「一个面板数据域 = 一个能力」惯例。*备选*：改 `console-panel-api`/`console-write-operations`——否决，会把通用契约和具体数据域耦合。

**D2. 清理走「按正文为空」一条确定性谓词，不做「按纳入原因批量清理」。**
对抗评审坐实：最该清的空正文壳行恰是 `bot_collected=true`，任何「默认保护机器人动作行」的按原因清理都会保护垃圾、只放删好素材；而被拒原因根本不在表里，「清 off_topic 垃圾」无的放矢。`clearEmptyBody` 用 `WHERE account_id=$1 AND (body IS NULL OR body='')`，语义清晰、不误伤有正文的高权重行。*备选*：按原因清理 + 重定义保护谓词——否决，复杂且易误删。

**D3. 删除语义 = 清当前快照、不持久压制，UI 如实告知。**
不加 tombstone、不改 schema（守 Non-Goals）。删除 / 清理的确认文案 MUST 写明「删的是当前快照，之后再浏览到且仍达标会重新纳入；历史点赞 / 收藏标记不会恢复」。绝不在 UI 谎称「永久移除」。*备选*：加 tombstone 做真永久——推迟（改 schema + 准入加查重，超 Phase 1 范围）。

**D4. 账号隔离靠服务端强制，不靠前端。**
读接口账号必填、缺失→400 `account_required`，绝不默认某账号 / 绝不跨账号合并；删 / 清的 SQL **必须**把 `account_id` 写进 WHERE（`id` 是全局 SERIAL，只凭 id 可越权）。前端账号必选、默认选第一个（规避「空表像功能坏」陷阱）、`enabled:!!accountId`。

**D5. honest-write 非乐观，回真实条数并可区分。**
`deleteOne` 回真实 0/1：删 0 条 UI 显示「该行已不存在（可能已被淘汰或他人删除）」，非笼统「已删除」。`clearEmptyBody` 回真实 N（可能与 facets 预览不同，因机器人并发写），UI 报真实 N。前端 mutation `onSuccess`→`invalidateQueries` 重取真态，不本地乐观改。

**D6. 列表 total 与筛选面分别取，缺表优雅降级。**
`listForPanel` 用 `COUNT(*) OVER()` 同查询取 total（空结果集 total 兜底 0，防分页器误渲染）；`facetsForPanel` 单独取纳入原因去重 + 计数 + 携双标记高权重行数 + 笔记 / 评论计数，驱动筛选下拉与清理前影响预览（让运营预知「按正文为空可删多少」）。两者均 `account_id` 过滤、`42P01` 缺表→空降级。读列表命中既有索引 `idx_curated_content_account_updated (account_id, updated_at DESC)`，retentionMax=1000/账号 量级下性能充裕；类型 / 原因为内存过滤、不额外加索引。

**D7. PII 姿态。**
列表正文默认折叠（详情抽屉看全文），来源外链 `rel=noopener noreferrer`、缺链显「无链接」不渲染死链，页面仅 JWT 可达，详情抽屉头标注「第三方内容，仅供创作参考，保留上限 1000/账号」。

**D8. 路由命名与顺序。**
`GET /api/curated/contents`、`GET /api/curated/facets`、`DELETE /api/curated/contents/:id`、`POST /api/curated/contents/clear-empty`。静态后缀（`/facets`、`/clear-empty`）的 `if` 分支 MUST 排在 `:id` 动态匹配之前，否则被吞。store 以可选 dep 注入面板（仿 `notificationContact?`），缺失每分支开头回 503。

## Risks / Trade-offs

- **[删除非持久，隐私笔记可能复活]** → UI 确认文案如实告知；永久压制列为 Non-Goal、需要时再加 tombstone。不在 UI 谎称永久移除。
- **[空正文壳行带 `bot_collected` 高权重，清理会移除一条召回行]** → 壳行正文空、对创作 prompt 零贡献，清掉只是移除一条无用高权重行；确认文案告知「删行 = 从下次发帖素材移除」。
- **[`id` 全局 SERIAL，漏带 `account_id` 即越权]** → 读账号必填、删 / 清 SQL 强制 `account_id` 进 WHERE，并加跨账号拒绝的测试覆盖（凭别账号 id 删→返回 0）。
- **[DTO 两处手工镜像（cloud panel/types ↔ console types/api）易漂移]** → 两处注释标注「须同步」，字段对齐；与 `panel-interaction-feed` 等既有镜像同纪律。
- **[`confirmed_like:<reason>` 等带后缀的纳入原因撑大筛选下拉]** → facets 可返回归一化族（按 `:`/`(` 切）供分组；本期筛选按精确值，下拉项来自实际值不硬编码即可，不做前缀清理。
- **[存储 init 失败 / 缺表]** → 面板 503、前端空态区分「加载中 / 暂无 / 服务不可用」，绝不崩边-云闭环。
- **[console 静态 SPA 改完不 rebuild 不生效]** → 部署步骤含重 build dist + 覆盖 + 备份 + curl 验证。

## Migration Plan

1. cloud：加 store 只读 / 删除方法 + panel DTO / 路由 + server 注入；本地 `npm run typecheck` + `npm test`（含面板与 store 单测，覆盖账号隔离越权拒绝、honest 真态、缺表降级）。
2. console：加 DTO / `apiDelete` / hooks / 新页 / 路由 / 导航；`npm run typecheck` + `npm run build`。
3. 部署：cloud 走安全序列（备份→committed-only 同步→restart→healthcheck→失败回滚），本地若有并发 WIP 走外科式提交 / 单文件 scp、勿 tar 整树；console 重 build dist 后覆盖 `/opt/aidcp/console`、备份 + curl 验证。
4. 回滚：cloud 还原备份 tar + restart；console 还原 dist 备份。本 change 不改表结构 / 无 migration，DB 层无回滚负担。
5. 验收：真机跑一段浏览使 `curated_content` 有数据后，核对——按账号看见笔记 + 评论两类、计数 null≠0、删单条回真态且账号隔离、清空正文壳行回真实 N、缺账号 400、缺存储 503。

## Open Questions

- 导航 label 与图标定名：暂用「精选」+ 灯泡 / 星形图标，落地时可调。
- `clear-empty` 是否需要二次 danger 确认 + 显示「将清理 N 条」预览（来自 facets）：倾向需要，落地时按 `DispatchControl` 风格定。
