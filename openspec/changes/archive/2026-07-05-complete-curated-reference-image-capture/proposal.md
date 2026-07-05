## Why

精选内容池的参考图链路已经上线，但生产数据表明图文笔记多数仍无图，少数有图行最多只保存前三张。根因是边端只在 `note.open` 当下读取已加载 DOM，后续轮播浏览不会回写图片快照，同时云端精选库默认只保存 3 张，导致多图笔记的视觉参考不完整。

## What Changes

- 边端在 `note.browse_images` 翻图后重新抽取当前详情页图片引用，并随同一 `note.detail` 事件回传更新后的图片快照。
- 云端精选参考图默认保存上限从 3 提高到平台图文硬上限 9，仍保持去重、顺序、状态诚实和硬上限。
- 云端收到后续观测时允许用非空图片快照刷新精选行；机器人收藏路径仍不得用空快照擦掉已有图片。
- 后台展示继续读取 `reference_images`，无需额外接口形状变更；历史空图行仍需重新浏览/收藏后才能补图。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `note-extraction-fidelity`: 图片快照不只来自打开详情瞬间；翻图完成后 MUST 回传当时详情页可观测到的有界图片引用。
- `curated-inspiration-corpus`: 精选笔记参考图保存上限 SHALL 覆盖平台图文最多 9 张，而不是默认只保留前三张。

## Impact

- **aidcp-edge**
  - `src/browse/browse-session.ts`: `note.browse_images` 成功后重新抽取图片并上报 `note.detail`。
  - `src/browse/note-extractor.ts`: 复用既有抽图规则和 9 张硬上限。
  - 相关 browse session 单测补覆盖翻图后回传。

- **aidcp-cloud**
  - `src/cache/curated-content-store.ts`: 参考图默认保存上限调整为 9。
  - `src/server.ts`: 构造 store 可保持默认；生产入库自然保留 9 张。
  - 相关 curated store 单测补覆盖默认 9 张。

- **Operations**
  - 已入库历史空图/三图行不会自动补齐；需要后续真实浏览重新观测该笔记才会刷新。
