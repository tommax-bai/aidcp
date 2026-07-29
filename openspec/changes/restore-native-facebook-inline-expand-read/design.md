## Context

Facebook 的浏览执行在 edge `4f04e9c`（2026-07-23）整体切到 Native Page Engine。装配处把历史 TypeScript Facebook 会话改成编译期不可达（`aidcp-edge/src/main.ts:1059` 的 `if (false && ...)`），就地读实现 `src/facebook/inline-reader.ts` 连编译产物都不再进 `dist/`，所以今天跑的必然是 Native 这条，**不存在回退路径**。

现状（实测坐标）：

- feed 面开帖：`native/page-engine/src/facebook-router/90-dispatch.js:78-85`。`surface==='feed'` 时只做 `actionRoot()` 锁卡 + `noteDetail(root, ...)` 返回，全程无点击、无等待、无校验。
- 正文取值：`20-feed.js:285-309` 的 `noteDetail` → `00-shared.js:506-511` 的 `articleBody`，取消息容器（或最长可见 `div[dir="auto"]`）的当前 `textContent`。整个 Facebook 页面规则脚本里搜不到「查看更多 / 展开 / See more」任一词形（11 个脚本 + Rust 源码全量搜索，零命中）。
- 停留：`src/native-page-engine/browse-session.ts:281-293` 的 `ensureFacebookScrollDwell` 只处理 `page_scroll` 的 `dwellMs`，锚点是「上批卡到达时刻」。就地读那条锚点（旧实现 `src/facebook/facebook-session.ts:214` 的 `computeInlineReadFloorMs` + `:894-896` 的 `inlineReadStartedAt`，与云端 dwell 在 `:695-709` 取 max）整条不存在。
- `thinkMs`：`src/native-page-engine/command-mapper.ts:55` 放行进 payload，Rust `command.rs:201` 有字段定义，但全仓搜不到任何消费点——收下即丢弃。
- 节奏快照：`browse-session.ts:224-229` 的 `applyPacingSnapshot` 是空实现，注释写「Pacing stays Cloud-owned」，连 `tempo` 也没留。

这些行为都不是设计变更，而是迁移时只搬了输出结构没搬行为：`facebook-feed-browse`（就地读全文、展开无效诚实失败、环境变化回落）与 `command-pacing`（`thinkMs` 执行前等待、就地读 read floor 第三锚点、「Native MUST NOT 接收字段后静默丢弃」）都是**当前已生效**的要求。缺的是 `native-facebook-behavior-parity` 没把它们列进 Native 必保清单，于是迁移任务被勾成完成而无人报警。

顺带发现同一条路径上的动作名漂移：脚本里 `fail('open', ...)`（`90-dispatch.js:81`）用的是 `open`，而云端角色关联的规范名是 `open_note`（`aidcp-cloud/src/comm/handler.ts:122`）。脚本里其余动作名（`like` / `comment` / `back` / `join_group` / `scroll` / `search` / `follow` / `comment_like` / `browse_images` / `scroll_comments`）都已对齐，只有这一个漏了。后果不是报错：兜底滚动因为不在 `noRecoverScroll` 名单里照样触发（`role-dispatcher.ts:3968-3981`），但 `open_note` 专属的清理（评论迁移标志 `pendingMigration`、评论支线时钟，见 `:3636-3641` / `:3693`）拿不到匹配。本次要在这条路径上新增「展开无效」终态，名字必须先归一，否则新终态会以云端不认识的名字回上去。

## Goals / Non-Goals

**Goals:**

- feed 面 `note.open` 恢复完整就地读语义：锁唯一卡 → 免点击捷径 / 锚定展开点击 → 增长校验 → 三项环境校验 → 上报全文。
- 恢复三条诚实终态：展开无效、环境变化回落详情、无展开控件的短帖正常成功。
- 恢复就地读 read floor，并与云端 `dwellMs` 取 max（不相加）。
- Native 实际消费 `thinkMs`（动作前等待）。
- 归一 feed 面开帖失败的动作名到 `open_note`。
- 用行为级回归测试把上述各条钉死，并把判据写进 Native 对等规格，使同类回归不能再静默通过。

**Non-Goals:**

- 不按浏览模式分叉。规则模式与人设模式共用同一条执行路径，客户端不感知模式。
- 不改云端。云端已按 `surface:'feed'` 下发、已在规则模式关掉质量粗筛、已在「帖子详情」上报的唯一入口记浏览与规则进度。
- 不做 Native 迁移的全面行为对等审计（本次只处理就地读与节奏两类）。
- 不补 `command-pacing` 要求的「操作类命令最小间隔 gating」——Native 路径同样缺失，但它是独立一层，单列后续处理。
- 不出桌面安装包。

## Decisions

### D1. 点击与校验放页面规则脚本，导航回落放 Rust

展开控件的定位、点击、增长轮询、URL / 弹层数 / 目标卡序号三项校验全部在页内完成，放 `facebook-router` 脚本；**只有环境变化后的详情页回落**交回 Rust。

理由：脚本层能做的只有页内动作，导航是 Rust 的既有职责边界（`session.cdp.navigate` + `wait_for_facebook_ready`），且 Rust 已有现成的「按 URL 打开详情、等身份确认再返回」路径（`native/page-engine/src/facebook/feed.rs:34-50` 的 `NoteOpen(params) if params.url.is_some()` 分支复用 `evaluate_facebook_router_until_requested_detail`）。脚本返回一个具名的 `context_changed` 终态，Rust 识别后按该帖规范 permalink 导航重读。

