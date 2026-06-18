## Context

详情页深读链路的事件骨架已连通：`quality.pass → DeepReader → reading.done → InteractionAppraiser → interaction.completed → AuthorEvaluator → profile.worth_visiting → ProfileOpener → profile.entered → ProfileBrowser → profile.browsed → FollowAgent → profile.done`。问题在中段三处空接线（详见 proposal）：`DeepReader` 空壳直通、`comment_reviewer` 孤名、`profile.open` 未走通且 `profile.detail` 双向断链。协议类型与边缘执行器大多已预埋，本设计聚焦**事件拓扑接线 + 边缘选择器校准 + 数据链路修复**，不重构既有角色框架（`BaseRole`/EventBus/RoleDispatcher）。

跨 aidcp-cloud（决策与编排）与 aidcp-edge（浏览器执行）两仓协同，契约与 spec 落在中控仓 aidcp。

## Goals / Non-Goals

**Goals:**
- 多图浏览、评论浏览成为真实可观测行为：cloud 按内容+人设决策并下发指令，edge 真实执行并**如实回报**（成败/数量）。
- 进作者主页真实发生：专用 `profile.open` 指令取代被丢弃的 `open_note{type:'profile'}`。
- 修复 `profile.detail` 数据链路，使 `FollowAgent` 基于真实粉丝/作品数判定。
- 拟人化取舍（看/不看图、看/不看评论）有概率多样性，复用既有 `dwellMs`/`thinkMs` 节奏。

**Non-Goals:**
- 不引入「正文是否值得继续读/弃读」判定（从未设计；正文停留时长已实装）。
- 不做"发评论"（仅浏览评论）；发评论属高风险路径，另行处理。
- 不改 `AuthorEvaluator` 触发源（维持 `interaction.completed`，仅互动过的笔记才评估进主页）。
- 不重写节奏模型（command-pacing），仅复用其 `dwellMs`/`thinkMs` 字段。

## Decisions

### D1：评论判定拆为独立角色 `comment_reviewer`，与 `DeepReader`（多图）串联
深读中段拆成两个单一职责角色，对齐现有 `content_evaluator`/`author_evaluator`/`follow_agent` 风格、各自可独立测试。事件拓扑串联：
```
quality.pass
  → DeepReader：决策是否看图/看几张 → (看) 下发 browse_images，待 action.completed → emit reading.images_done
                                       (不看) 直接 emit reading.images_done
  → comment_reviewer：决策是否看评论/看多少 → (看) 下发 scroll_comments，待 action.completed → emit reading.done
                                              (不看) 直接 emit reading.done
  → InteractionAppraiser（下游不变）
```
**为何串联而非并行**：edge 是单页面顺序操作，图与评论不能同时滚；串联保证动作有序、且 `reading.done` 仍是进入互动阶段的唯一出口（下游零改动）。
*备选*：DeepReader 兼管图+评论（改动小）——用户已否决，要求拆角色。

### D2：角色与边缘执行的协调走"指令 + action.completed 回执"
`DeepReader`/`comment_reviewer` 不直接调 edge，而是 emit 一个意图事件，由 `RoleDispatcher.setupCommandTranslation` 翻译成 `sendCommand({action:'browse_images'|'scroll_comments', params:{noteId, count, dwellMs}})`；edge 执行后回 `action.completed`，RoleDispatcher 据此推进到下一环（emit `reading.images_done`/`reading.done`）。沿用既有"动作失败兜底"（`recover_after_<action>_failed`），失败时也要推进、不卡死。

### D3：进主页用专用指令 `profile.open`，不复用 `open_note`
现状 `open_note{type:'profile'}` 的 `type` 字段在 `NoteOpenPayload` 不存在 → 序列化丢弃 → edge 按 `index=0` 开错笔记。新增协议消息 `profile.open`（cloud→edge，payload `{authorId?, reason?, thinkMs?}`），`command-bridge` 增加 `profile_open → profile.open` 映射，edge `dispatchCommand` 新增 case：点击当前详情页作者头像/跳转作者主页 URL，等主页渲染就绪。
*备选*：给 `NoteOpenPayload` 加 `type` 字段——会让 `note.open` 语义二义、edge 分支判断变脏，否决。

