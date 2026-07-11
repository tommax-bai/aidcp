> **P0 安全修复**：现网今天就可能加错群（推荐栏异群 join 被误点）。edge-only、无协议、无云端。单独即让 pending 场景 fail-safe；是 L2（`facebook-join-actuation-decouple`）clickTarget 匹配的作用域前置。

> **2026-07-12 评审订正**：承重判据从「异群链接排除（黑名单、fail-open）」翻为「目标群头部块正向包含（白名单、fail-closed）」——真机 dump 证实推荐位 join 是兄弟裸 `div` 无异群 `href`、黑名单漏排会误点异群。异群链接（E1）与推荐轮播容器（E2）降为 corroborating 排除。头部块祖先判据须真机校准后方 land。

## 0. 实装前硬前置（真机确认探针）

- [ ] 0.1 **头部块祖先判据校准（承重、决定能否 land）**：真机捕获目标群头部块结构——群名主标题（`<h1>`/`[role="heading"][aria-level="1"]`）的祖先链、目标自身 Join 与推荐位 join 相对该块的位置——坐实「正向包含目标群头部块」能框住目标自身 Join 且推荐位 join 落块外。取窄=安全侧。**未坐实前不 land**（fail-closed「在域」判据不可凭猜）。
- [ ] 0.2 E1/E2 定档：捕获推荐栏 join 候选 `href`/祖先群链接（E1 群 id 比对）、推荐轮播容器结构标志（E2 选择器）。

## 1. aidcp-edge — 作用域 helper（语言无关）

- [ ] 1.1 目标群 id 解析：从 `location.pathname` 的 `/groups/<id>` 段取目标群 id；`numeric-id` / `vanity-slug` 两式规范化，解析失败返回 null（供点击腿 fail-closed）。
- [ ] 1.2 **候选作用域正向包含（D1 承重、fail-closed）**：定位目标群「头部/动作区」块（含群名主标题的头部/hero 容器，祖先判据见 0.1）；候选 `inTargetScope=true` **当且仅当**它是该块后代——头部块解析不出 → 无候选在域内（点击腿按 D3 fail-closed）。**默认出域**，不是默认在域。
- [ ] 1.3 **corroborating 排除（E1/E2，非承重）**：在 D1 正向包含之上再叠——E1 候选 `closest('a[href]')`（或自身 href）解析到 `/groups/<异于目标群 id>` 则 `inTargetScope=false`；E2 候选落在「发现更多小组 / 查看推荐小组」推荐轮播容器内则 `inTargetScope=false`。最终 `inTargetScope = D1正向包含 AND NOT E1 AND NOT E2`。E2 选择器待真机校准，未定档前只靠 D1+E1、不放宽 D1。

## 2. aidcp-edge — 点击腿 fail-closed（承重、安全）

- [ ] 2.1 `GROUP_JOIN_CLICK_JS`：`join` 节点选取**只在 `inTargetScope` 候选内**取文档序首个；**删除**「页面级文档序第一个 join」回落。
- [ ] 2.2 fail-closed：目标群 id 解析失败**或头部块解析不出** → `clicked:false, reason:'scope_unresolved'`，绝不页面级扫 join；作用域内无 join 候选 → `clicked:false, reason:'no_target_in_scope'`。绝不越域找 join 冒充点过。
- [ ] 2.3 保持既有 disabled 诚实 bail、`__FB_JOIN_CLICK__` 标记、坐标回报不变。

## 3. aidcp-edge — 观测腿标注作用域（不阻断上报）

- [ ] 3.1 `GROUP_JOIN_OBSERVE_JS`：每候选加 `inTargetScope`（同 D1 正向包含 + E1/E2 判据）；`mainCta`/`joinButton` 挑选**只在 `inTargetScope` 候选内**——推荐栏 join 绝不冒充群主 CTA。
- [ ] 3.2 **成员信号收窄（红线1 尾巴）**：`membershipSignals` 从页面级 `signals.slice(0,8)`（`join-executor.ts:361`）改为**只在目标群头部块内读取**——推荐位某个建议群「已加入」信号绝不污染、绝不使点后 `hasMemberSignal` 对错群假成功。
- [ ] 3.3 候选清单**仍如实全量上报**（含 `inTargetScope:false`），不静默丢弃（守 L4 边缘不 fail-closed 丢原文）。
- [ ] 3.4 D5：作用域内控件 `ctaKind` 判不出 join/member/pending 时据实上报（原文 + `inTargetScope`），不越域找 join。

## 4. 测试（edge）

- [ ] 4.1 **红线（黑名单漏排 case，本次订正核心）**：页面有目标 pending「取消请求」+ 推荐位异群「加入小组」为**兄弟裸 `div[role=button]`、不带异群 `href` 祖先链接** → 点击腿绝不点推荐群 join、诚实 `no_target_in_scope`（正向包含默认出域挡住，非靠 E1）。
- [ ] 4.2 **红线（带异群链接 case）**：推荐位 join 带 `/groups/<异 id>` 祖先链接 → E1 亦排除、诚实 `no_target_in_scope`。
- [ ] 4.3 目标群自身可加入（Join 在头部块内）→ 正常点、坐标回报。
- [ ] 4.4 目标群已 member / pending（头部块内无 join）→ 诚实不点。
- [ ] 4.5 目标群 id 解析失败（畸形 URL）/ 头部块解析不出 → fail-closed `scope_unresolved`，绝不页面级点。
- [ ] 4.6 观测腿：`mainCta`/`joinButton` 挑选不取推荐栏候选；候选清单仍含 `inTargetScope:false` 项（全量上报）。
- [ ] 4.7 目标群自身钮在头部块内、或被指向**本群** id 的链接包裹 → 不误排（`inTargetScope=true`）。
- [ ] 4.8 **成员信号收窄**：推荐位建议群「已加入」信号在目标群头部块外 → 不进 `membershipSignals`、点后不对错群假成功。

## 5. 集成与部署（edge-only）

- [ ] 5.1 `npm run typecheck` + `npm run test:acceptance` + 全量 `npm test` 绿（改动前后跑安全红线 `AC-*`）。
- [ ] 5.2 edge master land（无 ECS/cloud 部署）。
- [ ] 5.3 真机验收登记 backlog：0.1/0.2 探针为实装前硬前置（已单列）；再核 pending/member/晚渲染三态作用域内不误点、可加入群正常、成员信号不被推荐位污染。归 FB 加群真机簇。

## 6. 收尾

- [ ] 6.1 `openspec validate facebook-join-candidate-scope-guard --strict` 通过。
- [ ] 6.2 tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注；archive（landed+deployed+真机核后）。
