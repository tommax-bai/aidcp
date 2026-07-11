## 1. aidcp-edge — 结构观测采集（无协议 parity 改动）

- [ ] 1.1 `src/facebook/join-executor.ts` 观测采集：群主体内「可聚焦发帖/评论 composer 存在」+「Join CTA 存在」+「Leave-group 可供性存在」三个语言无关结构布尔，写入 `observation`/`postObservation`（松类型 `unknown` 通道，非 `protocol.ts` parity 字段）。M3：composer 子树判别（群内发帖框 vs 无关输入框/搜索框）。
- [ ] 1.2 确认不动两份 `src/comm/protocol.ts` parity 类型、不加 `MessageType`、不动 `GroupJoinPayload`（`AC-PROTO` 不涉及）。

## 2. aidcp-edge — 结构后置校验（防新 false-positive）

- [ ] 2.1 承重闸（点后单帧事实）：judged joined 要求点后观测**有可聚焦 composer 且群主体内无可见 Join CTA**；跃迁用**同一次 `click=true` 导航内**的 pre/post 观测对佐证（非独立 observe-only 调用）。
- [ ] 2.2 顺序：pending/问卷检测**先于** joined 判（Join→Pending + composer 判 pending 不判 joined）。
- [ ] 2.3 observe 期：裸 composer **不得**翻 `already_member`；observe 期 `already_member` 仍需正向成员信号（词表命中，或 composer + 无可见 Join CTA）。
- [ ] 2.4 红线兜底：点后单帧事实不满足且词表无正向命中 → honest not-joined / retry，MUST NOT assume-joined。
- [ ] 2.5 慢渲染走既有 post-click readiness retry tier，不当终局失败。

## 3. aidcp-cloud — 裁判结构主判（结构字段透传，接线要点）

- [ ] 3.1 **把结构字段（composer/Join-CTA/Leave present）+ 同调用 pre 观测喂给云端 `evaluatePostClick`**（现只收 post 观测、无结构字段）——否则云端仍按未知语种成员标签回 `failed`、AND 门下仍重复加群（change 目标落空）。
- [ ] 3.2 云端裁判用点后单帧事实主判 joined、pending 先于 joined；词表保留为正向补充 + drift-guard 不变。
- [ ] 3.3 确认非成员组（composer 在但 Join CTA 仍可见）不被裁为 joined。

## 4. 测试

- [ ] 4.1 edge：本地语已加入 + 点后有 composer 且无可见 Join CTA → judged joined（消灭 `join_failed` 重复加群）用例。
- [ ] 4.2 edge：公开组非成员见 composer 但 Join CTA 仍可见 → 不判 joined、observe 期不翻 `already_member`、照常尝试 Join 用例（防新 false-positive）。
- [ ] 4.3 edge：Join→Pending + composer → 判 pending 不判 joined 用例（pending 先判）；结构事实与词表都无信号 → honest not-joined 用例；decorated English 成员标签仍被词表 contains 命中用例（回归）。
- [ ] 4.4 cloud：`evaluatePostClick` 收到结构字段后按点后单帧事实主判 joined、pending 先判用例；词表正向补充 + drift-guard 回归不变。
- [ ] 4.5 两仓 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck` 全绿。

## 5. 集成与部署

- [ ] 5.1 edge master land + cloud dev 部署（`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。无协议改动，冲突面仅加群文件、rebase 后 land 即可。
- [ ] 5.2 真机验收登记 backlog（判定准确率门：结构主判消灭重复加群、composer 子树判别不误伤非成员组）——不阻塞码级。

## 6. 收尾

- [ ] 6.1 `openspec validate facebook-join-structural-verify --strict` 通过。
- [ ] 6.2 tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注；archive。
