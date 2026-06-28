## 1. aidcp-cloud — 精选存储只读 / 删除方法

- [x] 1.1 `src/cache/curated-content-store.ts` 加只读 `listForPanel(accountId, { contentType?, admitReason?, limit, offset })`：动态 WHERE 强制 `account_id` + 可选 `content_type` 精确 + 可选 `admit_reason` 精确，`ORDER BY updated_at DESC`（命中既有 `idx_curated_content_account_updated`），参数化 LIMIT/OFFSET，`COUNT(*) OVER()` 同查询取 total（空结果集 total 兜底 0）；返回完整行映射为 camelCase、时间戳转 epoch ms、INT 用既有 `toNumOrNull` 诚实置空；`catch '42P01'`→`{items:[],total:0}` 降级。<!-- aidcp-cloud 新增 CuratedPanelRow/CuratedPanelListResult/CuratedFacets + listForPanel -->
- [x] 1.2 加只读 `facetsForPanel(accountId)`：按 `account_id` 过滤，`GROUP BY admit_reason` 取去重原因 + 各自 count + `SUM(CASE WHEN bot_liked OR bot_collected THEN 1 ELSE 0 END)` 高权重行数；另取笔记 / 评论各自计数；`'42P01'`→空降级。
- [x] 1.3 加 `deleteOne(accountId, id): number`：`DELETE FROM curated_content WHERE id=$1 AND account_id=$2`，返回真实 `rowCount`（0|1）。
- [x] 1.4 加 `clearEmptyBody(accountId): number`：`DELETE FROM curated_content WHERE account_id=$1 AND (body IS NULL OR body='')`，返回真实 `rowCount`；不动建表 DDL、不加列。
- [x] 1.5 store 单测：账号隔离（凭别账号 id 删→0）、honest 真态（删 1/删 0、清理回真实 N）、`COUNT(*) OVER()` 空结果 total=0、缺表 `42P01` 降级、`clearEmptyBody` 谓词。<!-- test/cache/curated-content-store.test.ts +7 用例 -->

## 2. aidcp-cloud — 面板 DTO / 依赖注入

- [x] 2.1 `src/panel/types.ts` 加精选内容行 DTO（复用 cache 导出的 CuratedPanelRow/CuratedPanelListResult/CuratedFacets）+ 新增 `PanelCuratedContent` 接口聚合 `listForPanel`/`facetsForPanel`/`deleteOne`/`clearEmptyBody`；`PanelDeps` 加可选 `curatedContent?`（仿 `notificationContact?`）。
- [x] 2.2 `src/server.ts` 面板注入块（`notificationContact` 旁）挂已实例化的 `curatedContentStore` 到 `curatedContent`（init 失败留 undefined 时面板自然 503）；不塞进 `PgPanelStore`。

## 3. aidcp-cloud — 面板路由

- [x] 3.1 `src/panel/panel-server.ts` 加 `GET /api/curated/contents`：照搬 `/api/notification/contacts` 范式——503 守卫→账号必填→`numOf` 解析 limit/offset→可选 contentType/admitReason→`listForPanel` 回 `{items,total}`。
- [x] 3.2 加 `GET /api/curated/facets`：账号必填、503 守卫、`facetsForPanel`。
- [x] 3.3 加 `DELETE /api/curated/contents/:id`：单段提取 id（非正整数→400 invalid_id）；账号从 query 取且**必填**（缺失→400 `account_required`）；`deleteOne` 回 `{deleted:0|1}`。
- [x] 3.4 加 `POST /api/curated/contents/clear-empty`：`readJsonBody`→账号必填→`clearEmptyBody` 回 `{deleted:N}`。**静态后缀（`/facets`、`/clear-empty`）排在 `:id` 动态匹配之前**。
- [x] 3.5 面板路由集成测试：账号缺失 400、未注入 503、删除账号隔离越权拒绝（别账号 id→deleted 0）、clear-empty 回真实 N、缺账号 400。<!-- test/panel-server.test.ts +1 集成 test -->

## 4. aidcp-cloud — 回归

