## Context

现有 cloud 已会在 `publishMetadata.mode === 'scheduled'` 时编排 `set_schedule`，但 edge 只是把 epoch 数字交给通用 `LocatingEngine`，后置校验仅检查页面上是否存在“定时”文本。因为该文案在开关未启用时也存在，这条路径可能假成功；同时 sequencer 将 `set_schedule` 放在 `bestEffort` 集合，失败仍会继续点击立即发布按钮。提交后又无条件执行 `capture_postId`，与平台原生定时语义不符。

2026-07-18 的实机探针得到以下事实：

- 定时开关可在填写标题、正文、话题之前开启，后续填写不丢时间；但自动化统一放在所有稿件内容和选项之后，便于最终校验。
- 平台接受未来 1 小时至 14 天、格式为 `YYYY-MM-DD HH:mm` 的定时时间；按钮从“发布”变为“定时发布”。
- `POST /web_api/sns/v2/note` 返回成功时没有可用公开 `post_id/note_id/share_link`，落地页仅有 `?published=true`。
- 「笔记管理 → 定时发布」能看到目标时间与内部 note id；它只是对账句柄，不是已公开链接。
- 删除该探针定时稿后数量恢复，账号已安全停止；没有留下测试定时稿。

本变更跨 edge/cloud/console、协议枚举、数据库状态和风险记账，必须保持边轻云重、AC-PUB、edge task 单写与“不假成功”不变量。

## Goals / Non-Goals

**Goals:**

- 让待审小红书稿件能选择平台原生定时发布，并且定时控件失败时绝不误发成立即发布。
- 把“平台接受定时任务”和“笔记已经公开”建模为不同事实。
- 只有对账取得真实公开 `postId` 后才消耗发布次数，且并发/重复对账最多记一次。
- 保留既有审批版本闸、edge lease、立即发布和 Facebook 行为。

**Non-Goals:**

- 不实现控制台取消/改期已提交到平台的定时稿；本期只能在提交前编辑目标时间。
- 不把内容排期页的生成时段改造成平台原生定时；两者仍是不同概念。
- 不承诺平台在目标分钟精确公开；对账以平台事实为准。
- 不为定时稿伪造公开链接，也不从裸内部 id 拼接链接。

## Decisions

### D1：`set_schedule` 使用专用 CDP 处理器并 fail-closed

edge 不再复用“页面含定时文字即成功”的通用定位。专用处理器先在本地校验 `now + 1h <= publishTime <= now + 14d`，按 Asia/Shanghai 格式化为分钟字符串，再执行：找到并开启定时复选框 → 通过原生 value setter 写日期时间控件并派发 `input/change/blur` → 回读复选框选中态、控件值与提交按钮“定时发布”三项正证据。任一证据缺失回 `ok:false`，sequencer 停在提交前。

否决方案：继续走 `LocatingEngine + valueValidator('定时')`。它无法区分“标签存在”和“开关生效”，已经被实机事实证明不具备发布安全性。

### D2：内容先完整填写，定时设置最后提交

小红书指令顺序固定为：

```
navigate_entry → select_mode → upload_image×N → set_cover?
→ fill_field(title) → fill_field(content) → add_with_candidate(topic/…)
→ set_option×N → set_schedule → submit_publish → capture_scheduled
```

立即发布仍为 `submit_publish → capture_postId`。定时模式绝不下发同页 `capture_postId`。`set_schedule` 从 `bestEffort` 移除；话题、可选元数据仍按原策略处理。

`submit_publish` 根据已验证的 scheduled 模式寻找“定时发布”按钮，并把平台成功提示视为“定时任务已接受”，不是“公开笔记已确认”。

### D3：新增 `scheduled` 持久态，公开确认前不记发布次数

状态流为：

```
pending_approval → scheduled → published
                         ↘ needs_review（对账有界耗尽）
```

定时提交成功或提交点击已派发但回执不确定时都进入 `scheduled`，绝不自动重投；内部定时 id 可空。`scheduled` 不进入 `status IN ('submitted','published')` 的既有发布计数口径，也不调用 `recordPublish`。对账以原子 `UPDATE ... WHERE status='scheduled' RETURNING` 确认首次转 `published`，只有返回一行的调用者记一次风险账，防重复轮询双计数。

### D4：协议不加消息，只增加两个通用 command kind

两端 `PublishCommandKind` 增加：

