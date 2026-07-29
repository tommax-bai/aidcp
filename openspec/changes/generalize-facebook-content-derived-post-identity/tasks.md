> **前置事实（真机实测，勿重新论证）**
> - 群组帖在**零交互**下拿不到任何可接受地址：Vo Tu 上 6/6 卡为 0；页面上只有 `/photo/`、`/stories/`，
>   `/groups/<群>/permalink/<帖>/` **不在 DOM 里**，它是点击评论按钮后**导航产生的 URL**。
> - 主页帖靠悬停时间戳可得（5/5，已由 `acquire-facebook-feed-post-identity-by-hover` / edge `78f89cf` 覆盖）；
>   群组帖悬停 0/1、悬停评论按钮 0/3、悬停点赞按钮 0/3。
> - 机制已存在：`00-shared.js:215-249` 的 `firstPostEvidence` / `firstPostTargetRef`
>   （证据 = 作者名 + 作者主页 + 正文 + 稳定链接 + 图片/视频标识，SHA-256），
>   含 DOM 标记、会话内 Map、取用时证据复校、歧义检测。**唯一限制是 `firstPostGroupScope()` 只认群组页。**
> - 云端只有评论链路认这个前缀（`facebook-edge-steps.ts:90`），浏览闭环完全不知道它存在。
>
> **热点文件警告**：本 change 触及两份 `protocol.ts`（CLAUDE.md §2 协议四处同步铁律）。
> 开工前确认无人同时在改；改动须两份逐字一致，靠双仓 `npm run typecheck` 暴露漂移。

## 1. 边缘 — 放宽作用域并签发引用

- [x] 1.1 把 `firstPostGroupScope()` 泛化为「当前列表面 + 文档代」的作用域键：首页 / 群组 / 搜索三面都能签发；换面或换代即失效。**保留既有群组页行为逐位不变**（回归零容忍） <!-- aidcp-edge 1d377fc contentRefScope()：群组页逐字返回原值，首页/搜索各自成域 -->
- [x] 1.2 前缀 `aidcp:facebook-group-feed-post:v1:` **保持不动**（云端评论链路按它匹配，改名会失配）；在代码注释注明它已不止用于群组，是历史命名 <!-- aidcp-edge 1d377fc 前缀保持不动，注释注明是历史命名 -->
- [x] 1.3 `cardOf` 在取不到平台地址时，改为签发内容派生引用并成卡，而不是返回 null；**仍保留"两者皆无则不成卡"的兜底**（例如证据不足以成立时） <!-- aidcp-edge 1d377fc 无地址即签发引用；证据不足或绑定歧义仍不成卡 -->
- [x] 1.4 卡上带出身份分档（平台地址 / 会话内引用），缺省为平台地址 <!-- aidcp-edge 1d377fc noteIdKind，缺省 permalink -->
- [x] 1.5 复核：签发引用**不得**污染 `seen_post_ids` 的既有语义——两类身份要能共存于同一个去重集合而不互相顶替 <!-- aidcp-edge 1d377fc cardDedupeKey：永久链接走 postId 归一，引用直接用自身 -->

## 2. 边缘 — 按引用重定位（点赞路径）

- [x] 2.1 `exactArticles` / `feedLikeTarget` 支持按引用重定位：命中唯一且证据复校通过才算命中；多命中 ⇒ `ambiguous_target`；证据变了 ⇒ 视为快照过期 <!-- aidcp-edge b717433 resolveContentRef 三种结局分开具名；快照过期沿用既有 `stale_target` 词汇，未造新词 -->
- [x] 2.2 点赞的成败**以按钮状态变化为准**，不做任何 id 比对 <!-- aidcp-edge b717433 确认仍是按钮状态；身份对齐闸对引用只比 DOM 标记、刻意不重算证据（点赞自己会改卡内 DOM，重算会把既成事实报成失败），证据复校移到下手之前的定位环节 -->
- [x] 2.3 复核 `validated_facebook_content_url` 对引用仍是**诚实拒绝**（导航兜底不得被绕过） <!-- aidcp-edge b717433 已复核并加断言（引用无 host ⇒ 拒）。附带收紧：就地读的导航回落对引用直接如实交出 context_changed，不再抛合成 InvalidRequest -->

## 3. 协议 — 身份分档字段（四处同步）