- [x] 4.1 `npm run typecheck` 净、全量 test 875/876 绿（唯一失败 `AC-PUB-01` 为 Windows 路径分隔符既有环境问题 `\tmp\` vs `/tmp/`，与本改动无关，生产 Linux 正确）；安全红线未破。

## 5. aidcp-console — API 客户端 / 类型 / 数据 hook

- [x] 5.1 `src/api/client.ts` 补 `apiDelete<T>(path)` 助手（method `DELETE`，复用 request 的 Bearer / 401 兜底 / 非 2xx 解析）。
- [x] 5.2 `src/types/api.ts` 手工镜像 cloud 精选 DTO（`PanelCuratedContent` 行 + `CuratedContentList{items,total}` + `CuratedFacets`），注释标注「与 cloud 两处须同步防漂移」；缺字段 `string|null`、时间戳 epoch ms。
- [x] 5.3 `src/api/queries.ts` 加读 hook `useCuratedContents(accountId, filters)`（`enabled:!!accountId`、queryKey 含全部筛选参数）与 `useCuratedFacets(accountId)`（`enabled:!!accountId`）；删除/清理 mutation 落页面内（与 ContentPage 同范式）。

## 6. aidcp-console — 页面与接入

- [x] 6.1 新建 `src/pages/CuratedContentPage.tsx`：`page-stack` 堆 Alert(PII/保留上限) + 列表卡（extra 账号 Select 走 `accountDisplayName` 禁裸 ID、默认选第一个账号、无「全部账号」合并；类型 + 纳入原因(来自 facets) 筛选；Table 服务端分页；列含类型/标题/正文预览(ellipsis)/作者/赞藏评(null≠0)/双标记徽章/纳入原因/更新时刻/操作；Empty 区分 请选账号/加载中/服务不可用/暂无）+ 清理卡 + 详情 Drawer（全文、外链 `rel=noopener noreferrer`/「无链接」、topics、采集/首次/更新时刻）。
- [x] 6.2 行内删除：Popconfirm + danger，文案明示「仅清当前快照、之后达标会重新纳入、历史标记不恢复、删后不进发帖素材」；删 1→「已删除」、删 0→「该行已不存在」（honest 分支）。
- [x] 6.3 清空正文壳行：清理卡 danger 按钮 + Popconfirm（展示来自 facets 的 content_missing「约 N 条」预览），清理后 message 回真实 deleted N。
- [x] 6.4 `src/App.tsx` 加路由 `/curated` + import 页面；`src/pages/AppShell.tsx` BUSINESS 加 `{ key:'/curated', label:'精选', icon:<BulbOutlined/> }` + import 图标。
- [x] 6.5 `npm run typecheck` 净、`npm run build` 出 dist（index-Bbl414Fp.js）。

## 7. 部署与验收

- [x] 7.1 三仓外科式提交并 push：cloud `28f3bb1`、console `dfe4e41`（避开并发 WIP `QuotasPage.tsx`）、中控 `5834975`。
- [x] 7.2 cloud 部署 ECS（2026-06-28 18:15 重启）：因 master 上夹着别会话已提交未上线的 `f4a575d`（weekly-active-window 主动唤醒），改走**targeted scp 4 个源文件**（curated-content-store/panel-server/panel-types/server.ts，不碰 f4a575d 文件）避免误带；先备份（cloud-src.bak.20260628-181512.tar.gz + 逐文件 .bak）→scp→restart→healthcheck 全绿（active、8787+8090 监听、CuratedContentStore 已就绪、飞书长连已建、PG 就绪、无致命错误、/api/health 200、/api/curated/contents 无 token 401 证明路由接通）。
- [x] 7.3 console 部署（2026-06-28 18:20）：QuotasPage WIP 已被别会话提交进 HEAD `3d2ab68`（工作树转干净），从干净 HEAD 重 build（index-Bbl414Fp.js）→备份 console.bak.20260628-182002.tar.gz→scp index.html + 新 assets→验证 index.html 已切新包、包内含精选页标记、:80/:8088 HTTP 200。
- [ ] 7.4 真机验收：跑一段浏览使 `curated_content` 有数据后核——按账号看见笔记 + 评论两类、计数 null≠0、删单条回真态且账号隔离、清空正文壳行回真实 N、缺账号 400、缺存储 503、删后再观测达标会重新纳入（语义符合）。【用户侧】
- [ ] 7.5 `openspec validate` 已过；真机验后全部 task `[x]` 再 archive。
