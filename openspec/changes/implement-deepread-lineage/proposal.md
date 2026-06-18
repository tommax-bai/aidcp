## Why

详情页深度阅读链路（列表选卡 → 详情页粗筛 → 多图浏览 → 评论浏览 → 进作者主页 → 抓粉丝/作品数 → 是否关注）在设计文档（`docs/architecture.md`、`docs/protocol.md`、`docs/risk-control.md`、`docs/anti-detection.md`）里是完整闭环，协议类型与边缘执行器也已预埋，但**中段从未接线**：`DeepReader` 是硬编码 0、不发命令的空壳；`comment_reviewer` 只是个孤名；"进主页"复用 `open_note` 但 `type` 字段在协议里不存在被丢弃，导致边缘从不真正进作者主页；`profile.detail` 在 cloud handler 漏接、edge 也从不上报。结果是机器人**从不浏览多图与评论、从不进作者主页、关注判定永远拿到 0 粉丝/0 作品的假数据而恒拒**。本 change 把这条链路的中段补实接线。

## What Changes

- **多图浏览**：将 `DeepReader` 从空壳改为真实角色——基于内容（图数/正文长度）+ 人设决策本次是否看图、看几张，下发 `browse_images` 指令；边缘校准真实小红书选择器、回报真实张数（修复 `||1` 兜底导致的恒报成功）。
- **评论浏览**：实体化独立角色 `comment_reviewer`（当前仅类型联合里的一个名字），用 LLM 判定本次是否浏览评论、浏览多少，下发 `scroll_comments` 指令；边缘校准评论区选择器。本链路只做"浏览评论"，**不做发评论**。
- **进作者主页**：**BREAKING（内部协议）** 新增专用指令 `profile.open`（cloud → edge），取代当前被静默丢弃的 `open_note { type: 'profile' }`；cloud 把 `profile.entered` 翻译为该新指令；边缘新增进主页执行（点击作者头像/跳转 + 等渲染）。`AuthorEvaluator` 触发源**维持现状**（`interaction.completed`，仅点赞/收藏过的笔记才评估进主页）。
- **抓粉丝/作品数（修复数据链路断裂）**：cloud `handler.ts` 新增 `case 'profile.detail'` 喂入 `profileData`；边缘进主页后抽取 `postsCount`/`followersCount` 并调用 `reportProfileDetail`。修复后 `FollowAgent` 不再在 0/0 假数据上判定。
- **拟人化取舍**：下发 `browse_images`/`scroll_comments` 时按内容携带 `dwellMs`，并以概率决定本次看/不看（取舍多样性，对齐 `anti-detection.md` "有时看图不看文、有时看评论区"）；复用既有 `dwellMs`/`thinkMs`，无需新节奏字段。
- **不做**：「正文是否值得继续读/弃读」的 LLM 判定——从未设计过；正文停留时长已按字数实装上线，本 change 不引入该环。

## Capabilities

### New Capabilities
- `detail-deep-read`: 详情页深读行为——多图浏览（`DeepReader`/`browse_images`）与评论浏览（`comment_reviewer`/`scroll_comments`）的**判定 + 执行 + 拟人化取舍**，含边缘选择器校准与真实回报。
- `author-profile-visit`: 进入作者主页并采集作者资料——专用 `profile.open` 指令、边缘进主页执行、`profile.detail` 的上报与接收，修复粉丝/作品数数据链路以支撑关注决策。

### Modified Capabilities
<!-- 复用 command-pacing 的 dwellMs/thinkMs 机制，但不改其既有 requirement（每条决策指令本就可携带这两个时间字段），故不列为 modified。 -->

## Impact

- **aidcp-cloud**：`src/agents/deep-reader.ts`（空壳→真实角色）、新增 `src/agents/comment-reviewer.ts`、`src/orchestrator/role-dispatcher.ts`（接线 `browse_images`/`scroll_comments`/`profile.open`、订阅 `profile.detail`）、`src/comm/handler.ts`（新增 `case 'profile.detail'`）、`src/comm/protocol.ts` 与 `command-bridge.ts`（新增 `profile.open`、可选回报字段）、`src/event-bus/types.ts`（事件/角色定义）。
- **aidcp-edge**：`src/browse/browse-session.ts`（`browse_images`/`scroll_comments` 选择器校准与真实回报、新增进主页执行 case）、`src/browse/note-extractor.ts` 或新增 profile 抽取（`postsCount`/`followersCount`）、`src/client/edge-client.ts`（落实 `reportProfileDetail` 调用）、`src/comm/protocol.ts`（同步 `profile.open`）。
- **aidcp（本中控仓）**：`docs/protocol.md` 增补 `profile.open` 指令与回报字段说明；本 change 的 spec delta。
- **风控**：`browse_images`/`scroll_comments` 属低风险浏览动作，复用既有节奏与预算；不触碰发评论/发布的高风险路径。