- [x] 3.1 两份 `protocol.ts` 新增可选分档字段，**逐字一致**；缺省 = 平台地址 <!-- aidcp-edge 1d377fc / aidcp-cloud 3e4203b 两份逐字一致（落地前 diff 校验过） -->
- [x] 3.2 `aidcp-cloud/src/comm/command-bridge.ts` 的动作↔消息映射按需同步 <!-- 无需改动：桥只做 action→MessageType 映射并原样透传 params，本 change 不新增 action、不新增消息类型；且它在云→边方向，新字段在边→云的 page.cards 上 -->
- [x] 3.3 `docs/protocol.md` 同步（含头部计数与 §2 表，若消息类型数未变则只改字段说明） <!-- aidcp §3.8 卡片字段 + §2.4 page.cards 行；该文档已主动取消「消息总数」计数行（19-20 行明写不复制易漂移的总数），故无头部计数可改 -->
- [x] 3.4 双仓 `npm run typecheck` 确认无漂移 <!-- aidcp-edge 1d377fc / aidcp-cloud 3e4203b 双仓 typecheck 全过 -->
- [x] 3.5 确认**不涉及**第 4 处主动命令白名单（本 change 不新增云端独立下发的命令） <!-- 本 change 不新增云端独立下发命令，不涉及第 4 处白名单 -->

## 4. 云端 — 准入分档

- [x] 4.1 会话内引用的卡：允许内容评估、允许计入浏览、允许就地点赞 <!-- aidcp-cloud 3e4203b 未拦评估/浏览/就地读，放行 -->
- [x] 4.2 **MUST NOT** 对其下发导航 / 打开详情 / 定向评论类命令——在调度器的统一出口处拦，不依赖边缘兜底 <!-- aidcp-cloud 3e4203b 闸在 sendCommand 统一出口、先于其他闸；判据精确到不误伤 surface=feed 的就地读 -->
- [x] 4.3 **MUST NOT** 进入交付人工的线索队列 <!-- aidcp-cloud 424834d 两处：引流线索检测器（唯一的机器→人工线索路径，出声跳过不静默）+ 精选库准入（后台精选页挂着定向评论按钮，等同交付人工） -->
- [x] 4.4 **MUST NOT** 落库作跨会话去重 <!-- aidcp-cloud 424834d 拦住全部按笔记键的持久行：跨会话去重表 / 点赞血缘 / 展示账本 / 精选库观测与自有动作标记。风控计数照常（真实发生的事实不因身份形态而不算数） -->
- [x] 4.5 老边端（无分档字段）行为逐位不变 <!-- aidcp-cloud 3e4203b 字段缺省即 permalink，逐位等于今天 -->

## 5. 测试

- [x] 5.1 断言：对会话内引用下发任何导航类命令 ⇒ 测试失败（红线，必须有断言守住） <!-- aidcp-cloud 424834d test/integration/content-derived-post-identity.test.ts：导航 + 定向评论都断言不下发；反面同批断言就地读必须放行（判粗会掐死浏览本身） -->
- [x] 5.2 断言：分档字段缺省时，行为与今天逐位一致 <!-- aidcp-cloud 424834d 三处：命令准入、handler 打标、线索链路各有一条缺省用例 -->
- [x] 5.3 断言：证据变化后按引用重定位失败（不解析到别的卡） <!-- aidcp-edge b717433 test/native-page-engine/facebook-content-ref-like.test.ts：证据改动后报 stale_target 且一次点击都没发出 -->
- [x] 5.4 断言：引用多命中 ⇒ ambiguous，不动手 <!-- aidcp-edge b717433 同文件：复制带标记的容器模拟虚拟化复用 ⇒ ambiguous_target -->
- [x] 5.5 断言：会话内引用不进人工线索队列 <!-- aidcp-cloud 424834d test/hot-lead-detector.test.ts 新增两条（引用不触发 / 缺省照常触发） -->
- [x] 5.6 协议一致性用例（`AC-PROTO-*`）覆盖新字段 <!-- aidcp-edge b717433 / aidcp-cloud 424834d AC-PROTO-20c，两仓逐字一致（已 diff 校验）。注：AC-PROTO 不做字节比对，加可选字段三层守卫都不会红，故必须手工补往返断言 -->

## 6. 真机验证（Vo Tu / `k1f44fit`，群组帖为主）