### D4：`profile.detail` 接线复用 `note.detail` 的成熟模式，并把 `ProfileBrowser` 触发点改到"数据就绪后"
- cloud `handler.ts` 新增 `case 'profile.detail'` → `emit('profile.detail.arrived', {detail, ts})`（与 `note.detail.arrived` 同构）；`RoleDispatcher` 订阅该事件 → `updateProfileData(detail)`。
- **关键时序修复**：`ProfileBrowser` 当前消费 `profile.entered` 时读 `getProfileData()` 恒得 null。改为消费 `profile.detail.arrived`（数据已就绪）后 emit `profile.browsed`（带真实 counts）。`profile.entered` 仅用于触发 `profile.open` 指令。
- edge 进主页成功后抽取 `postsCount`/`followersCount` 调 `reportProfileDetail`。
- **兜底**：edge 抽取失败/超时仍要回报（counts 缺省可标记 unknown 或 0 但附 `extracted:false`），cloud 侧 `FollowAgent` 对"未取到真实资料"应倾向保守 skip，**但不得因恒 0 而把"数据缺失"误当"低质量"**——这正是本 change 要消除的假信号。

### D5：拟人化取舍 = 角色决策里的概率门 + 内容相关 dwellMs
`DeepReader`/`comment_reviewer` 的 LLM/策略输出包含"本次是否执行"（看/不看）与"看多少"，并按内容长度/图数算 `dwellMs` 随指令下发；edge 叠 lognormal 抖动。多样性来自决策本身（有时看图不看文、有时翻评论、有时直接过），无需新协议字段。

### D6：边缘选择器对真实小红书校准，回报必须反映真实结果
当前 `browseNoteImages` 用 `.swiper-wrapper` 等过时/猜测选择器且 `count||1` 恒报 ok、`scrollNoteComments` 用不符的评论选择器。本 change 要求对照真实小红书详情页 DOM 校准选择器，并让 `action.completed` 如实反映"翻了几张/滚了几屏/无评论"，去掉恒成功兜底（找不到目标→报 `no_target` 而非 ok）。

## Risks / Trade-offs

- **[小红书 DOM 选择器易变]** → 选择器集中放置、配兜底链与单测夹具；回报如实使失效可观测（不再静默假成功）。
- **[串联增加详情页耗时]** → 由概率门控制执行频率 + dwellMs 上限截断；本就要模拟真人停留，额外耗时即拟人化收益。
- **[进主页/抽取失败致 follow 链中断]** → 失败也回报并兜底返回信息流（复用 `back_to_feed`），不卡死会话；follow 在数据缺失时保守 skip。
- **[`profile.open` 是内部协议新增]** → edge/cloud 两侧 `protocol.ts` 同步；旧 edge 不识别会忽略，但本仓 edge/cloud 同步发布，无跨版本兼容包袱。
- **[动作数增加触碰风控预算]** → `browse_images`/`scroll_comments` 属低风险浏览动作，纳入既有 view 类预算；不增加 like/collect/follow/comment 高风险计数。

## Migration Plan

1. aidcp：合并 spec delta、更新 `docs/protocol.md`。
2. aidcp-cloud + aidcp-edge：按 tasks 实装，本地 `npm test`/`typecheck`/`test:acceptance` 通过。
3. edge 本地连 ECS（`ws://121.89.85.150:8787`）跑通一轮浏览，人工观测：能看图、能翻评论、能进主页、`profile.detail` 上报且 `FollowAgent` 收到非 0 数据。
4. cloud 部署按 ECS 安全序列（备份→rsync→restart→healthcheck→失败回滚）。
5. 回滚：cloud 回退到备份版本；协议新增向后兼容（旧 edge 忽略 `profile.open`），无破坏性数据迁移。

## Open Questions

- `profile.open` 进主页的边缘实现走"点击作者头像"还是"直接跳转 `/user/profile/<id>` URL"？取决于真实小红书在详情页 modal 内能否拿到稳定的作者主页链接——实装时在本地页面核对后定（两者皆可，URL 跳转更稳但需 authorId→URL 规则）。
- 是否需要给 `browse_images`/`scroll_comments` 的 `action.completed` 增加结构化回报字段（已浏览张数/已滚屏数）供观测与训练？倾向加，但若 `ActionCompletedPayload` 现有 `reason` 字段够用则先不扩协议。
