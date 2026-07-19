## 1. OpenSpec 与隔离开发

- [x] 1.1 完成 proposal/design/spec delta，并通过 `openspec validate persona-like-affinity --strict`
  <!-- control worktree: initial strict validation passed on 2026-07-19. -->
- [x] 1.2 为 aidcp-edge 与 aidcp-cloud 建立同名隔离 worktree，确认不触碰 canonical checkout 的既有改动
  <!-- scripts/new-change created isolated edge/cloud worktrees from origin defaults; canonical control/edge untracked and modified files remain untouched. -->

## 2. aidcp-edge 客户端

- [x] 2.1 在账号人设向导的语气调性下方增加“点赞倾向”三档单选面板，默认“正常”，补齐样式与无障碍状态
- [x] 2.2 采集/预览中文档位并通过受控 `like_affinity:*` 标记随既有 `keywordSelections` 发送
- [x] 2.3 补充 renderer/persona UI 回归，覆盖位置、默认档、单选、摘要和请求标记
  <!-- aidcp-edge focused fleet-console 46/46; full suite 1834/1834; typecheck passed. -->

## 3. aidcp-cloud 人设模板

- [x] 3.1 为 `behavior_guidelines` 增加可选严格枚举 `like_affinity`，实现 loader/serializer/模板往返与历史缺省兼容
- [x] 3.2 解析并剥离受控档位标记，生成人设后确定性补齐与兴趣及档位匹配的 behavior guidelines，保证不生成 mandatory rules
- [x] 3.3 补充 soul 与 persona generator 测试，覆盖三档、旧客户端、未知标记、token 不污染和强制点赞零生成
  <!-- aidcp-cloud persona/soul focused coverage passed; invalid enum fails closed and missing field resolves to normal. -->

## 4. aidcp-cloud 普通点赞倾向

- [x] 4.1 在笔记互动 prompt/persona source 中注入三档软倾向，保持 pass、预算、冷却、风控与 mandatory 边界
- [x] 4.2 将评论点赞 Bernoulli 默认概率按三档映射为 0.60/0.75/0.90，保留显式注入和所有既有硬闸
- [x] 4.3 补充互动与评论点赞回归，证明档位单调、正常档兼容以及高档位不强制执行
  <!-- aidcp-cloud focused persona/interaction/comment-like 42/42; acceptance 59/59; actual full suite 2538 pass, 0 fail, 8 gated skips. -->

## 5. 验证、集成与交付

- [x] 5.1 Edge 运行定向测试、全量测试与 typecheck；Cloud 先验收/定向，再全量测试与 typecheck
  <!-- Windows note: package `npm test` preserved single quotes and discovered 0 tests, so Cloud full verification used `.\\node_modules\\.bin\\tsx.cmd --test test/**/*.test.ts`; 2546 discovered, 2538 pass, 8 gated skip, 0 fail. -->
- [ ] 5.2 更新 tasks 证据并再次严格校验 OpenSpec；分别提交隔离 worktree
- [ ] 5.3 用 `scripts/land-change` 串行 rebase/验证/ff 推送默认分支，保留 canonical 既有本地改动
- [ ] 5.4 按规范从 Cloud canonical checkout 部署 dev 并完成服务/监听/health/飞书/PostgreSQL 检查；Edge 不构建安装包
- [ ] 5.5 记录提交、验证、部署与偏差，归档并推送 OpenSpec change