- `capture_scheduled`：定时提交后打开笔记管理的定时列表，以精确标题 + 目标分钟匹配并返回内部定时 id；失败不改变“可能已排队”的事实。
- `reconcile_scheduled`：目标时刻后打开已发布列表，优先使用内部 id、再用精确标题 + 目标分钟匹配；只有取得公开 post id 和平台给出的可用 URL 才回 `ok:true`。

参数增加 `scheduledTitle`、`scheduledPlatformId`；`value` 在 `capture_scheduled` 结果中表示内部 id，在 `reconcile_scheduled` 结果中表示真实公开 post id。`postUrl` 只允许后者携带。MessageType 数量不变，`command-bridge` 的通用映射不变，但两份 protocol 与 `docs/protocol.md` 必须同步。

### D5：cloud 负责有界对账与退避

`publish_log` 增加 `scheduled_platform_id`、`scheduled_at`、`schedule_reconcile_attempts`、`schedule_next_reconcile_at`、`schedule_last_error`。首次对账时间为目标时刻后 10 分钟；未公开/暂时找不到时按 15m、30m、60m、2h、4h、6h 上限退避，最多 8 次。达到上限转 `needs_review` 并保留诊断，绝不声称失败发布或自动重投稿件。

对账复用 `EdgeTaskLeaseClient.withLease(kind='publish')` 和账号绑定 edge，属于平台只读核验；edge 离线、验证码暂停或未拿到 lease 时只延期，不消耗稿件失败预算。cloud 定时扫描只查询到期索引行，并按既有账号串行边界执行。

### D6：定时字段走既有草稿 CAS 与 delegated candidate 路径

控制台在待审详情中把发布方式控件放在标题/正文/话题编辑之后、审批动作之前。选择定时后显示 `datetime-local`，前端做即时范围提示，cloud 仍做权威校验。`EditDraftPatch` 增加 `publishMode` 与 `publishTime`：

- `immediate` 强制 `publishTime=null`；
- `scheduled` 必须为小红书且落在提交时的 1h–14d 窗口；
- 修改成功深合并 `publish_metadata.mode/publishTime`，自增 `content_version`，旧审批签名按既有版本闸失效。

复用 `/api/delegated-tasks/draft` 的 `modify_candidate`，不新增裸 SQL HTTP 写口。Panel projection 增量返回 `platform`、`publishMode`、`publishTime`、`scheduledAt` 与内部 id（内部 id 只做诊断，不渲染成链接）。

### D7：兼容与迁移

新列均可空并由幂等迁移添加；旧行保持原状态。立即发布序列、Facebook profile 与旧协议消息类型不变。部署顺序为 cloud schema/协议兼容代码 → edge → console；在 edge 未升级时 scheduled command 会诚实失败在提交前，不会立即误发。

## Risks / Trade-offs

- **[平台 DOM 或文案变化导致定时设置失败]** → 三项正证据 + fail-closed；立即发布不会作为降级路径。
- **[平台公开延迟超过退避窗口]** → 转 `needs_review` 而不是 `failed`；运营可在平台核对，数据保留最后错误。
- **[同标题多篇造成误匹配]** → 优先内部 id；回落匹配同时要求精确标题与目标分钟，歧义时回 `ambiguous_match`。
- **[定时提交点击后网络断开]** → 按“可能已排队”进入 `scheduled`，不重投；后续对账解决，不制造双稿。
- **[本地时区与平台时区不一致]** → cloud 存 epoch，edge 唯一按 Asia/Shanghai 格式化；UI 展示明确为北京时间。

## Migration Plan

1. 先执行 additive migration 并部署兼容新状态/字段的 cloud。
2. 部署支持新 kind 与 fail-closed `set_schedule` 的 edge；协议验收确认两端逐字一致。
3. 部署 console 定时编辑入口。
4. 在 dev 使用「工程师大白」做一条至少 1 小时后的定时探针，确认 `scheduled`、不计数、平台定时列表可见后取消测试稿；真正到期对账用短周期测试桩与后续受控真机项分别验收。
5. 回滚应用代码时保留 nullable 列；若存在 `scheduled` 行，旧 cloud 不得部署到无法识别该状态的版本，需先停对账并人工收敛。

## Open Questions

- 平台“已发布”列表在目标时刻后的公开 URL DOM 选择器仍需随首条真实到期稿校准；在此之前只接受明确、无歧义的正证据，宁可进入 `needs_review`。

