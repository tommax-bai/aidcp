# Proposal: 精选源帖类型拆分为图文 / 视频

## 背景

精选内容当前以 `content_type=note|comment` 区分「笔记」和「评论」。运营侧需要把存量「笔记」明确迁移为「图文」，并在后续采集时识别「视频」，这样面板筛选、召回和行级动作才能表达真实素材类型。

## 变更范围

- 将精选内容类型从 `note|comment` 调整为 `image_text|video|comment`。
- 存量 `note` 行全部迁移为 `image_text`，同步修正依赖类型参与计算的去重键。
- 边端在上报笔记详情时携带图文 / 视频媒体类型；老边端未上报时云端按 `image_text` 兼容。
- 精选面板支持图文、视频、评论筛选与计数，并在过渡期兼容旧 `note` 查询语义为图文+视频。
- 创作 / 评论召回使用图文+视频作为源帖集合，不再只召回旧 `note`。
- 控制台行级动作中，「洗稿」仅对图文可点击；视频和评论的洗稿按钮置灰并禁止点击。定向评论仍仅对源帖（图文 / 视频）开放，评论行禁用。

## 非目标

- 不为视频实现视频内容洗稿或视频脚本生成。
- 不改变评论精选的准入逻辑。
- 不迁移历史 `note` 行为为视频；历史无法可靠反推媒体形态，统一按图文处理。

## 验证

- `openspec validate split-curated-source-media-types --strict`
- cloud：相关单测、acceptance、typecheck
- edge：相关单测、typecheck
- console：相关单测、build / typecheck
