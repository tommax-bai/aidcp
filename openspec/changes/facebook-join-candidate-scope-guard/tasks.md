> **P0 安全修复**：现网今天就可能加错群（推荐栏异群 join 被误点）。edge-only、无协议、无云端。单独即让 pending 场景 fail-safe；是 L2（`facebook-join-actuation-decouple`）clickTarget 匹配的作用域前置。

> **2026-07-12 评审订正**：承重判据从「异群链接排除（黑名单、fail-open）」翻为「目标群头部块正向包含（白名单、fail-closed）」——真机 dump 证实推荐位 join 是兄弟裸 `div` 无异群 `href`、黑名单漏排会误点异群。异群链接（E1）与推荐轮播容器（E2）降为 corroborating 排除。头部块祖先判据须真机校准后方 land。

## 0. 实装前硬前置（真机确认探针）

- [ ] 0.1 **头部块祖先判据校准 + 非锚点推荐位形态（承重、决定能否 land；二轮评审强化）**：真机捕获目标群头部块结构——群名主标题（`<h1>`/`[role="heading"][aria-level="1"]`）的祖先链、目标自身 Join 与推荐位 join 相对该块的位置——坐实「正向包含目标群头部块」能框住目标自身 Join 且推荐位 join 落块外。取窄=安全侧。**并 MUST 坐实真机「发现更多小组」推荐位卡片的导航形态**：`a[href="/groups/id"]` / `[role="link"]`+属性编码 id / 纯 JS 闭包（无任何属性带 id）。前两类 D7-1 已覆盖；若为纯不透明第三类，需补真机可辨结构信号（否则该形态头部块 fail-open）。**并 MUST 坐实真机推荐卡片是否**：① 用双列布局（异群链接在缩略图列、群名 h1+加入在内容列）；② 群名用 `<h1>`/`aria-level=1`（与目标群 heading 同级）——若是，验证「停在 ceiling」甄别能把目标 heading 与卡片 heading 分开、且目标群头部 heading 上溯确实只在 `[role=main]` 处撞见异群引用（非某中层 wrapper 与推荐位共处→那会 fail-closed 漏认目标）。**未坐实前不 land**；**land 前须真机验证一个非锚点推荐位 + 一个双列卡片、不能只重采简单锚点形态**（否则测试给假信心，二/四轮评审坐实）。
- [ ] 0.2 E1/E2 定档：捕获推荐栏 join 候选 `href`/`[role=link]`/属性编码的祖先群引用（E1 群 id 比对，含非锚点）、推荐轮播容器结构标志（E2 选择器）。

## 1. aidcp-edge — 作用域 helper（语言无关）

- [x] 1.1 目标群 id 解析：从 `location.pathname` 的 `/groups/<id>` 段取目标群 id；`numeric-id` / `vanity-slug` 两式规范化，解析失败返回 null（供点击腿 fail-closed）。 <!-- aidcp-edge 70b53e0 __parseGroupId；branch 未land、0.1-gated -->
- [x] 1.2 **候选作用域正向包含（D1 承重、fail-closed）**：定位目标群「头部/动作区」块（含群名主标题的头部/hero 容器，祖先判据见 0.1）；候选 `inTargetScope=true` **当且仅当**它是该块后代——头部块解析不出 → 无候选在域内（点击腿按 D3 fail-closed）。**默认出域**，不是默认在域。 <!-- aidcp-edge 70b53e0 __resolveHeaderBlock/__inTargetScope -->
- [x] 1.3 **corroborating 排除（E1/E2，非承重）**：在 D1 正向包含之上再叠——E1 候选导航引用（`a[href]`/`[role=link]`/属性编码，见 4b.1）解析到 `/groups/<异于目标群 id>` 则 `inTargetScope=false`；E2 候选落在推荐轮播容器内则 `inTargetScope=false`（E2 选择器待真机校准、暂不接线）。最终 `inTargetScope = D1正向包含 AND NOT E1`（E2 校准前不接）。 <!-- aidcp-edge 70b53e0 __candForeignRef（E1，已拓宽非锚点）；E2 defer -->


## 2. aidcp-edge — 点击腿 fail-closed（承重、安全）

- [x] 2.1 `GROUP_JOIN_CLICK_JS`：`join` 节点选取**只在 `inTargetScope` 候选内**取文档序首个；**删除**「页面级文档序第一个 join」回落。 <!-- aidcp-edge 70b53e0 -->
- [x] 2.2 fail-closed：目标群 id 解析失败**或头部块解析不出** → `scope_unresolved`；作用域内无 join → `no_target_in_scope`。绝不页面级点。两者在执行端映射为可重试 `not_ready`（见 4b.3），非 no_button。 <!-- aidcp-edge 70b53e0 -->
- [x] 2.3 保持既有 disabled 诚实 bail、`__FB_JOIN_CLICK__` 标记、坐标回报不变。 <!-- aidcp-edge 70b53e0 -->


## 3. aidcp-edge — 观测腿标注作用域（不阻断上报）

- [x] 3.1 `GROUP_JOIN_OBSERVE_JS`：每候选加 `inTargetScope`；`mainCta`/`joinButton` 挑选**只在 `inTargetScope` 候选内**——推荐栏 join 绝不冒充群主 CTA。 <!-- aidcp-edge 70b53e0 -->
- [x] 3.2 **成员信号收窄（红线1 尾巴）**：`membershipSignals` 从页面级 `signals.slice(0,8)` 改为**只在目标群作用域内读取**——推荐位建议群「已加入」信号绝不污染。 <!-- aidcp-edge 70b53e0；另加 D7-2 矛盾守卫双保险 -->
- [x] 3.3 候选清单**仍如实全量上报**（`ctaCandidates` 含 `inTargetScope:false`），不静默丢弃（守 L4）。 <!-- aidcp-edge 70b53e0 -->
- [x] 3.4 D5：作用域内控件 `ctaKind` 判不出 join/member/pending 时据实上报（原文 + `inTargetScope`），不越域找 join。 <!-- aidcp-edge 70b53e0 -->


