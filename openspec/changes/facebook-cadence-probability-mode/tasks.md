# Tasks: facebook-cadence-probability-mode

## 1. aidcp-kernel — 类型与校验器(→ tag v0.1.5)

- [x] 1.1 `facebook-operation-policy-resolution.ts`:`FacebookCadenceMode` 类型 + `FACEBOOK_CADENCE_MODES` 常量;`FacebookOperationPolicyBaseProjection` 加 `cadenceMode`(wire 可选,producer 必填,消费方缺省回落 fixed)。 <!-- aidcp-kernel ae4f045 -->
- [x] 1.2 `sync-read-facts.ts` 的 `isFacebookOperationBaseline`:接受 11 键(旧)与 12 键(新)两种精确键集;含 `cadenceMode` 时必须合法枚举值。 <!-- aidcp-kernel ae4f045 -->
- [x] 1.3 kernel 测试 + `npm test`/typecheck 绿;bump 0.1.5、annotated tag `v0.1.5`、push。 <!-- aidcp-kernel ae4f045 · tag v0.1.5 · 81/0 -->

## 2. aidcp-api — 存储 / 面板 / 迁移 / 镜像

- [x] 2.1 迁移 `0118_facebook_cadence_mode.sql`:全局表加 `cadence_mode TEXT NOT NULL DEFAULT 'fixed' CHECK` + `config_mirror_version` 的 `facebook_operation_policy` 行 version +1(样板 0108)。 <!-- aidcp-api d63f0c3 -->
- [x] 2.2 kernel pin 抬 `#v0.1.5`(`npm update` 重解析,核 lock sha + dist 标志物)。 <!-- aidcp-api d63f0c3 -->
- [x] 2.3 store:schema 探针列 + SELECT + view(`cadenceMode`)+ `normalizedGlobalWrite` 校验(缺省保持现值)+ UPDATE + 审计快照 + 模式变更触发级联传播 + `baselineForEnv` 逐字段加 `cadenceMode` + schemaVersion `@4`。 <!-- aidcp-api d63f0c3 -->
- [x] 2.4 panel PUT `hasExactlyKeys` 加可选 `cadenceMode`(旧前端不发=保持现值)、GET 透出;store 测试补 3 断言(缺省保持/翻转级联/非法先拒)。 <!-- aidcp-api d63f0c3 -->
- [x] 2.5 api `test:acceptance` 28/0 + `test` 587/0 + typecheck 干净。 <!-- aidcp-api d63f0c3 -->

## 3. aidcp-automation — 五处触发点 + 迁移 + schema 门

- [x] 3.1 kernel pin 抬 `#v0.1.5`;镜像消费侧缺 `cadenceMode` 回落 `fixed`(经 `resolveFacebookCadenceMode`)。 <!-- aidcp-automation 2445d49 -->
- [x] 3.2 迁移 `0119_facebook_rule_batch_includes_join.sql`:规则批次表加 `includes_join BOOLEAN`(NULL=旧行回落派生)。 <!-- aidcp-automation 2445d49 -->
- [x] 3.3 Reel 节奏(role-dispatcher):按 `decision.cadenceMode` 分支,probabilistic 每条合格 Reel 对 like/follow 各掷 `random()<1/N`;ordinal 照常推进。 <!-- aidcp-automation 2445d49 · 新增共享助手 src/orchestrator/facebook-cadence-mode.ts -->
- [x] 3.4 规则 store:`applyConfirmedView` 加 cadenceMode + random;view→like probabilistic 掷骰起批;批创建时掷 `includes_join` 落库,`batchFromDb` 优先读列 NULL 回落派生。 <!-- aidcp-automation 2445d49 -->
- [x] 3.5 消费:`advanceFacebookConsumptionCounters` reducer(likes→join/joins→comment)+ store viewsPerLike 按模式掷骰;cadenceMode 经 wiring 单点注入结算路径 + apply 路径经 decision 注入;random 注入。 <!-- aidcp-automation 2445d49 -->
- [x] 3.6 schema 门:`REQUIRED`/`KNOWN_MAX` 抬到 `0119`(store 读 includes_join 硬依赖,0108 先例)。 <!-- aidcp-automation 2445d49 -->
- [x] 3.7 单测:helper + reducer(fixed 零回归 + probabilistic 掷中/不中/清零/downstream 关)+ reel 概率(命中非固定第 N/全程不中无保底)+ boundary census 加新文件属主;`test` 2450/0 + acceptance 305/0 + typecheck 干净。 <!-- aidcp-automation 2445d49 · 新文件登记 fileOverrides + module-ownership -->

## 4. aidcp-console — 开关 UI

- [x] 4.1 `types/api.ts`:View/Write 加 `cadenceMode`;`FacebookCadenceMode` 枚举 label 进 `aidcp-enums.ts` 单源(labelOf 防漂移)。 <!-- aidcp-console a6ff45c -->
- [x] 4.2 `FacebookOperationGlobalPolicyEditor.tsx`:Modal 顶部新 section(Segmented fixed|probabilistic)+ 摘要卡模式 Tag + `draftFrom` + 提交体手写展开显式加字段;fixture + 提交断言测试。 <!-- aidcp-console a6ff45c -->
- [x] 4.3 console `test` 360/0 + typecheck + build 绿。 <!-- aidcp-console a6ff45c -->

## 5. 集成 / 部署 / 收尾

- [x] 5.1 四仓 worktree 集成回 master(rebase + ff)、push;kernel tag v0.1.5。 <!-- kernel ae4f045 / api d63f0c3 / automation 2445d49 / console a6ff45c 均已 origin/master -->
- [x] 5.2 部署 dev(sync-read 载荷形状变更,走 stop-api→migrate 0118→migrate 0119→start api→restart automation 的防漂移序;各服务备份 + blast radius diff = 恰为本 change 文件;随包送 kernel v0.1.5 node_modules;console 非-delete rsync)。 <!-- 2026-08-10 deployed:api 备份 api.bak.20260810... 门 0118/8090-8091-8093;automation 门 0119/8787-8094;无 drift/invalid_envelope;isales 未受影响;console live bundle index-CeWyIA_c.js/200 -->
- [x] 5.3 控制仓 tasks.md 回写 sha,`openspec validate --strict`。 <!-- 本次提交 -->
- [ ] 5.4 真机观察项登记 backlog(概率分布长期均值、模式切换重置)。 <!-- 已登记 docs/real-machine-acceptance-backlog.md 簇 157 -->
