# Proposal: 空正文自有收藏不补建精选行

## 背景

精选内容池现在承担发帖创作与后台参照洗稿的正向素材职责。历史实现中，机器人收藏一篇笔记但同次访问没抓到正文时，会补建一条 `body=''`、`admit_reason='bot_collect(content_missing)'` 的精选行。这样的壳行保留了“机器人收藏过”的强信号，但没有可供创作消费的正文，后台还需要额外清理。

## 变更范围

- 自有收藏仍然免模型评估，但只有拿到非空正文时才自动补建精选行。
- 如果收藏事件没有可用正文，不再新建 `curated_content` 壳行；只允许对已经存在的精选行补 `bot_collected=true` 标记。
- 保留后台「清理空正文壳行」接口与入口，用于历史遗留数据和异常恢复，不再把它作为常规治理路径。
- 不改变行为账本、风控去重、点赞/收藏真实动作记录；这里只改变精选素材池是否补建行。

## 非目标

- 不新增 tombstone 或永久屏蔽机制；已删除/未纳入的内容以后若重新抓到正文且符合准入，仍可进入精选。
- 不改变评论精选准入。
- 不改表结构、不做数据迁移；历史壳行继续由现有清理按钮处理。

## 验证

- `openspec validate curated-empty-body-skip-admission --strict`
- cloud：`test/cache/curated-content-store.test.ts`、`npm run typecheck`
- console：`npm run typecheck`，必要时运行精选页相关测试
