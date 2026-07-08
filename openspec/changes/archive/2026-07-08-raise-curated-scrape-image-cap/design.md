# Design — raise-curated-scrape-image-cap

## 决策 D1：抓取参照池上限与发布配图张数解耦

系统里有两族独立的「9」，本变更只动前者：

| 族 | 常量 / 位置 | 语义 | 本变更 |
| --- | --- | --- | --- |
| **抓取参照池** | edge `NOTE_IMAGE_HARD_MAX`；cloud `CURATED_REFERENCE_IMAGE_DEFAULT_LIMIT` / `_HARD_MAX` | 观测别人的笔记时，抽取 / 持久化多少张参考图进精选库 | 9 → **30** |
| **发布配图张数** | cloud `IMAGE_COUNT_HARD_MAX`（prompts.ts）；`REFERENCE_IMAGE_MAX_COUNT`（reference-image-guidance.ts）；wanxiang `slice(0,9)` | 我们自己发帖时每帖最多几张图 / 喂几张参照给生成 | **不动**（小红书图文帖 ≤9 平台硬约束） |

参照池存 30、发布仍 ≤9 是刻意的：更丰富的源图池让洗稿/对齐（见并行 change `rewrite-image-count-parity`）有更多素材可选，而发布出口独立夹在 9。二者无数据耦合——发布链在 `publish-scheduler.prepareReferenceImages`、`image-generator`、`image-prompt-composer`、wanxiang provider 四处独立把参照图夹到 ≤9，参照图只作生成引导、从不作为发布图直接上传。

## 决策 D2：为何不抬边端翻图浏览张数

边端「翻几张图」由云端 `DeepReader` 决定，高互动图文给 `VIEW_ALL_IMAGE_CAP=18`（「尽量看完」，边端按真实轮播总数截断）。小红书图文笔记至多 18 张，故 18 已等于「看完任何笔记」；抬到 30 只会让边端多点几下已禁用的翻页箭头（无害但无益，且徒增页面停留时长）。旧真实瓶颈是抽取 + 持久化的 9（把 18 张源稿截成 9），本变更正对此。YAGNI：不抬 18。

## 决策 D3：revert 地雷拆除

已完成未归档 change `curated-reference-images` 的 note-extraction-fidelity delta 新增了「笔记详情上报有界图片引用」要求，硬写「上限 MUST NOT 超过平台图文硬上限 9」；其 design.md 也记「hard cap 9」。若该 change 在本变更之后归档，会把 live spec 的图片上限**悄悄退回 9**、与已部署代码漂移。拆弹方式：直接把那个 change 的 delta 与 design 里的 9 就地改 30（该 change 已 Complete、非活跃，改的是事实已过时的常量值，不改其它语义）。改后无论两 change 谁先归档，live spec 上限恒为 30，幂等无冲突。
