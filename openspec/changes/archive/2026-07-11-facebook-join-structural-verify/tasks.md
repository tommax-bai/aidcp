> **实装说明（对抗评审修正）**：初版结构判据 `composerPresent && !joinCtaPresent` 被评审揪出 fail-open（`joinCtaPresent` 词表派生、未覆盖语种漏 → 非成员误判 joined；且 observe/pre-click 结构 already_member 会没点击就 markJoined 污染账本）。**已改为**：承重 = 语言无关「跃迁」（composer 点前无、点后有），`!joinCtaPresent`/`!loading` 仅 corroborating；**删除 observe/pre-click 结构判定**（仅 post-click）。下方任务按最终实现标注。

## 1. aidcp-edge — 结构观测采集（无协议 parity 改动）

- [x] 1.1 `src/facebook/join-executor.ts` 观测采集：`composerPresent`（`[role=main]` 内可聚焦 `[contenteditable]`/`[role=textbox]`，排除顶栏/导航/侧栏/搜索，无 main 时 fail-closed）+ `joinCtaPresent`（分类到的 join 节点存在），写入 `observation`/`postObservation`（松类型 `unknown` 通道）。M3 子树判别按 aria/placeholder 排除搜索框。<!-- aidcp-edge 1442783 composerPresent/joinCtaPresent 观测字段 -->
- [x] 1.2 确认不动两份 `src/comm/protocol.ts` parity 类型、不加 `MessageType`、不动 `GroupJoinPayload`（`AC-PROTO` 不涉及；观测走 `ActionCompletedPayload.observation?: unknown`）。<!-- aidcp-edge 1442783 -->

## 2. aidcp-edge — 结构后置校验（承重=语言无关跃迁）

- [x] 2.1 `structuralJoinConfirmed(pre, post)`：承重 = **跃迁**（`pre?.composerPresent !== true && post.composerPresent && post.joinCtaPresent !== true && post.documentReady !== 'loading'`）；用同一次 `click=true` 导航内的 pre/post 观测对。<!-- aidcp-edge 1442783 承重改跃迁、非 no-CTA 单帧事实 -->
- [x] 2.2 顺序：pending/问卷检测**先于** joined 判（Join→Pending + composer 判 pending 不判 joined）。<!-- aidcp-edge 1442783 -->
- [x] 2.3 observe 期：**删除据结构判 `already_member`**（评审修正：无点击不 markJoined）；observe 期 `already_member` 仅词表 `hasMemberSignal`；`isDecisiveObservation` 移除结构项。<!-- aidcp-edge 1442783 -->
- [x] 2.4 红线兜底：跃迁与词表都无正向命中 → honest not-joined / retry，MUST NOT assume-joined。<!-- aidcp-edge 1442783 -->
- [x] 2.5 慢渲染走既有 post-click readiness retry tier，不当终局失败（未改动，延用）。<!-- aidcp-edge 1442783 -->

## 3. aidcp-cloud — 裁判结构主判（结构字段透传，接线要点）

- [x] 3.1 `evaluatePostClick(post, preObs?)` 收同调用 pre 观测；scheduler 传 `clicked.observation`。结构字段随观测松通道流入（`asObservation` cast 不剥字段）。<!-- aidcp-cloud 6ce347e 透传 pre 观测 + 结构字段 -->
- [x] 3.2 云端裁判用**跃迁**主判 joined、pending 先于 joined；**删除 pre-click 结构 already_member**；词表保留为正向补充 + drift-guard 不变；LLM prompt 补 composer/joinCta 信号兜公开组子案。<!-- aidcp-cloud 6ce347e -->
- [x] 3.3 确认非成员（点前已有 composer 无跃迁 / Join CTA 仍在）不被裁为 joined。<!-- aidcp-cloud 6ce347e 红线回归测试 -->

## 4. 测试

- [x] 4.1 edge：跃迁（点前无 composer→点后有、词表未命中语种）→ judged joined（消灭重复加群）。<!-- aidcp-edge 1442783 -->
- [x] 4.2 edge 红线：非成员公开组点前已有 composer（无跃迁）→ 不判 joined；未覆盖语种非成员 observe → 绝不 `already_member`。<!-- aidcp-edge 1442783 防 fail-open false-positive -->
- [x] 4.3 edge：Join→Pending + composer → pending（pending 先判）；无跃迁无词表 → honest not-joined；decorated English 成员标签词表 contains（回归）；`structuralJoinConfirmed` 纯函数。<!-- aidcp-edge 1442783 -->
- [x] 4.4 cloud：跃迁 → 确定性 joined、pending 先判；点前已有 composer / pre-click 有 composer 均绝不 joined/already_member（红线）；drift-guard 回归不变。<!-- aidcp-cloud 6ce347e -->
- [x] 4.5 两仓 `test:acceptance`（edge 16 / cloud 47）→ 全量（edge 1000 / cloud 1807）→ typecheck 全绿。<!-- 2026-07-11 -->

## 5. 集成与部署

- [x] 5.1 edge master land（1442783）+ cloud dev 部署（deploy-target dev check → tar 备份 + .env.bak → 外科 rsync 2 文件 md5 核对 → restart → healthcheck 全过：active/8787/飞书长连/无 error）。无协议改动、rebase 后 ff land。<!-- aidcp-edge 1442783 / aidcp-cloud 6ce347e --> <!-- 2026-07-11 deployed(dev cloud + edge master) -->
- [x] 5.2 真机验收登记 backlog（结构主判消灭重复加群 / composer 子树判别 / 渲染时序残留 / 公开组点前 composer 靠 LLM 兜）。<!-- 2026-07-11 backlog -->

## 6. 收尾

- [x] 6.1 `openspec validate facebook-join-structural-verify --strict` 通过。<!-- 2026-07-11 -->
- [x] 6.2 tasks.md 勾选 + sha 标注；archive。<!-- 2026-07-11 -->