## 4. 测试（edge）

- [x] 4.1 **红线（兄弟裸 `div` 无异群 href case，订正核心）**：目标 pending「已申请」+ 推荐位异群「加入小组」为兄弟裸 `div[role=button]` → 绝不点、判 pending、`outOfScopeJoinCount=1`（正向包含默认出域挡住，非靠 E1）。 <!-- aidcp-edge 70b53e0 jsdom 真跑 IIFE -->
- [x] 4.2 **红线（带异群链接 case）**：推荐位 join 带 `/groups/<异 id>` 祖先链接 → E1 亦排除、判 pending、不点。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.3 目标群自身可加入（Join 在头部块内）→ 正常点、点后 joined。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.4 目标群 pending（头部块内无 join）→ 诚实不点（含 4.1）。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.5 目标群 id/头部块解析不出 → fail-closed（not_ready），绝不页面级点。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.6 观测腿：`mainCta`/`joinButton` 不取推荐栏候选；`ctaCandidates` 含 `inTargetScope:false`（全量上报）。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.7 目标群自身钮被指向**本群** id 的链接包裹 → 不误排（在域可选）。 <!-- aidcp-edge 70b53e0 -->
- [x] 4.8 **成员信号收窄**：推荐位「已加入」在头部块外 → 不进 `membershipSignals`、不误判 already_member。 <!-- aidcp-edge 70b53e0 -->


## 4b. 二轮实装对抗评审订正（D7；5 确认发现含 1 红线）

- [x] 4b.1 **D7-1 红线闭合（承重；五轮对抗评审收敛）**：异群检测五轮从「仅 `a[href]`」→「扫全部元素属性(`querySelectorAll('*')`)」→「块保证无异群引用(含块根自身)」→「正向甄别 heading(只接受停在 ceiling 者)」→「歧义即 fail-closed(恰一个合格 heading 才用、≥2 判歧义)」。每轮 jsdom 复现前版本逃逸(现实概率逐轮降至 LOW)。`__hasForeignGroupRef` 含节点自身+后代；`__candForeignRef`(E1) 走到 `__HEADER_BLOCK`。**至此停客户端启发式**，剩余双向角落交 0.1（见 5.3）。 <!-- aidcp-edge 70b53e0+e554fcd+1ae8f66+dec006f+3161203(歧义守卫) -->
- [x] 4b.2 **D7-2 成员矛盾守卫**：`already_member` 仅当作用域内无 join 按钮时成立（`hasMemberSignal && !raw.joinButton?.found`）；正反 mutation-killing 测试已补。 <!-- aidcp-edge 70b53e0(守卫)+e554fcd(测试) -->
- [x] 4b.3 **D7-3 可重试回执**：观测腿 `scopeResolved===false` 与点击腿 scope bail 映射为 `not_ready`（不折叠 `no_button`）；`publicObservation.scopeResolved` 区分 undefined vs false。 <!-- aidcp-edge 70b53e0 -->
- [x] 4b.4 **D7-4 测试补齐**：先序异群 join click-leg 回归护栏 / 畸形 URL fail-closed / 点后推荐位已加入不伪造 / 非锚点推荐位(role=link 与 `div[role=button]` data-*)出域 / D7-2 正反。 <!-- aidcp-edge 70b53e0+e554fcd；full suite 1063 green -->


## 5. 集成与部署（edge-only）

- [x] 5.1 `npm run typecheck` + `npm run test:acceptance`(16) + 全量 `npm test`(1060) 全绿（AC-* 红线过）。 <!-- aidcp-edge 70b53e0 -->
- [ ] 5.2 edge master land（无 ECS/cloud 部署）。**未 land**：代码已提交并推送分支 `facebook-join-candidate-scope-guard`（aidcp-edge 70b53e0 + e554fcd + 1ae8f66），land 到 master **gated 在 0.1 真机校准**（含非锚点推荐位 + 双列卡片 heading 甄别 + 游离链接歧义 + 目标头部是否引用别群/嵌套 main 的可用性验证）。<!-- branch @ 3161203, awaiting 0.1 -->
- [ ] 5.3 真机验收登记 backlog：0.1/0.2 探针为实装前硬前置（已单列，五轮评审强化）；再核 pending/member/晚渲染三态作用域内不误点、可加入群正常、成员信号不被推荐位污染。**并 MUST 核可用性张力（五轮评审揭示的 fail-closed 角落）**：① 目标群头部若引用兄弟/关联群 `/groups/<异 id>` 会致目标 heading 被甄别掉 → 永久 `not_ready`（真机确认 FB 头部是否引别群；若是，需据真结构放宽甄别或改判据）；② 嵌套 `[role=main]` / 推荐位铺平为 main 裸兄弟 → `no_button`。归 FB 加群真机簇。

## 6. 收尾

- [x] 6.1 `openspec validate facebook-join-candidate-scope-guard --strict` 通过。 <!-- 2026-07-12 valid -->
- [ ] 6.2 tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注（代码/测试项已标 70b53e0）；archive（**gated**：landed+deployed+0.1 真机核后）。
