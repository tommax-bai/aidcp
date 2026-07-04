# Design: 发布与评论创作状态切换

## 1. 现状依据

- Electron 客户端通过核心进程 stdout 的 `[ui-event]` 行更新桌面状态：`../aidcp-edge/src/flows/ui-event-lines.ts` 构造结构化事件，`../aidcp-edge/src/electron/ui-events.cjs` 解析为 `loopStage` 和 presence。
- 渲染层 loop chip 由 `../aidcp-edge/src/electron/renderer/ui-logic.js` 的 `LOOP_STAGES` 与 `index.html` 中的 `data-stage` 标签共同决定。
- 发布链路已有两条边缘入口：旧整页 `publish.request` 和当前原子 `publish.command`；两者都应投影为“写笔记”状态。
- 阅读页发布评论由云端下发 `interaction.comment`，边缘真实发布成功后才产出 `action.completed/comment` 和 UI 计数。
- 管理后台精选内容池的 `create-post` 端点语义是参照精选内容重写成新草稿，即“洗稿”，并不是一般意义的写笔记入口。

## 2. 状态模型

Electron loop stage 增加两个创作态，但仍保持单点亮：

```text
feed -> select -> read -> write/comment/interact -> return
```

- `write`：发布稿件过程中点亮。来源包括云端发布快照、人审状态、旧整页发布请求、新原子发布指令。
- `comment`：阅读页进入评论创作和评论真实发布成功时点亮。
- `interact`：保留给点赞、收藏、关注、评论点赞等非创作互动。

## 3. Cloud 行为修正

不得在阅读完成后因“强参照”自动触发发布链。精选内容池手动“洗稿”、飞书 `/publish`、内容排期和原有发布触发器仍按既有规则进入发布链；阅读闭环只负责阅读、互动、评论创作、返回续刷。

这意味着：

- 删除读后自动写作机会角色、LLM prompt 目录项、集成测试和 `read_reference` 来源码。
- `triggerManual(referenceNote)` 的参照创作来源保持 `manual_reference`。
- 任何阅读后想洗稿的入口必须是显式用户/后台动作，而不是模型自动判断。

## 4. Console 口径

精选内容池行级 `create-post` 动作统一叫“洗稿”：

- 按钮、确认框、成功提示、失败提示、测试断言都使用“洗稿”。
- 描述仍强调“借选题结构、人设口吻重写、禁逐句照抄、生成后走飞书人审”。
- “纳入原因”和“更新时刻”列压窄并 `nowrap`；“操作”列放宽承载“洗稿 / 评论 / 删除”。

## 5. 失败边界

- 发布状态投影只改变 Electron 当前状态，不改变发布链成功/失败判定。
- 评论创作状态只在评论命令进入或真实评论成功时投影；失败行不得计数。
- 后台“洗稿”触发成功仍只表示生成链受理；最终是否发布由既有发布记录、人审卡和终态回执呈现。
- 不因状态投影新增边云协议，避免破坏旧边缘兼容。
