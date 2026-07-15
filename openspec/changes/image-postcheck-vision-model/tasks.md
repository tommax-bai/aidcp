# Tasks — image-postcheck-vision-model

## 1. Contract and storage

- [x] 1.1 定义整组视觉分析、类型专用 frame spec、风格聚类、逐槽参考绑定和视觉审计类型；所有新字段对历史数据可选/null-safe。
- [x] 1.2 `curated_content` 启动 schema 新增视觉分析 JSONB；以图片抓取锚 + provider/model/schema version 为 cache key，缓存命中零模型调用、失败不伪造成功。
- [x] 1.3 精选读取/洗稿触发透传缓存结果；不把 OCR 文本或原图具体文案纳入视觉分析契约。

## 2. aidcp-cloud — visual reverse analysis

- [x] 2.1 新增 `VisualReferenceAnalyzer`：整组分类/序列/聚类 → 按摄影、插画/3D、文字卡、UI/文档、图表信息图、混合类型分组专用分析 → 汇总 `setStyleBible + styleClusters + frameSpecs`。
- [x] 2.2 严格 JSON 解析、调用超时、分组有界并发、token usage 记账与诚实 `unavailable/partial` 状态；默认旗标关闭并支持影子落库。
- [x] 2.3 管线角色恒写键并接入 planner/composer；反推可用时源风格优先，现有内容品类风格仅作兜底。

## 3. aidcp-cloud — slot binding and provider

- [x] 3.1 `ImageSetPlanner` 按有效源图顺序产出 sourceArrayIndex/sourceIndex，视觉反推产出 sequenceRole；1/3/8/9 图均保持槽位顺序且图 0 仍为封面/钩子位。
- [x] 3.2 `ImagePlan` 为每槽生成独立参考绑定；默认仅绑定该槽主参考，绝不再把整组参考图传给每槽。
- [x] 3.3 Wan 多图请求明确各图片角色并保证主参考图最后；provider 返回真实参考使用状态，失败不进入发布 URL。
- [x] 3.4 文字卡保留确定性渲染；UI/文档、图表、混合类记录诚实路由状态，未接结构化重绘器时不得标为 deterministic redraw。

## 4. aidcp-cloud — visual fidelity audit

- [x] 4.1 新增 `VisualFidelityAuditor`，比较主参考与生成图，输出形态/主体/构图/色彩/风格分数及真人、乱码、水印、逐字复制/原创风险。
- [x] 4.2 不通过时每槽有界重生成一次；重试仍失败则丢弃该槽。视觉模型不可用时标 `unverified`，MUST NOT 假 pass。
- [x] 4.3 逐槽绑定、路由、分析来源和审计结果汇总到 `ImageDirective`/发布 metadata，M<N 继续按既有保序语义发布。

## 5. aidcp-console — explainable audit

- [x] 5.1 精选素材详情显示视觉分析状态、风格来源、类型/风格簇与缓存模型；旧行无字段时显示未分析、不报错。
- [x] 5.2 发布详情显示 source→output 槽位绑定、生成路由、是否使用参考图、逐槽评分/风险/重试与未核验原因；不得把 `used` 等同于“保真通过”。

## 6. Verification and rollout

- [x] 6.1 单测覆盖严格解析、缓存命中/失效、非摄影字段差异、失败诚实状态、源风格优先与旧行为 flag-off 回归。
- [x] 6.2 单测覆盖 1/3/8/9 图顺序、每槽独立绑定、Wan 主参考最后、缺图保序、文字卡回归。
- [x] 6.3 单测覆盖 audit pass/fail/retry/unavailable、乱码/真人/水印/复制风险及 metadata/panel null-safe。
- [x] 6.4 cloud/console typecheck 与目标测试通过；`openspec validate image-postcheck-vision-model --strict` 通过。
- [x] 6.5 提交、推送、落默认分支并部署 dev；只开启反推影子并完成一组真实 UI/文档样本反推与缓存复用验证，绑定/源风格/审计保持关闭。
- [ ] 6.6 按 `docs/real-machine-acceptance-backlog.md` 簇 83 完成同素材生成 A/B、逐槽绑定、源风格与产后审计真图验收，再逐阶段开 dev 旗标。

## 7. Change record

- [x] 7.1 回写 commits、validation、deploy 和未完成真实样本验收项。
- [ ] 7.2 6.6 全部满足后 archive。

### 7.1 Record (2026-07-15)

- cloud `023b5da`、console `8c27fc2` 已 fast-forward 到各自 `origin/master`。
- cloud acceptance + 全量 `2061/2061`、typecheck、build 通过；console 全量 `123/123`（另 1 skipped）、typecheck、build 通过；OpenSpec strict validate 通过。
- dev 备份：`/opt/aidcp/cloud.bak.20260715-110212.visual-reference.tar.gz` 与同时间戳 `.env` 备份；cloud/console checksum 复核无漂移。
- dev 健康：`aidcp-cloud.service=active`、`NRestarts=0`、8787 返回预期 426、8090/8088 health 均 `{"ok":true}`、console 新资产 HTTP 200、飞书 `WSClient onReady`。
- DB：`curated_content.visual_analysis` 已以幂等启动 DDL 建为 `jsonb`。真实影子样本 row 342（2 图）由 `dashscope/qwen3.7-plus` 得到 `analyzed`，两帧均为 `ui_document` + `ui_document` 专用字段；未混入摄影参数。首次整组+专用两次调用分别 7712/6967 tokens，第二次复跑缓存命中且零模型调用。
- dev 当前仅 `AIDCP_REFERENCE_VISUAL_ANALYSIS=true`；`AIDCP_REFERENCE_VISUAL_BINDING=false`、`AIDCP_REFERENCE_SOURCE_STYLE=false`、`AIDCP_VISUAL_FIDELITY_AUDIT=false`。未触发真实洗稿、未生成草稿、未做真人/摄影/文字卡/图表同素材 A/B；这些边界登记在簇 83。