备选方案（脚本内自己 `location.href = ...` 跳转）被否：会把导航事实藏进页内脚本，绕开 Rust 的 URL 校验（`validated_facebook_content_url`）与就绪等待，且跳转后脚本自身的执行上下文即刻失效、无法诚实回执。

### D2. read floor 与 `thinkMs` 都放 TypeScript 会话层，不放 Rust

两者都在 `NativeBrowseSession` 里等待，Rust 侧 `think_ms` 保持纯透传、不新增消费点。

理由有三。其一，节奏语义必须单点：既有的 feed 停留已经在 TS（`ensureFacebookScrollDwell`），read floor 与它是同一个「取 max、不相加」判定的第二个锚点，拆到两个进程各判一半，必然出现两边都以为自己在保证停留、实际相加或都不保证。其二，TS 层持有 `AbortSignal`，等待可被租约抢占 / 暂停当场打断；等待若沉进 Rust 命令内部，抢占响应会被整段等待拖长，而抢占是「调度事件不是动作失败」的既有语义。其三，read floor 需要 `tempo`，而 `tempo` 是经握手快照下发到 TS 侧的。

配套：`applyPacingSnapshot`（`browse-session.ts:224`）不再整体丢弃，至少留存 `tempo` 供 read floor 使用。`opFloorsMs` 本次仍不消费（属最小间隔 gating，见 Non-Goals），但不再假装「无事可做」——留存并注明未接线，避免下一个人再读到「Pacing stays Cloud-owned」就以为这里本就该空。

### D3. 「展开无效」是动作失败终态，不是一条内容上报

点了展开但正文渲染长度没增长 → 返回 `open_note` 的失败回执（`reason: expand_no_effect`），**不**返回帖子详情。

理由：帖子详情上报是云端记一次浏览、推进规则进度、喂人设质量粗筛的唯一入口。展开没生效说明这次阅读没有真发生，回一条详情就等于把没读到的内容记成读过了——这正是要修的那类问题的镜像。失败回执会走云端既有的兜底滚动，循环不会卡。

代价明说：规则模式会因此偶尔白烧一张卡（该卡在下发前已被记入本会话已选集合，不会重选），进度更慢。这是诚实设计应付的成本。

### D4. 免点击捷径优先于点击

消息容器的全文已在 DOM 内、仅被视觉截断时直接取全文，不点。理由：Facebook 的折叠有两种形态，纯视觉裁短那种点击是纯粹多余的页面交互，多一次点击就多一次可被观测的动作，且这种形态本来就读得到全文——今天没有回归的那一半。此判定必须在点击**之前**做，否则捷径形同虚设。

### D5. 不按模式分叉，理由写进规格

云端可以只对规则模式关掉展开（省时间），但这条被否：规则模式的「已确认浏览」是直接兑换点赞与加群评论的凭证，用零交互的 DOM 抓取换真实互动，正撞「MUST NOT 静默假成功」；而且展开与停留同源，省掉展开等于同时省掉按正文长度的停留，行为会明显快于真人。反过来，按模式分叉还会在客户端引入一处「云端以为读了全文、边缘其实没读」的不一致来源，而这类不一致编译期查不出来。所以把「同一条执行路径、客户端不感知模式」写成规格条文，不留可选项。

### D6. 回归测试判据是行为，不是投影结构

新增的对等测试必须断言外部可见状态与 reason 码：展开前后正文长度关系、展开无效不产生详情上报、环境变化产生 detail 面上报、read floor 与 dwell 取 max 而非相加、`thinkMs` 产生实际等待。并把「行为对等而非同形状投影」写进 `native-facebook-behavior-parity` 的必测清单——这次回归之所以静默通过，正是因为迁移任务的完成备注写的是「返回有界的投影结构」。

## Risks / Trade-offs

- **[展开控件识别对文案敏感，Facebook 多语言 / 改版会漏]** → 定位以结构为主：限定在目标卡的消息容器内、只认非链接的可点控件，文案只作辅助判据且覆盖既有词形（含中英越西法）。漏认的后果是「无展开控件的短帖」路径 = 正常成功，退化成今天的行为，不会新增失败。
- **[增长轮询拖长单次开帖耗时，可能顶到命令超时]** → 轮询有界（固定轮数 × 固定间隔，量级参照已退役实现的 6 × 300ms），且远小于 feed 面开帖的默认命令上限 30s（`browse-session.ts` 的 `DEFAULT_NATIVE_COMMAND_TIMEOUT_MS`）。
- **[规则模式吞吐下降，运营侧观感像"变慢了"]** → 预期内且已在 proposal 写明：每篇多一次点击 + 更长停留 → 攒满 10 条更慢 → 规则批次触发频率下降；另有展开无效导致的偶发白烧卡。需要在交付说明里点名，避免被当成故障排查。
- **[环境变化回落引入额外导航，多一次页面往返]** → 只在校验真的失败时触发，且回落路径是既有的详情读取，行为等于该 change 之前的 `surface='detail'`。
- **[`thinkMs` 等待被抢占时的语义]** → 等待走可中断 sleep（`browse-session.ts` 已有 `abortableSleep`），抢占按既有语义处理为调度事件、不记动作失败。
- **[动作名归一改动触及回执关联]** → `open` → `open_note` 是**向云端规范名靠拢**，云端对 `open_note` 的处理路径本就存在且更完整；风险在于是否有别处依赖了 `open` 这个错名。落地时须在 edge 与 cloud 两侧全局搜索 `'open'` 作为动作名的消费点确认无依赖。
- **[本地只能验到判定层]** → 真实 Facebook 长帖的展开控件形态、折叠语义（视觉裁短 vs 点击补文）与多语言文案须真机确认，按既有约定登记进 `docs/real-machine-acceptance-backlog.md`，不在本地伪造通过。
