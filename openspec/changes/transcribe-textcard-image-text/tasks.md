# Tasks

> 本 change **仅动 aidcp-cloud**：不改协议、不改边缘、不新增凭据面。转写复用 `src/llm/vision.ts` 视觉出口与 `cover-form-sensor` 形态判定。默认旗标 off + 影子先行。

## 1. aidcp-cloud — 数据模型

- [ ] 1.1 `curated_content` 新增列：`image_text`（转写文字）+ 转写元数据（`transcribed_for` 抓取锚、`transcribe_model`/`transcribe_provider`、转写时刻、来源标记）；schema 启动自建（无迁移器），旧行 NULL 向后兼容
- [ ] 1.2 `CuratedContentStore` 读写新列：落库/读出 `image_text` 与元数据；`upsertObservation` 既有行为不变、新列可选写入

## 2. aidcp-cloud — 转写服务（复用视觉出口 + 形态门控）

- [ ] 2.1 新增文字卡图内文字转写服务：复用 `OpenAiCompatVisionClient`（`vision.ts`）；一条笔记的全部文字卡图**合并为一次**多模态调用；输出上限提到 8192（env 可调）防密卡截断；`temperature` 0
- [ ] 2.2 门控：复用 `cover-form-sensor` 形态判定，仅 `form === 'text_card'` 才转写；`photo`/`illustration`/`other` 跳过；转写与形态判定为**两次独立调用**（保结构隔离）
- [ ] 2.3 按抓取锚缓存（`transcribed_for === capturedAt`、零 TTL）：命中零调用；重抓（锚变）失效重转
- [ ] 2.4 诚实降级：失败/超时/解析失败 → 跳过 + 标记，绝不编造、不阻断准入/发布；缺密钥沿 `vision.ts` 诚实抛错、绝不跨厂商兜底；失败保持既有内容不变（不污染/不清空）
- [ ] 2.5 转写 prompt（中文）：只转写图内文字、按阅读顺序忠实抄录、不补不改不评价；严格 JSON/文本解析，脏输出按失败处理
- [ ] 2.6 时限：单次调用内层超时闸 + 遵守 180s 上限与发布看门狗；合并单次调用避免串多次

## 3. aidcp-cloud — 模型解析 + 旗标 + 记账

- [ ] 3.1 转写模型解析：`AIDCP_TEXTCARD_OCR_MODEL` → 默认 `qwen-vl-ocr`；provider 同 cover-form 路径（env → 代码默认，装配处注入 `getModel`/`getProvider`，客户端不回落文本层）
- [ ] 3.2 特性旗标 `AIDCP_TEXTCARD_OCR`（缺省 off）+ 影子态开关；off 时零转写调用、零写入
- [ ] 3.3 token 记账：注册转写角色供 `onCall` 记账入 `llm_token_usage`；**仅记账、不进 role-catalog 可配置**（模型走 env，避免 console enum drift 白屏）

## 4. aidcp-cloud — 接入准入链 + 并入内容正文

- [ ] 4.1 在观测落库准入链接入转写：详情到达 → 形态门控 →（text_card）批量转写 → 落 `image_text` 列
- [ ] 4.2 启用态把转写文字并入内容正文（DOM 正文在前、转写文字在后）；影子态只写 `image_text` 列、**不**并入正文
- [ ] 4.3 内容全在图里（空 DOM 正文）但有转写的文字卡：转写后按内容参与准入，**不改**下游空正文闸/壳行清理判定——靠内容正文并入后非空使其自动正确

## 5. aidcp-cloud — 消费验证（评估/改写读到增补内容）

- [ ] 5.1 验证准入丰富度评估读增补后的全文（含转写文字），空 DOM 文字卡不再被误判单薄
- [ ] 5.2 验证参照改写源料（`referenceNote.body` → `referenceNoteBlock`）含转写文字，经保真链（分析→规划→改写→忠实审核）改写去重
- [ ] 5.3 验证防搬运：转写文字 MUST NOT 逐字进生成卡；忠实审核照常拦截未获原稿支持的新增

## 6. aidcp-cloud — 测试

- [ ] 6.1 单测：门控（text_card 转 / 其他不转 / 旗标 off 零调用）、批量一次调用、缓存命中与重抓失效、诚实降级（失败不编造 / 缺密钥不兜底 / 解析失败不污染既有内容）、影子只存不并入、启用并入 body
- [ ] 6.2 acceptance：转写失败绝不编造/不阻断、缺密钥诚实抛、空 DOM 文字卡经转写纳入且可改写、防搬运不逐字直贴
- [ ] 6.3 `npm run typecheck` + `npm run test:acceptance` + `npm test` 全绿

## 7. 上线与灰度

- [ ] 7.1 上线前 A/B `qwen-vl-ocr` vs `qwen-vl-max`（20–30 张真卡）定默认；百炼控制台核实 `qwen-vl-ocr` 真价与 SKU
- [ ] 7.2 部署 dev（旗标 off）→ 开影子期核转写质量/成本/延迟 → 通过后切启用态并入 body
- [ ] 7.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：文字卡转写准确率、纳入率变化、改写丰富度、成本/延迟实测
- [ ] 7.4 tasks.md 回写 commit-sha + 部署标注；`openspec validate --strict`；完成后 archive