> **已解耦到 `docs/real-machine-acceptance-backlog.md` 簇 121**（归档与真机验收解耦）。
> 下列条目原样保留作追溯；执行以 backlog 簇 121 为准（那里另补了「不落库不进人工」「浏览量口径已放宽不是 bug」两条）。

- [ ] 6.1 基线：冷启动 + 纯程序化滚动，记录可上报卡数（当前实测 **0**）
- [ ] 6.2 改后：可上报卡数应 > 0；逐张核对作者与正文正确
- [ ] 6.3 就地点赞：能命中、能按按钮状态确认；**绝不能**点到别的卡上
- [ ] 6.4 确认云端从未对会话内引用下发导航类命令
- [ ] 6.5 采样引用碰撞率（招聘 / 租房群是最坏场景）；碰撞只应导致"少读一条"，绝不导致"操作错帖子"
- [ ] 6.6 虚拟化复用场景：滚走再滚回，引用不得漂到别的帖子上

## 7. 部署

- [ ] 7.1 边缘侧改的是编入 Rust 二进制的引擎与注入脚本，**仅 push 不生效**，须重打客户端包 <!-- 未做：打包属用户显式触发（CLAUDE.md §6），已登记 backlog 簇 121 前言 -->
- [x] 7.2 云端侧需部署 dev（按 CLAUDE.md §5 安全序列） <!-- aidcp-cloud 424834d 2026-07-29 deployed；部署前探得 ECS 恰在前一提交 64d767d（无并发部署撞车），备份 cloud.bak.20260729-182331.tar.gz，重启后 active + 8787 监听 + 飞书长连接已建立 + PG select 1 通过 -->

## 8. 明确不做（本 change 范围外）

- [x] 8.1 **不做**「点开评论弹窗取真地址」。那是交互路径（弹窗开关、滚动位置复原、被抢占后遗留清理），风险与本 change 不同源。评论 / 线索这条低频路径需要它，另起 change <!-- 刻意不做，本 change 范围外；已按此执行 -->
- [x] 8.2 **不补** `/groups/<群>/permalink/<帖>/` 地址格式。它只在点击导航后才出现，单独补格式**没有任何效果**（实测该 URL 不在 DOM 里）；须与 8.1 同一条 change 一起做 <!-- 刻意不做，本 change 范围外；已按此执行 -->
- [x] 8.3 不改哈希算法与证据构成 <!-- 刻意不做，本 change 范围外；已按此执行 -->
- [x] 8.4 不引入"有内容但无身份"的第三种上报态 <!-- 刻意不做，本 change 范围外；已按此执行 -->

## 9. 规格待和解（不得无限期挂着）

- [ ] 9.1 `facebook-feed-browse` 现有正文隐含「可上报 = 持有平台永久链接」，与本 change 的第二类身份口径不一致。因该能力已被 `repair-facebook-feed-exhaustion-continuation` 与 `restore-native-facebook-residual-parity` 各持 delta，本 change 刻意不叠第三份。**待那两条归档后立即补一条只改措辞的 change 收口**——两份规格同时有效期间，后来人按哪一份实现都说得通，这是真实的歧义风险

## 10. 实装实测记录

- [x] 10.1 **加载中不签发引用**（原设计没写，实装期被既有用例撞出来）。`facebook-router-contract` 的
  「区分加载中 / 可见不可上报 / 明确空态」夹具是「作者与正文都在、但永久链接尚未水合」——此刻若签发引用，
  等链接水合后同一条帖子会**以平台身份再上报一次**，浏览被记两次。**测试是对的，原设计漏了这条。**
  已加 `feedLoading()` 守卫（与 feedProbe 的 loading 同源判据） <!-- aidcp-edge 1d377fc -->
- [x] 10.2 **引用复用**（原设计没写）。判稳期每 500ms 重扫一次；群组帖那种整屏无地址的页面上，
  不复用等于每半秒把全屏卡片重新做一次 SHA-256。已加「元素已绑且证据未变则复用」 <!-- aidcp-edge 1d377fc -->
- [x] 10.3 `feedCards` / `feedProbe` / `cardOf` 因摘要是异步而全链路改 async，10 处调用点补 await <!-- aidcp-edge 1d377fc -->
- [x] 10.4 云端闸的判据必须精确到**不误伤就地读**：`open_note` 只有 `purpose:'navigate'`
  或非 feed 面才需要地址；`surface:'feed'` 的就地读不跳转、必须放行。判粗一点就会把浏览本身掐死 <!-- aidcp-cloud 3e4203b -->

