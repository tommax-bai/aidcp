## Why

2026-07-11 把 dev/OL 角色对调、定死「主干开发、分支上线」模型：OL（`123.56.253.183`）转稳定生产、只从 `release/<yyyymmdd>-<scope>` 分支部署；dev（`121.89.85.150`）转不稳定主干测试位。这套规则当时只写进了人读文档 `docs/deployment-environments.md`（控制仓 main `06e69aa`），**尚未进 openspec 契约**——`deployment-environments` spec 里现有的 "Ol deployments must come from release branches" 只覆盖「OL 必须从 release 分支的干净 checkout 部署、不得从脏树/feature/默认分支/tag/SHA 直接部署」，**缺**几条本次已在真实操作里被依赖的硬约束：

- release 分支的**命名规范**（`release/<yyyymmdd>-<scope>`、从干净已提交 SHA 切）。
- release 分支**不可变、只进不退**：作为部署 ref of record 保留不删；只能 fast-forward 向前推（热修），**绝不 force-push / rebase / reset 重写历史**。
- 被取代后的 release 分支**保留 / 清理策略**。
- 「主干开发、分支上线」的**环境角色模型**（master=dev 不稳定主干、OL=只从 release 稳定生产）与**隔离分支合并纪律**（要保 OL 干净，必须先从「合并前的主干」切好 release 并部署，再把 feature 合进主干）。
- **edge 安装包**为何**不切 release 分支**：OL 包靠构建期 flag（`cloud_default_env=ol`）从主干出，主干保持 dev-default（零回归），不维护长命分支承载默认端点。

本 change 把上述规则正式沉淀进 `deployment-environments` spec，使其成为一等契约而非文档散文。规则本身已在 2026-07-11 的 OL 稳定化 + 0.3.18 安装包上架里实操验证（cloud/console `release/20260711-ol-stable`、console release 用 ff 向前推一格做 0.3.18 下载页 bump），本 change 只做**契约化**，不改任何运行时代码。

## What Changes

- **新增 spec 需求：主干开发 / 分支上线的环境角色模型 + 隔离分支合并纪律**。明确主干（各 sub-repo 默认分支）落地即部署 dev、dev 允许承载不稳定内容；OL 是稳定生产、只从 release 分支部署；合并隔离 feature 回主干时，若要保 OL 干净，必须先从合并前主干切 release 并部署，合并只推进主干、绝不回改已钉死的 release 分支或已部署的 OL 运行时。
- **新增 spec 需求：release 分支 append-only、保留、可清理**。命名 `release/<yyyymmdd>-<scope>`、从干净已提交 trunk commit（分支尖 / tag / SHA）切；作为在役 OL 部署 ref 时保留不删；向前推按 **append-only**——热修是 release tip 严格后代时可 fast-forward，否则（trunk 已合入 OL 须排除的内容）以追加提交（cherry-pick）落到 release 分支、绝不把被排除内容拖进 OL；**任何情形都绝不 force-push / rebase / reset 重写已发布历史**；被新 release 取代且不再是部署 ref 后方可归档 / 删除。（评审揪出初版「ONLY fast-forward」会使隔离热修不可能且与 append-only 自相矛盾，已改。）
- **新增 spec 需求：OL edge 安装包默认云环境靠构建期选择、不靠长命分支**。只到 **property 层**（不把具体 flag 名 / 打包管线钉进契约，避免 mechanism-as-contract 引发 MODIFIED 漂移）：主干保持 dev-default（零回归）、OL 目标靠对主干施加构建期选择产出；不维护「只为承载 OL 默认端点」的长命 edge 分支；OL release 记录里 edge 的 ref of record = 所建 trunk commit + 构建期选择。**显式声明 edge 是 release-branch 部署强制的例外**（edge 是分发工件、非 OL ECS 运行时部署），化解与现有 "Ol deployments must come from release branches"（把 edge 计入 OL release 工件）的冲突。
- **不改动**现有需求文本（避免 MODIFIED header 漂移风险）：新规则全部以 `## ADDED Requirements` 追加，与现有 "Ol deployments must come from release branches" 互补（后者管「部署源合法性」，新需求管「分支生命周期 + 环境模型 + 合并纪律 + edge 例外」），且 Req A/C 以 cross-reference 指向现有需求而非重述其 SHALL，保持单一规范来源。

## Capabilities

### New Capabilities
<!-- 无新增独立能力：本 change 是对既有 deployment-environments 能力的规则补全，按 YAGNI 不新造能力/抽象。 -->

### Modified Capabilities
- `deployment-environments`：把「主干开发、分支上线」模型、release 分支不可变/只进不退/保留清理纪律、隔离分支合并顺序纪律、以及 OL edge 安装包靠构建 flag（非长命分支）三组规则追加为一等 spec 需求。现有部署目标 / 部署源合法性 / 运行时隔离 / 凭据出仓 / edge·console 选目标 / 首次 OL bootstrap 六条需求**不改**。

## Impact

- **控制仓 aidcp（本仓）**：新增 `openspec/changes/deployment-release-branch-policy/`（proposal + design + specs delta + tasks）；archive 时 delta 并入 `openspec/specs/deployment-environments/spec.md`。`docs/deployment-environments.md`（main `06e69aa`）已含「主干开发 / 分支上线模型 + 合并纪律」的散文，但 **release 分支 append-only / 禁 force-push / 清理时机 / 命名强制** 几条 docs 尚未覆盖——本 change **顺带补齐这几条 docs 条款**使其与新 spec 一致（评审揪出初版声称「docs 已等价、只核对」不准确，已改为实际补齐）。
- **无 sub-repo 代码改动**：cloud / edge / console 均不动；协议（AC-PROTO）、风控（AC-RISK）、发布（AC-PUB）红线无关；无 DB 迁移；无 ECS 部署（纯契约文档）。
- **不改运行时行为**：规则描述的正是 2026-07-11 已落地的现状（OL 跑 `release/20260711-ol-stable`、edge OL 包靠构建 flag、FB 已合回主干部署 dev）；本 change 使其可被 `openspec validate --strict` 校验、可被后续操作引用为契约。
- **验证**：`openspec validate deployment-release-branch-policy --strict` 必过；archive 后 `openspec list --specs` 中 `deployment-environments` 需求数由 6 增至 9。
