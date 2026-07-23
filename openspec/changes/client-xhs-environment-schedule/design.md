## Context

当前 Edge 右侧主区域包含三个互斥工作区：选中环境后的 `legacy-workspace`、视频号互动工作区与内容工作区。小红书环境主页在 `legacy-workspace` 中依次展示当前动作、实时工作说明、今日进展、发布状态和活动流；账号排期属于当前环境的运行能力，不属于内容首页。

Cloud 已以 `accountId` 为键解析两层生效周历：活跃时段 `effectiveActiveWeekMask` 与内容时段 `effectiveMask`。内容调度只在两层都命中时尝试动作，并继续受总开关、动作模式、日上限、在线状态、风控与单飞约束。因此客户端必须把周历展示成“可工作时间段”，不能把它包装成精确任务或成功承诺。

客户端普通业务读取已经通过 env-scoped customer-auth HTTP 完成：Renderer 只提交本地 envId，Electron main 将其转换为 profileId/envKey 并调用固定 Cloud 路径，Cloud 再做客户归属和持久账号绑定解析。本变更复用该边界。

## Goals / Non-Goals

**Goals:**

- 在小红书环境主页提供易发现但不抢占实时工作焦点的排期入口。
- 在同一环境上下文中展示当前账号七日生效排期、当前/下一时段与已启用动作摘要。
- 保证客户看到的时间段来自 Cloud 单一生效配置，不由 Edge 解析后台原始字段。
- 将“处于允许时段”和“真实正在执行”分开表达，并复用现有环境状态与今日进展。
- 环境离线时仍可读取；环境切换、平台切换和迟到响应不串号。

**Non-Goals:**

- 不在内容首页、内容工作区导航或全局标题栏增加账号排期入口。
- 不开放客户写排期、动作模式、审批模式、总开关或日上限。
- 不改变 168 格周历、继承规则、分钟错峰、调度闸序、风控或发布审批。
- 不把小时窗口解释为精确执行时刻，也不按时间经过伪造“已完成”。
- 不为 Facebook 或视频号提供本入口，不构建 Edge 安装包，不部署 OL。

## Decisions

### 1. 入口属于环境主页，详情是环境二级页

入口插入 `legacy-workspace` 的实时工作说明之后、“今日进展”之前。入口保持为一张紧凑横条，显示“本周安排”、今天时段数和当前/下一时段；整条可点击。

点击后隐藏 `legacy-workspace` 并展示新的 `environment-schedule-workspace`。顶部标题栏与左侧环境栏继续保留；返回时恢复环境主页与原滚动位置。详情页不嵌入 `content-workspace`，也不复用内容页导航状态。

替代方案是全局标题栏入口，但排期严格属于当前环境，会与既有灵感摘要争夺窄窗空间；另一个替代方案是内容首页入口，但会错误地把浏览/互动运行时段解释为内容功能。

### 2. Cloud 返回客户可读投影，不下发原始掩码

新增 `GET /environments/:envKey/schedule`。路由复用 `resolveOwnedBoundAccount`，以 Cloud 权威账号平台判定小红书资格，再调用只读依赖获取 `ContentScheduleStore.effectiveScheduleFor(accountId)`。

Cloud 把有效的 168 位掩码转换为周一至周日的半开小时区间 `[startHour, endHour)`，并返回：

- `timezone` 与 `weekStartsOn=monday`；
- 每日 `activityRanges` 与 `contentRanges`；
- `autoEnabled` 以及平台支持且实际启用的客户动作摘要、审批含义和日上限；
- 由同一服务器本地时钟计算的 `currentWindow` 与 `nextWindow`；
- `meta.asOf`。

响应不含 `accountId`、原始掩码、override/global 来源、updatedBy 或内部失败原因。活跃掩码缺失沿运行时语义投影为全天可活动；内容掩码缺失/非法投影为空。内容区间再次与活跃区间取交集，确保客户投影不比运行时更宽。

### 3. 排期状态与运行状态分层

排期接口只说明 `currentWindow`、`nextWindow` 和允许动作，不声称任务正在执行。Edge 只有在现有当前环境状态明确运行时才使用“工作中”；处于窗口但未运行时使用“当前可工作”；窗口结束仅显示“已结束”，不得自动显示“已完成”。

详情页右侧“今天已经发生”直接复用环境主页已有的 Cloud 已确认今日用量，不复制到排期 API。启动、关闭与浏览器按钮继续委托现有环境生命周期控制，排期组件不建立第二份 running 状态。

### 4. 环境范围状态与迟到响应防护

Renderer 以 `{envId, platform, requestEpoch}` 管理排期状态。选中环境变化时立即清空旧入口和详情数据并递增 epoch；只有 envId、权威平台与 epoch 均仍匹配的响应才能提交。

入口只在平台明确为 `xiaohongshu` 时显示。平台未知、Facebook、视频号、无真实环境或缺 main IPC 时均 fail-closed 隐藏且不发请求。详情打开期间切换到另一个小红书环境时重新读取；切换到非小红书或无环境时退出详情并回到对应环境主页。

### 5. 普通读取与运行连接解耦

Electron main 新增具名 IPC `environment-schedule:get`，Renderer 不能传 URL、token 或 accountId。main 只接受本地 envId，解析 profileId 后调用固定 customer-auth 路径。

读取不检查 core、浏览器或自动化 WebSocket 在线。页面打开、环境切换与显式重试触发 HTTP 读取；页面保持打开时按分钟边界刷新当前/下一时段，已有运行事件只触发重新渲染或失效，不直接覆盖 Cloud 排期。

### 6. 第一版只读且状态完整

入口和详情覆盖 loading、真实空排期、环境未启动、绑定未知、平台不支持、读取失败与带旧数据刷新。读取失败时若有同环境旧成功数据则保留并标记“上次更新”；没有旧数据时展示可重试错误，绝不回落到编造的全天或空周历。

本次不展示无后端写能力的“调整安排”按钮。未来若开放客户写入，应另立 OpenSpec，定义客户可编辑字段、CAS/审计与后台配置冲突语义。

## Risks / Trade-offs

- [服务器本地时区与客户认知不一致] → Cloud 显式返回实际时区，Edge 按返回值展示，不硬编码“北京时间”；部署验证核对 DEV 进程时区。
- [活跃缺失的 fail-open 被误画为管理员显式排了全天] → 客户只看到生效时间，不展示“已自定义”；文案使用“可工作时段”而不是“你设置的时段”。
- [窗口存在但其它闸阻止实际动作] → 窗口状态与真实运行状态分层，详情脚注说明会依据账号状态和当日安排择机执行。
- [环境主页新增卡片使主屏过长] → 入口收敛在 64–72px，详情点击后进入二级页，不在主页展开七日网格。
- [切换环境时旧数据闪现] → 切换即清空并用 envId + epoch 双重提交校验。
- [Cloud 接口泄露后台配置] → 使用显式客户 DTO allowlist 和固定平台动作标签，不序列化 store/catalog 原对象。

## Migration Plan

1. 先发布 Cloud customer-auth 只读接口；旧 Edge 不调用，行为不变。
2. 集成 Edge 源码，入口仅在接口存在且当前平台为小红书时显示。
3. DEV 验证离线读取、绑定失败、平台门禁、环境切换和时段边界；不构建客户端安装包。
4. 回滚 Edge 即移除入口；Cloud 新增只读端点可安全保留或随 Cloud 回滚，不涉及 schema 与数据迁移。

## Open Questions

无。用户已明确入口属于点击小红书环境后进入的环境主页，而非内容首页。