## 11. 未完成（**不要当作已做**）

> 2026-07-29 第二批（edge `b717433` / cloud `424834d`）已把 11.1–11.4 全部补完、cloud 已部署 dev。
> 下面只剩两条真未完成，各自的门槛写在条目里。

- [x] 11.1 ~~`4.3` 交付人工线索的排除未实装~~ <!-- aidcp-cloud 424834d 已补。查证结论：机器→人工的线索路径只有一条（引流线索检测器→飞书待审卡），另有精选库这条等价面（后台精选页挂着「定向评论」按钮），两处都已按分档挡住 -->
- [x] 11.2 ~~`4.4` 跨会话去重的排除未实装~~ <!-- aidcp-cloud 424834d 已补。全部按笔记键的持久写都已挡：跨会话去重表 / 点赞血缘 / 展示账本（元数据 + 事件两处）/ 精选库观测与自有动作标记。风控计数刻意不挡 -->
- [x] 11.3 ~~`2.x` 按引用重定位（点赞路径）未做~~ <!-- aidcp-edge b717433 已补，三种结局分开具名 -->
- [x] 11.4 ~~`5.x` 测试全部未加~~ <!-- aidcp-edge b717433 / aidcp-cloud 424834d 已补 5.1–5.6 -->
- [ ] 11.5 **`6.x` 真机验证全部未做**（已解耦到 backlog 簇 121）。可上报卡数是否真的从 0 变正、
  引用会不会漂到别的卡上、碰撞率如何，一概未测。**前置是 11.6 的边缘出包**。
- [ ] 11.6 **边缘未出包**：cloud 侧 `424834d` 已部署 dev；edge 侧改的是编入 Rust 二进制的引擎与注入脚本，
  **仅 push 不生效**，须重打桌面客户端包。打包属用户显式触发的动作（CLAUDE.md §6），本 session 未做。

## 12. 归档前置（本 change 尚未归档的原因）

- [ ] 12.1 **§9.1 的规格和解还没门槛**：它要等 `repair-facebook-feed-exhaustion-continuation` 与
  `restore-native-facebook-residual-parity` 归档后才能补那条只改措辞的 change（现在叠第三份 delta
  会在归档合并时撞车）。**此前不归档本 change**——一旦归档，§9.1 就只活在归档目录的 tasks.md 里，
  等于把一条已知的规格歧义悄悄丢掉，而这正是提案里明写「不得无限期挂着」的那条。
- [ ] 12.2 归档时顺带确认：本 change 的 spec delta 只新增 `facebook-content-derived-post-identity`
  一份能力，不碰 `facebook-feed-browse`（刻意为之，见提案）。

## 13. 实装期发现（不属于本 change，但别忘了）

- [ ] 13.1 **两份 `protocol.ts` 已有既存漂移（非本 change 造成）**：`origin/master` 上 18 行不一致
  （`ui.snapshot` 注释、`INTERACTION_BROWSER_PROFILE_IN_USE` 在三处联合里的位置、一处 `submitted_unconfirmed`
  拼写）。本 change 新增的字段与 `AC-PROTO-20c` 用例两侧逐字一致（已 diff 校验）。
  **`AC-PROTO` 抓不到这类漂移**——它不读对端文件、不做字节比对，只靠手工维护的消息名穷举 + 计数 + 逐字段往返。
  值得单起一条 change 收口（要么真做字节比对，要么把注释类差异显式豁免）。
- [ ] 13.2 **`contentRefNoteIds`（云端调度器侧，前一批 `3e4203b` 引入）没有清理点**：
  `clearFacebookNaturalInteractionEvidence()` 清了另外五个 FB 集合、没清它。方向是 fail-closed
  （一个引用 id 永远被挡住），不是正确性洞，但长会话会缓慢增长。本批新加的 handler 侧同名登记表已有界（FIFO 4096）。
- [ ] 13.3 **`fake_cdp` 的 reel 滚动用例在并行满载下偶发超时**（`deadline_unix_ms = now + 8s` 是墙钟预算，
  机器负载高时命令跑不完 ⇒ 无输出）。单独跑与第二次全量跑都通过，与本 change 无关（reels 面不签发引用），
  但它是一条会随机变红的用例，值得单独调预算。
