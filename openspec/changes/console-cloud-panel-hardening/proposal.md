## Why

管理后台（console）+ 云端面板层（cloud `src/panel/`）自 2026-06 MVP 上线后，累积了一批经 code review 坐实的治理项（26 条，逐条带 `文件:行` 证据）。它们不是孤立缺陷，而是四类**系统性**问题：

1. **登录会话先天设计缺陷**——定长有效期令牌 + 无续签 + 无撤销：到点必踢、踢了无提示、凭证泄露收不回，且令牌明文落进 Nginx 日志、WS 连接期不复检。
2. **双仓配置漂移**——console 手抄了一份 cloud 面板接口的全部类型，无共享源、无逐字比对测试；唯一的漂移哨兵是「副本对副本」恒绿的假防线。已出现两处现行漂移（评论赞动作列缺失、图片厂商界面显示错误）。
3. **越用越慢的性能炸弹**——面板只读查询打在为「按账号写」优化的表上，全部退化为全表扫描，三张表零保留策略无限增长；面板 WS 与浏览编排同进程、无背压，慢客户端能把整个云端拖到 OOM。这直接违背既有 spec 的「MUST NOT 全表扫描」与「非阻塞」红线。
4. **前端快速堆叠留下的错误呈现与复制债**——10 个页面读失败呈现成「还在加载」或「暂无数据」（UI 层的静默假成功，恰是本项目后端红线禁止的反模式）；写失败上屏英文机器码；审批关键写链零测试；周历网格/写样板/路由导航多处复制。

本 change 把这 26 条统一挂账、按依赖波次治理，主体是**加固既有 `console-panel-api` capability**（补足其已声明但被违背的非阻塞/防漂移/JWT 契约），并新增会话续签、DTO 单源、数据保留、诚实错误呈现四组要求。

## What Changes

按 7 组（对应四类根因）：

- **【登录会话】** cloud 面板层新增滑动续签端点 + 令牌可撤销机制（jti + 服务端黑名单）；WS 鉴权改首帧传 token（不走 query，止血 Nginx 日志泄露）+ 连接期到期主动断开；console 401 加「登录已过期」提示 + 记来源路径重登回原页 + 活跃自动续签；令牌存储预留 httpOnly 迁移缝。ECS 侧 `AIDCP_PANEL_JWT_TTL_SECONDS` 配置为 12h 止血（运维项，无代码）。
- **【配置漂移】** 抽零依赖 DTO 单一来源 + 两仓逐字 diff 测试（参照边云 protocol.ts「两份逐字一致 + typecheck 穷举 + 验收断言」范式）；补齐 console 公用枚举镜像的评论赞动作列 + 修复失灵的漂移哨兵测试（本地断言改为对 `/api/version` live 真值）；修图片厂商漂移（前端补厂商下拉与类型 + cloud 角色页视图读真实图片厂商而非文本默认）；QuotasPage 档位标签/配色复用公用枚举。
- **【监控性能】** cloud 面板 WS 加背压（发送前查 `bufferedAmount`，慢客户端丢帧/断连）+ 单帧大载荷截断 + 零客户端时跳过序列化；console 监控页帧批处理（合并到帧率）+ 限渲染条数（虚拟化或截断）+ 修「暂停」文案与行为不符。
- **【数据库】** cloud 给 `risk_counters` / `interaction_feed` 补 `occurred_at` 打头（或单列）索引消灭全表扫描；三张表挂每日保留清理（risk_counters 保留 7d，interaction_feed 保留窗，llm_token_usage 接上已存在但未接线的 purge）；修正「无全表扫描」的错误注释。
- **【接口安全】** cloud pause/resume/风控三端点加账号存在性校验（不存在返 404，杜绝幽灵账号「假成功」）；审批端点 requestId 加白名单格式校验（防路径穿越）；ECS Nginx 关闭 `/downloads/` 目录 autoindex。
- **【前端体验】** 抽 `<QueryGate>` 统一呈现读查询错误（10 页永久骨架屏/误导空态归一为可见错误 + 重试）；API client 保留 `body.reason` 并配集中中文映射；账号筛选进 URL querystring + 账号行站内深链；内容页队列卡展开管道快照 + 「只看待审」筛选。
- **【质量债】** 补 console 写路径测试（首推审批 CAS 链）+ npm test 进部署序列；WeekActiveGrid 两份拷贝去重；抽 `useConfigMutation` hook 收口约 20 处写样板；删除或接线 `honest-write-result.ts` 死代码；合并路由表 + 导航双清单为单一 `routes.ts`。

