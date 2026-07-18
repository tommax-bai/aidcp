## Why

小红书创作平台已经提供原生定时发布，但现有实现把 `set_schedule` 当成可忽略的元数据增强，并在提交后强求同页 `capture_postId`。2026-07-18 使用「工程师大白」账号的实机探针确认：定时提交成功时通常没有公开笔记链接，只能先在「笔记管理 → 定时发布」看到排队记录，等目标时刻后再对账确认公开。

如果继续沿用当前语义，系统可能在定时控件没有真正生效时立即发帖、把正常的“尚未公开”误判为失败，或在平台尚未发布时提前消耗发布次数。

## What Changes

- 为小红书提供原生定时发布编辑入口；仅接受当前时间后 1 小时至 14 天内的分钟级时间，Facebook 与其它平台 fail-closed。
- 将发布页执行顺序固定为上传图片 → 标题 → 正文 → 话题/其它选项 → `set_schedule` → 最终校验 → 定时提交；`set_schedule` 改为提交关键步骤，失败即停止，绝不退化成立即发布。
- 定时提交后进入持久化 `scheduled` 状态，可保存平台定时记录内部 id，但不把它冒充公开 `postId`，也不在当场强求 `capture_postId`。
- 新增到期后对账：通过现有 edge task lease 打开笔记管理，确认笔记真正公开后才回写公开 `postId/postUrl`、转为 `published` 并记一次发布风控账；未公开时有界退避，耗尽后转人工复核。
- 扩展后台内容页投影与待审草稿编辑，使审核人能看见并修改“立即发布 / 定时发布”和目标时间；该修改与标题/正文相同，会自增内容版本并使旧授权失效。
- 协议仍使用现有 `publish.command` / `publish.command.result` 两条消息；只扩展 `PublishCommandKind` 与参数/结果语义，不新增 MessageType。

## Capabilities

### New Capabilities

- `xhs-native-scheduled-publish`: 小红书原生定时设置、定时提交状态、到期对账、计数边界与运营可见性。

### Modified Capabilities

- `publish-pipeline`: 定时模式的指令顺序、失败边界和终局状态与立即发布分流。
- `console-write-operations`: 待审草稿的发布方式/定时时间通过既有乐观 CAS 单写通道编辑。
- `console-panel-api`: 内容投影增量返回定时字段并支持控制台编辑展示。

## Impact

- **aidcp-edge**: `publish-command-handlers.ts`、两端同步的 `protocol.ts`、发布命令与实机 DOM 单测。
- **aidcp-cloud**: command plan/sequencer/dispatcher、`publish_log` 迁移与 store、定时对账轮询、delegated candidate 编辑、panel projection、协议与验收测试。
- **aidcp-console**: 内容详情浮层的发布方式和时间控件、状态标签、API 类型与前端测试/typecheck。
- **aidcp control**: `docs/architecture.md`、`docs/protocol.md`、`docs/risk-control.md` 同步定时状态与“确认公开才计数”的边界。

