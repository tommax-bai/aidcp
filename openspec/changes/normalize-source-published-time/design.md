## Context

Edge 已在小红书详情页抽取并上报原始 `publishedAtText`，但当前 Cloud 只有 `hot-lead/heat-velocity.ts` 的专用解析器。该解析器为 48 小时热度窗设计：把“昨天”固定为 36 小时、把裸日期压成超窗哨兵；它没有观测时刻锚，不能生成可持久化的来源发布时间。精选准入、机器人收藏补建、管理 API 和客户 API 均未携带发布时间，桌面灵感库则把 `updatedAt` 显示在作者旁。

时间文案属于平台观测证据：同一个“3小时前”在不同观测时刻对应不同时间；“07-05”只有日精度且可能跨年；未知格式不能靠 `first_seen_at` 或 `updated_at` 猜测。部署还必须兼容旧 Edge、旧行和数据库自愈建列机制。

## Goals / Non-Goals

**Goals:**

- 提供无外部依赖、可注入观测时刻与 UTC 偏移的纯函数标准化器。
- 同时保留原始文案、解析状态、标准时间、精度和观测锚，允许后续重算。
- 让热度帖龄与精选持久化复用同一语义源。
- 精选列表/详情对管理端与客户域如实披露来源发布时间；缺失或不可解析时明确未知。
- 兼容旧消息与历史行，不做推测性回填。

**Non-Goals:**

- Edge 不生成绝对时间，不新增协议字段或主动命令。
- 本变更不抓取 feed 卡片发布时间，不扩展到 Facebook/视频号 DOM 抽取。
- 不使用来源发布时间改变精选准入门槛、排序或保留策略。
- 不把日精度来源伪装成精确时分；不批量猜测历史行。

## Decisions

### D1. Cloud 纯函数输出结构化标准化结果

新增通用模块，输入 `rawText`、`observedAt` 和 `utcOffsetMinutes`，输出：

- `rawText`: trim 后的原始平台文案；
- `status`: `parsed | unparseable`；
- `publishedAt`: 解析成功时的 epoch ms，否则 `null`；
- `precision`: `minute | hour | day`，不可解析时 `null`；
- `observedAt`: 本次详情事件时间锚。

默认偏移为 `Asia/Shanghai` 的固定 `+08:00`（480 分钟），调用者可以显式覆盖。纯函数不读 `Date.now()`，从而可测试、可复算。备选是只返回 `hoursAgo`，但它会丢失观测锚、日历日期和精度，无法持久化复用；备选是 Edge 直接算绝对时间，但会把平台语义与时钟决策下沉到客户端并扩大协议漂移面。

### D2. 日历文案按平台本地日历解析并显式记录精度

- “刚刚 / N 分钟前”按分钟精度从 `observedAt` 回推；“N 小时前”按小时精度回推。
- “昨天 HH:mm”按本地上一自然日指定时分解析；“昨天 / 前天 / N 天前”落对应本地自然日零点并标记 `day`，调用方不得把零点解释为平台提供的精确时刻。
- `YYYY-MM-DD`/中文日期按显式年份解析；`MM-DD` 选择不晚于观测本地日期的最近年份，处理一月看到“12-31”的跨年情形。
- 非法日历日期、未来相对量、未知文本返回 `unparseable`；原文仍保留。

备选是为不精确文案保存起止区间。区间最诚实但会显著扩大数据库/API/UI 模型；本变更用“代表时间 + precision”保持可查询性，并要求所有展示按精度格式化。

### D3. 热度判断由标准化结果派生年龄

`evaluateHotLead` 接受事件 `observedAt`，调用统一标准化器，再计算 `hoursAgo = max(0, (observedAt - publishedAt)/hour)`。日精度结果用于年龄上界保守判断：以该自然日结束时刻计算最小可能帖龄；即便最年轻估计仍超窗才判 `too_old`。不可解析仍 `unparseable_time` fail closed。

这样裸日期不再靠魔法哨兵表达，但不会把日精度零点当精确发布时间夸大帖龄。`HotLeadEval` 继续回报 `hoursAgo` 供现有审计消费。

### D4. 精选表保存完整证据，缺失更新不得擦除

`curated_content` 幂等新增：

- `source_published_at_text TEXT`；
- `source_published_at TIMESTAMPTZ`；
- `source_published_at_precision TEXT`；
- `source_published_at_status TEXT`；
- `source_published_at_observed_at TIMESTAMPTZ`。

精选观测和机器人收藏补建都携带 `publishedAtText + event ts` 到 store，由 store 调统一标准化器。冲突更新仅当本次有非空原始时间证据时替换整组字段；本次缺字段时保留已有证据。不可解析文本仍替换为最新原文、`status=unparseable`、标准时间/精度为 NULL，使平台格式漂移可观测而不是静默保留过期解析。

历史行保持五列 NULL。回滚代码时新增 nullable 列可留存；无须回滚 DDL。

### D5. API 白名单显式投影，UI 只展示来源语义

内部面板 DTO 与客户最小披露 DTO 均显式返回 `sourcePublishedAtText/sourcePublishedAt/sourcePublishedAtPrecision/sourcePublishedAtStatus/sourcePublishedAtObservedAt`。客户域不直出整行。

Console 列表新增“原稿发布”并在详情展示；桌面灵感列表/详情作者副行使用统一格式化 helper：解析成功按精度显示，未解析但有原文时显示原文并标“未转换”，完全缺失显示“发布时间未知”。`updatedAt` 仍可作为数据维护字段返回，但不得占据原稿发布时间位置。

## Risks / Trade-offs

- [小红书文案格式变化导致解析失败] → 保留原文与 `unparseable` 状态，测试覆盖已知格式，未知格式不猜测。
- [设备/Cloud 事件时钟有偏差] → 以 Cloud 事件 `ts` 为统一观测锚，不信任 DOM 隐含时钟；保留锚供审计和重算。
- [日精度代表时间被误当精确时间] → DTO 带 `precision`，UI 按日显示，热度按日区间保守计算。
- [自愈 DDL 在多实例启动时短暂竞争] → 沿用 `ADD COLUMN IF NOT EXISTS`，约束用幂等 DO block；部署后做 schema 与样例读取验证。
- [热度边界结果轻微变化] → 固定注入观测时刻做回归测试，重点覆盖 48 小时边界和裸日期；保持不可解析 fail closed。

## Migration Plan

1. 先部署 Cloud：nullable 列自愈创建，旧 Edge 消息兼容；新字段开始随新观测写入。
2. 验证表列、解析单测、精选新写入和客户/面板 API 投影；历史行仍为 NULL。
3. 发布 Console 静态资源与 Edge 源码更新；旧前端忽略新增字段，新前端对旧行显示未知。
4. 若运行验证失败，回滚 Cloud/前端代码；nullable 列保留且不影响旧版本。

## Open Questions

- 当前仅落小红书 `+08:00`；后续平台接入时由平台适配层选择偏移，不在本变更猜测其它平台时区。
- 是否按来源发布时间排序/筛选留给后续产品变更；本次只存储与展示，不改变精选池现有排序。
