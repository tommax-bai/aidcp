## Context

`deployment-environments` spec 已有六条需求，其中 "Ol deployments must come from release branches" 管住了「OL 部署源必须合法」（干净 checkout、非脏树/feature/默认分支/tag/SHA 直接部署）。但 2026-07-11 定死的「主干开发、分支上线」模型里，有几条被真实操作依赖、却只落在人读文档、未进契约的规则。本 change 把它们契约化。

坐实的现状（`文件:行` / ref）：
- 现有需求：`openspec/specs/deployment-environments/spec.md` 的 "Ol deployments must come from release branches"（部署源合法性，已覆盖）。
- 人读文档已含等价散文：`docs/deployment-environments.md`「角色与发布模型」节（控制仓 main `06e69aa`）。
- 实操验证：OL 跑 cloud/console `release/20260711-ol-stable`（cloud `3177735` / console `0c8db0c`）；console release 分支用 **fast-forward** 向前推一格做 0.3.18 下载页 bump（`6bce66d→0c8db0c`）——正是「只进不退」规则的活例。
- edge 机制：OL 安装包靠构建期 `extraMetadata.aidcpCloudDefaultEnv=ol`（烘进包内 `package.json`，启动读取注入 `AIDCP_CLOUD_URL=ol`、`fromSelection:true` 保证芯片=实连），主干缺省=dev（零回归）。

## Goals / Non-Goals

**Goals**
- 把三组规则升为一等 spec 需求：① 主干开发/分支上线的环境角色模型 + 隔离分支合并纪律；② release 分支不可变、只进不退、保留/清理；③ OL edge 包靠构建 flag 非长命分支。
- 纯 additive（`## ADDED Requirements`），不改现有需求文本，规避 archive 时 MODIFIED header 匹配失败（见 memory `openspec-archive-batch-mechanics`）。

**Non-Goals**
- 不改运行时代码、协议、DB、部署形态。
- 不重述已被 "Ol deployments must come from release branches" 覆盖的「部署源合法性」（避免重复需求）。
- 不引入自动化 enforcement（如 CI 拦 force-push）——YAGNI；规则先立为契约，enforcement 是后续可选 follow-up。

## Decisions

**决策 1：三条 ADDED 需求，不 MODIFY 现有需求。**
现有 "Ol deployments must come from release branches" 管「部署源」，新需求管「分支生命周期 + 环境模型 + 合并纪律」，职责正交、可并存。ADDED 优于 MODIFY：archive 合并靠 header 精确匹配，MODIFY 一旦措辞漂移就 merge 失败（memory 有实例）；additive 无此风险。

**决策 2：spec delta 用英文，proposal/design/tasks 用中文。**
`deployment-environments` spec 现有全文英文，delta 合并进同一文件须同语言以保连贯；面向人的 proposal/design/tasks 按项目默认中文。

**决策 3：release 分支用 append-only 定义，不是 fast-forward-only。**
release 分支要能收热修（如 console 0.3.18 bump 就是一次 ff），一刀切「冻结不可写」不现实。**关键约束（对抗评审揪出）**：本 change 的隔离模型里，OL release 从「合并前 trunk」切出、之后 trunk 合入了 OL 须排除的 feature——此时 trunk 上的热修已**不是 release tip 的严格后代**，若强行 fast-forward 会把被排除的 feature 一并拖进 OL；而唯一正确落法是把热修**追加**到 release 分支（cherry-pick），这是 append-only 但**不是** fast-forward。所以初版「ONLY fast-forward」既使隔离热修不可能、又与「append-only」自相矛盾。定案规则=**append-only 向前**：是严格后代时可 ff，否则以追加提交落（绝不拖入被排除内容）；任何情形都禁 force-push/rebase/reset 重写已发布历史。

**决策 4：edge 需求只到 property 层 + 显式声明为 release-branch 例外。**
它是「分支上线」模型的边界澄清：cloud/console 的 OL ECS 运行时用 release 分支，edge 安装包**不用**（edge 是分发工件、非 ECS 运行时部署）。两点评审修正：① **不把具体 flag 名 / extraMetadata / 启动读取 打包管线钉进 SHALL**——那是 mechanism-as-contract，edge 一改机制就逼着 MODIFY 本需求、正是想规避的 header 漂移；契约只断言 property（OL 目标靠对主干的构建期选择产出、主干保持 dev-default），具体 flag 名留给 edge docs 自由演进。② **显式声明 edge 是现有 "Ol deployments must come from release branches" 的例外**并定义 edge 的 OL provenance = trunk commit + 构建期选择——否则现有需求（把 edge 计入 OL release 工件、要求来自 release 分支）与「edge 从 trunk 构建」在合并后的 spec 里自相矛盾。与现有 "Edge and console must select the intended target"（管「不得静默连 dev」红线、芯片=实连）互补、不重述其运行时不变量。

## Risks / Trade-offs

- **风险：新需求与现有需求语义重叠被指冗余。** 缓解=职责边界写清（部署源 vs 生命周期 vs 机制），scenario 不复述对方覆盖面。
- **风险：规则无自动 enforcement，靠纪律。** 接受（YAGNI）；本 change 目标是「立契约」，force-push 早已受 §6/§7 纪律约束，spec 化让它可被引用与校验。future follow-up 可加 CI 守卫。
- **Trade-off：edge flag 条目略超「release 分支」窄题。** 保留，因为它正是「为什么 edge 不切 release 分支」的答案，补全模型边界、防误维护长命分支。

## Migration Plan

1. 写 proposal + spec delta（英文 ADDED）+ tasks（本 change）。
2. `openspec validate deployment-release-branch-policy --strict` 过。
3. 对抗评审（防过度设计 / 查与现有需求冲突 / 补失败模式）——三视角揪出 Req B「only ff」自相矛盾、Req C mechanism-as-contract + 与 Req 2 冲突、Req A 过度断言、docs 漂移，已全部据此修订。
4. **补齐** `docs/deployment-environments.md` 缺失的 append-only / 禁 force-push / 清理时机 / 命名强制 条款（非空口核对），使 docs 与新 spec 一致。
5. commit + push main。
6. 后续 archive 时 delta 并入主 spec（需求数 6→9）。