> 非 BREAKING：登录续签/撤销、DTO 单源、索引/保留、错误呈现均为加固与新增；既有接口形状与语义不变（DTO 单源是抽取不是改形）。console 前端重构为纯前端接线，后端数据/字段已具备。

## Capabilities

### Modified Capabilities
- `console-panel-api`：加固既有 JWT 鉴权（续签 + 撤销 + WS 首帧鉴权 + 到期断连）、只读聚合非阻塞（补索引 + 数据保留，落实既有「MUST NOT 全表扫描」）、面板 WS 扇出（背压 + 大载荷截断 + 零客户端跳过）、enum 漂移哨兵（修哨兵对 live 真值）；新增 DTO 单源防漂移、面板写端点输入校验（存在性/格式，落实「绝不静默假成功」于面板写路径）、console 读查询诚实错误呈现（落实红线于 UI 读路径）。

## Impact

- **aidcp-cloud**（`src/panel/`、`src/risk/`、`src/cache/`、`src/metrics/`、`src/config/`、`src/feishu/`）
  - 面板服务端：`panel-server.ts`（续签端点 + 存在性校验 + requestId 白名单）、`panel-ws.ts`（背压 + 首帧鉴权 + 到期断连 + 零客户端跳过）、`jwt.ts`（jti + 撤销表/内存黑名单）、`panel-store.ts`（三处全表扫描查询改走新索引 + 修注释）。
  - 存储层：`pg-risk-store.ts` / `interaction-feed-store.ts` 补 `occurred_at` 索引（建表 + migrations 双写）；三表保留清理定时任务；`token-usage-store.ts` 接线既有 `purgeOlderThan`。
  - 配置视图：`role-config-facade.ts` 图像角色生效厂商读真实图片厂商；`server.ts` 面板视图组装。
  - DTO 单源：抽 `src/panel/dto/`（或共享形状）+ 逐字 diff 测试骨架（cloud 侧）。
- **aidcp-console**（`src/`）
  - 鉴权：`api/client.ts`（401 提示 + reason 保留 + 续签调用 + token 存储缝）、`auth/AuthContext.tsx`、`App.tsx` / `LoginPage.tsx`（来源路径回跳）、`ws/panelWs.ts`（首帧传 token + 4401 辨识 + 停止无限重试）。
  - 漂移：`types/aidcp-enums.ts`（补评论赞）+ `.test.ts`（对 live 真值）、`types/api.ts`（图片厂商字段 + DTO 单源镜像）、`components/AccountTotalsTable.tsx`、`pages/SettingsPage.tsx`（厂商下拉）、`pages/QuotasPage.tsx`（复用枚举）。
  - 性能/体验：`ws/panelWs.ts` + `pages/MonitorPage.tsx`（帧批处理/限渲染/暂停语义）、新增 `components/QueryGate.tsx`（10 页接入）、新增 `hooks/useConfigMutation.ts`（收口 20 处样板）、`components/WeekActiveGrid.tsx`（去重）、新增 `routes.ts`（合并双清单）、删/接 `components/honest-write-result.ts`、内容页队列快照/待审筛选、账号筛选 URL 化。
  - 测试/部署：审批 CAS 链前端测试；`README.md` 部署序列加 `npm test`。
- **ECS**（运维，无代码）：`AIDCP_PANEL_JWT_TTL_SECONDS=43200` 止血、Nginx `aidcp-console.conf` 去 `autoindex on`、生产库补索引（上机执行或随重启自建）。
