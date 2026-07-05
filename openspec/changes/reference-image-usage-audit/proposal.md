## Why

精选页参照洗稿已经支持把原文参考图带入发布链，但当前图片厂商可能只支持文生图而不支持图生图。运营看到“带图参考”后容易误以为生成配图实际使用了原图视觉信息；当 provider 明确 `unsupported` 时，生成结果会与原图差异很大但后台没有直接暴露原因。

## What Changes

- 发布配图链路 SHALL 汇总参考图使用状态，区分 `used` / `unsupported` / `unavailable` / `skipped` / `none`，并随发布记录持久化。
- 内容面板 SHALL 在参照洗稿记录上展示参考图审计：有几张原文参考图、图片生成是否实际使用、若未使用则显示稳定原因。
- 历史记录无审计字段时 SHALL 诚实回落为空态，MUST NOT 编造“已使用参考图”。
- 本 change 不接入新的图生图 provider，不直接复用原图，也不改变现有配图生成、审批、下发红线。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `publish-multi-image`: 配图生成结果需要把参考图使用状态作为审计信号持久化。
- `console-panel-api`: 内容页发布记录投影需要暴露并展示参考图使用审计。

## Impact

- **aidcp-cloud**
  - `publish-agent/types.ts`: 发布元数据/面板 DTO 增加参考图审计类型。
  - `publish-agent/roles/publish-executor.ts`: 从 `imageDirective` 与 `referenceNote.images` 汇总审计并写入 `publish_metadata`。
  - `panel/panel-store.ts` / `panel/types.ts`: 从 `publish_metadata` 投影审计字段。
  - 单测覆盖 unsupported、无参考图、历史无字段回落。
- **aidcp-console**
  - `src/types/api.ts`: 镜像新增审计 DTO。
  - `src/pages/ContentPage.tsx`: 在配图/洗稿来源附近展示参考图使用状态。
  - 页面测试覆盖 unsupported 文案。
