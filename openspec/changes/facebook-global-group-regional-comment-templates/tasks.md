## 1. aidcp-cloud — 范围模型与版本化数据迁移

- [x] 1.1 在 Cloud kernel / panel DTO 中增加 `accountScopeMode=global|restricted`，保持旧 `accountGroupLabels` 请求按 restricted 兼容，并为矛盾范围提供具名整块拒绝。 <!-- aidcp-cloud 0137429；focused/full/typecheck 通过。 -->
- [x] 1.2 增加版本化 PostgreSQL migration：为 `facebook_group_target` 添加范围模式、创建区域通用模板权威表，并在事务内把迁移开始时全部现存群目标设为 global、保留共享库中供未升级 OL 使用的休眠映射并回读断言；为账号评论配置增加 `comment_mode_configured`，历史行标记为显式方案；同步 schema capability/DDL parity 元数据。 <!-- aidcp-cloud 0137429；0089/0090 expand migration、ownership/schema 门测试通过；共享库兼容映射为复核后偏差。 -->
- [x] 1.3 改造群目标 import、list、facets、批量范围写及真态回读，覆盖 global、restricted 多标签、restricted 空范围和未携带范围四种语义。 <!-- aidcp-cloud 0137429；store/panel/transport 测试通过。 -->
- [x] 1.4 改造候选计数、`nextJoinCandidate`、`claimNext` 与执行前重验，使 global 接受有分组/未分组的 Facebook 账号，同时保留投影新鲜度、平台、启用态、gating 和一群一账号锁。 <!-- aidcp-cloud 0137429；候选 SQL/锁/陈旧投影回归通过。 -->
- [x] 1.5 添加 store/migration 回归测试，证明 global 并发只认领一个账号、restricted 不回退、陈旧投影 fail-closed、迁移不改 membership/目标业务字段且失败整事务回滚。 <!-- aidcp-cloud 0137429；focused 185/185、full 3694 pass + 11 gated skip。 -->

## 2. aidcp-cloud — 区域通用模板与评论解析

- [x] 2.1 实现 automation 权威的区域通用模板存储、sanitize/整块校验、按区域读取和数据库真态回读，并接入 Cloud 组合根的既有命令/视图边界。 <!-- aidcp-cloud 0137429；automation store + internal port 已接线。 -->
- [x] 2.2 扩展 Panel API：读取区域模板目录、替换单区域完整模板集合，并为区域不存在、模板非法和权威不可用返回稳定原因。 <!-- aidcp-cloud 0137429；Panel HTTP 测试通过。 -->
- [x] 2.3 调整 Facebook 账号评论配置默认、内部 sync-read 快照和正文来源解析：独立持久化/传播是否显式设置方案；显式 generated 优先，显式 template 的账号模板优先，账号模板为空或无显式方案时在目标群确定后按 `group_url -> region` 读取通用模板。 <!-- aidcp-cloud 0137429；config/sync-read/scheduler 测试通过。 -->
- [x] 2.4 删除选群前的 `empty_template` 错误早退，增加 `missing_group_region` / `regional_template_missing` 等诚实非提交审计，同时保留关键词、正文校验、审批、联系方式、风险与平台确认边界。 <!-- aidcp-cloud 0137429；保留主干空关键词首帖模式，无 Edge/协议改动。 -->
- [x] 2.5 添加配置/API/调度器测试，覆盖账号模板优先、未设方案默认模板、区域兜底、显式 generated 不被覆盖、无区域/无模板 no-op、空关键词首帖模式及非法通用模板被既有校验拒绝。 <!-- aidcp-cloud 0137429；相关 scheduler/config 用例全绿。 -->

## 3. aidcp-console — 群组范围与通用模板管理

- [x] 3.1 更新 Console API 类型和群列表渲染，明确显示“全局分组”“指定账号分组”“未设置适用分组”，并增加范围模式筛选。 <!-- aidcp-console a369544；页面测试通过。 -->
- [x] 3.2 更新单条/CSV 导入与批量范围编辑为互斥 global/restricted 选择；保留未携带范围、显式受限空集合和旧导入兼容语义，所有成功提示使用服务端回读。 <!-- aidcp-console a369544；导入/批量范围测试通过。 -->
- [x] 3.3 在 `/facebook-groups` 增加按现有 region 编辑多条通用评论模板的配置区，展示数据库更新时间/更新人及具名保存错误。 <!-- aidcp-console a369544；区域模板组件与回读已接线。 -->
- [x] 3.4 添加 Console 组件/API 测试，覆盖三态展示、全局筛选/批量设置、导入范围语义、区域模板回填/sanitize/保存失败不冒充成功。 <!-- aidcp-console a369544；full 283 pass + 1 skip，typecheck/build 通过。 -->

## 4. 验证、集成与 DEV 交付

- [x] 4.1 在各 owning repo 的同名隔离 worktree 安装物理依赖，运行 Cloud 相关 acceptance/focused tests、完整测试和 typecheck；运行 Console focused/full tests、typecheck 和 production build。 <!-- Cloud 0137429：3705 total/3694 pass/11 gated skip；Console a369544：284 total/283 pass/1 skip；两仓 typecheck 与 Console build 通过。 -->
- [x] 4.2 更新本任务完成项的 repo、commit SHA、验证与偏差注释，并运行 `openspec validate facebook-global-group-regional-comment-templates --strict`。 <!-- 2026-07-27 strict validate 通过；共享库映射兼容与主干空关键词首帖语义已回写 design/spec。 -->
- [ ] 4.3 将 Cloud/Console 分支分别 rebase 到最新默认分支，串行 fast-forward 集成并推送；控制仓 OpenSpec 记录同步提交并推送 main。
- [ ] 4.4 DEV 部署前运行 `scripts/deploy-target dev --check`、只读统计现存目标/范围/membership 并完成数据库与应用备份；禁止触碰 OL 和无关 `isales` 服务。
- [ ] 4.5 部署 Cloud migration/runtime 与 Console 静态资源到 DEV，核验 migration ledger、全部迁移前目标为 global、兼容映射逐行未变、membership/关键字段计数不变，以及 service/listener/health/Feishu/PostgreSQL/页面资源。
- [ ] 4.6 用 DEV 只读 API/数据库证明已分组与未分组 Facebook 账号均能获得 global 候选计数、restricted 仍按标签限制、区域模板读写真态可见；未经单独真实账号写验收授权，不执行真实加群或真实评论。
