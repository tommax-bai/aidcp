# Change: Remove Curated Empty Cleanup Panel Entry

## Why

空正文精选壳行已经在准入侧停止新增，后台继续展示“清理”入口会让运营误以为该清理是日常动作，并可能在全账号/单账号切换时造成额外认知负担。用户明确要求直接去掉后台这个“清理”入口。

## What Changes

- 精选内容后台不再展示“历史清理 / 清理历史空正文行”卡片、按钮、说明和确认弹窗。
- 前端不再从该页面触发 `/api/curated/contents/clear-empty`。
- 后端清理接口暂时保留为内部/应急能力，本次不做云端接口删除。

## Impact

- 影响仓库：`aidcp-console`、`aidcp`。
- 不改变精选列表、筛选、删除单条、洗稿、评论能力。
- 不需要数据库迁移；不删除生产数据。
