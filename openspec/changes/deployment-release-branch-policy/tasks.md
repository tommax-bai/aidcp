# Tasks: deployment-release-branch-policy

> 纯控制仓（aidcp）契约 / 文档 change，无 edge/cloud 代码、无 ECS 部署。

## 1. aidcp（控制仓）— spec 契约化

- [x] 1.1 写 proposal.md（Why / What Changes / Capabilities: Modified deployment-environments / Impact） <!-- aidcp additive 目录，无 sha（随本 change 提交） -->
- [x] 1.2 写 specs/deployment-environments delta：三条 `## ADDED Requirements`（① 主干开发/分支上线模型 + 合并纪律；② release 分支不可变/只进不退/保留清理；③ OL edge 包靠构建 flag 非长命分支），英文以匹配现有 spec <!-- aidcp -->
- [x] 1.3 写 design.md（业界方案映射 / 决策 / 风险 / 迁移） <!-- aidcp -->
- [x] 1.4 `openspec validate deployment-release-branch-policy --strict` 通过（3 需求 / 10 scenarios）
- [x] 1.5 对抗评审（3 视角：防过度设计 / 查与现有 6 条需求冲突 / 补失败模式），按 findings 修订 delta：Req B「only ff」→ append-only（隔离热修用 cherry-pick 追加）、Req C property 化 + 显式声明为 release-branch 例外 + 定义 edge provenance、Req A 软化「SHALL deploy dev」+ 降冗余 SHALL 为 cross-reference + 折叠近同义 scenario <!-- workflow wf_93b713e0-898 -->
- [x] 1.6 **补齐** `docs/deployment-environments.md`：「分支上线」条加 append-only（ff 后代 / 否则 cherry-pick 追加）+ 禁 force-push/rebase/reset + 清理时机 + edge 例外指针；Ol deploy flow step 2 去「such as」规范化命名 + append-only；顺手改正已过期的域名切换「尚待两步」状态（DNS+安装包实已完成）——使 docs 与新 spec 一致 <!-- aidcp docs/deployment-environments.md -->
- [x] 1.7 commit + push 到 origin/main <!-- 见下方 commit sha -->
- 备注：本 change 待后续分诊清账时 archive（见 §2.1）。
- [ ] 1.7 commit + push 到 origin/main

## 2. 后续（本 change 不做，登记备忘）

- [ ] 2.1 archive 本 change（delta 并入 `openspec/specs/deployment-environments/spec.md`，需求数 6→9）——完成即随分诊清账走
- [ ] 2.2（可选 follow-up，非本 change）为「release 分支只进不退」加 CI/hook 自动 enforcement，防 force-push/rebase；YAGNI 暂缓
