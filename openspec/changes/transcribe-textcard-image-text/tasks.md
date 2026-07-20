# Tasks

## 1. 契约与数据模型

- [x] 1.1 明确有序逐卡记录、单 JSONB 事实源、正文增补与逐槽生成对应关系
- [x] 1.2 `curated_content` 新增可空 `text_card_transcription` JSONB；实现严格归一、读写与旧行兼容
- [x] 1.3 精选行、委派任务和 `ReferenceNote` 贯通有序转写，未授权的客户端列表不额外暴露原文

<!-- aidcp-cloud 9056a1603eb90ecd786f788b903a2e7d71a173f1: single JSONB source of truth, strict boundary normalization, panel/delegated/reference propagation; client list/detail remain allowlisted and do not expose per-card OCR. -->

## 2. 识别与转写服务

- [x] 2.1 复用封面形态识别，仅高置信 `text_card` 入选；形态结果按来源数组下标回填图片快照
- [x] 2.2 一条笔记的入选图片合并为一次视觉转写，严格解析逐卡 JSON，输出保序
- [x] 2.3 实现有序图片 SHA-256 锚、数据库缓存命中与进程内 single-flight
- [x] 2.4 旗标关闭零调用零写入；调用/超时/缺密钥/解析失败诚实记录且不阻断主路径
- [x] 2.5 视觉调用支持显式 `max_tokens=8192`，模型/厂商 env 覆盖并默认复用封面视觉配置，token 用量照常记账

<!-- aidcp-cloud 9056a1603eb90ecd786f788b903a2e7d71a173f1: text-card-transcriber + OpenAiCompatVisionClient maxTokens; role browse:text_card_transcriber is visible in the role catalog and usage ledger. -->

## 3. 精选准入与正文

- [x] 3.1 共鸣预筛后接入转写，空 DOM 文字卡先转写再参与丰富度评估
- [x] 3.2 成功卡片文字按参考图顺序增补正文；重复事件不重复追加，失败保持 DOM 正文
- [x] 3.3 落库同时保存带形态注解的图片与有序转写；重新观测时旧锚失效

## 4. 文字卡对应生成

- [x] 4.1 `CoverCardWriter` 选取实际生成槽对应的有序转写；完整时使用 `ordered_transcription`，缺失时诚实 `body_fallback`
- [x] 4.2 `buildCardSetPrompt` 将每张来源卡文字按顺序交给卡片文案生成，要求第 i 张对应第 i 张且终稿事实优先
- [x] 4.3 保留现有防搬运、整套失败回落、确定性渲染和视觉参考边界

<!-- aidcp-cloud 9056a1603eb90ecd786f788b903a2e7d71a173f1: ordered slot mapping is stamped through ImagePlan/CoverFormAudit; missing slots fall back as a whole, and the overlap guard includes full per-card transcription. -->

## 5. 测试与验证

- [x] 5.1 单测：严格归一、判形门控、批量一次、顺序、缓存、single-flight、失败、旗标关闭、正文合并
- [x] 5.2 单测：有序逐槽 prompt/计划、缺卡回落、原文重叠闸
- [x] 5.3 focused tests、`npm run test:acceptance`、`npm test`、`npm run typecheck`
- [x] 5.4 `openspec validate transcribe-textcard-image-text --strict`

<!-- Validation after rebase onto origin/master: acceptance 62/62; full suite 2706 total, 2698 passed, 8 gated skips, 0 failed; typecheck passed. OpenSpec strict validation passed in the control worktree. -->

## 6. 集成与 dev

- [x] 6.1 回写 cloud/control commit SHA 与验证证据，rebase 后 fast-forward 合入并 push 默认分支
- [x] 6.2 按部署规范从 clean cloud master 部署 dev，备份、重启、service/listener/health/Feishu/PostgreSQL 检查
- [x] 6.3 dev 真实文字卡验收：记录顺序、识别文字、缓存命中、逐槽生成对应；未实测项诚实登记 backlog

<!-- Integrated and pushed: aidcp-cloud master 9056a1603eb90ecd786f788b903a2e7d71a173f1; aidcp main 512de6946fcab73684259e4e142043ac9c3b1bd7. Deployed clean cloud master to dev 121.89.85.150 after backup /opt/aidcp/backups/cloud-20260720-182152.tar.gz and .env backups; only aidcp-cloud.service restarted. Service active, 8787/8090 listeners, panel API v6, Feishu WS ready, Edge sessions reconnected, and curated_content.text_card_transcription is jsonb. AIDCP_TEXTCARD_OCR=true enabled on dev. Real acceptance used curated row 459: 9/9 cards transcribed in sourceArrayIndex order 0..8, persisted through CuratedContentStore, DB read-through cache hit with zero repeat vision call, and all nine ordered texts appeared monotonically in buildCardSetPrompt with ordered_transcription mapping. One transient failed OCR result was honestly discarded and one bounded diagnostic retry succeeded. No image rendering, approval, or platform publish was performed; that destructive/end-to-end check remains in docs/real-machine-acceptance-backlog.md. -->
