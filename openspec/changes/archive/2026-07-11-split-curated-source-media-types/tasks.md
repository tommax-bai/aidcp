# Tasks: 精选源帖类型拆分为图文 / 视频

## 1. OpenSpec 与契约

- [x] 1.1 增加精选源帖类型拆分的 spec delta，并通过 `openspec validate split-curated-source-media-types --strict`。
- [x] 1.2 cloud / edge `protocol.ts` 同步给 `note.detail` 增加可选 `mediaType`，老边端缺失时云端按 `image_text` 处理。

## 2. aidcp-cloud

- [x] 2.1 `curated_content.content_type` 调整为 `image_text|video|comment`，启动时将存量 `note` 迁为 `image_text`，并重算 `dedup_key`。
- [x] 2.2 精选写入：详情评估、自有收藏路径按媒体类型写入；未携带媒体类型时写 `image_text`。
- [x] 2.3 面板 API：支持 `image_text`、`video`、`comment` 筛选与 facets；旧 `note` 查询兼容为图文+视频。
- [x] 2.4 创作与评论召回：源帖召回改为图文+视频集合。
- [x] 2.5 行级动作：参照洗稿只允许 `image_text`，定向评论允许 `image_text|video`，评论行拒绝。
<!-- aidcp-cloud 67a0acb split source media types, migration compatibility, panel/API action gating -->

## 3. aidcp-edge

- [x] 3.1 笔记详情上报携带 `mediaType: image_text|video`，来源使用 feed 卡片已有的视频识别。
- [x] 3.2 更新协议类型并覆盖测试。
<!-- aidcp-edge 4559fe7 emit note.detail mediaType from feed video state -->

## 4. aidcp-console

- [x] 4.1 精选页筛选、标签和 facets 展示改为图文 / 视频 / 评论。
- [x] 4.2 洗稿按钮仅图文可点击；视频、评论置灰并禁止点击；原因提示可区分。
- [x] 4.3 定向评论按钮仅源帖可点击，评论行置灰。
<!-- aidcp-console 5c9c5f5 update curated filters and disable rewrite for video/comment -->

## 5. 验证

- [x] 5.1 运行 OpenSpec strict validate。
- [x] 5.2 运行 cloud 相关测试与 typecheck。
- [x] 5.3 运行 edge 相关测试与 typecheck。
- [x] 5.4 运行 console 相关测试与 build / typecheck。
<!-- validated: openspec strict; cloud acceptance/full/typecheck; edge acceptance/full/typecheck; console test/build -->
<!-- deployed 2026-07-04 21:27 CST: cloud 67a0acb to ECS via clean git archive; health active + 8787/8090 listening + Feishu WS ready + PG select 1. console 5c9c5f5 dist deployed to /opt/aidcp/console with assets/index-AGAanTVI.js and 8088/api/version OK. edge mediaType commit 4559fe7 included in local package dist-electron/AIDCP Setup 0.2.1.exe, built from then-current edge HEAD c422586. -->
