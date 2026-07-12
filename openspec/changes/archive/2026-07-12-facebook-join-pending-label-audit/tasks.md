> **P0 correctness**：中文界面已 pending 群被误报「未申请」（「取消请求」不在 pending 词表）。小改、edge + cloud 判官、无协议。与 A 互补独立——A 灭红线错群、B 修状态上报准确。

## 1. aidcp-edge — pending 词表补中文 cancel-request

- [x] 1.1 `PENDING_CTA_LABELS`（`join-executor.ts:197-201`）加「取消请求」「取消加入请求」「取消申请」「已发送请求」；守 `:185-186` 裸词红线——只加明确短语，**绝不**加裸「取消」。
  <!-- aidcp-edge c06fa2c: added explicit Chinese cancel-request pending labels only; no bare 取消. -->
- [x] 1.2 确认 `ctaKind`（观测腿 + 点击腿两处同源）对「取消请求」返回 `'pending'`（member/pending 先判、join 后判顺序不变）。
  <!-- aidcp-edge c06fa2c: classifyCtaLabel and jsdom observe/click shared tables now classify 取消请求 as pending. -->

## 2. aidcp-cloud — 判官两处 pending 短语表同步

- [x] 2.1 pre-click `hasAny`（`facebook-group-join-judge.ts:168`）加同族中文 cancel-request 短语。
  <!-- aidcp-cloud 19b83b4: pre-click deterministic gate recognizes 取消请求 / 取消加入请求 / 取消申请 / 已发送请求. -->
- [x] 2.2 post-click `hasAny`（`:197`）加同族中文 cancel-request 短语，与边缘 + pre-click 一致。
  <!-- aidcp-cloud 19b83b4: post-click pending_gated fallback uses the same Chinese phrase family. -->

## 3. 状态词审计（轻，一次性，禁扩 N 语）

- [x] 3.1 对照真机 dump 核已覆盖语种（en/zh/vi/es/id/fr/de/…）内是否还有「pending 状态词有、cancel-request 动作钮形态缺」的类似不对称；发现明确缺口补具体短语，**不**扩到未覆盖语种（守核心纠偏①）。无明确证据不臆测补词。
  <!-- audit: existing covered-language tables already had en/vi/es/id/fr cancel-request forms plus status words; only proven zh gap was changed. German/Thai/Korean status forms were not expanded without true button evidence. -->

## 4. 测试

- [x] 4.1 edge：`ctaKind('取消请求')`==='pending'；观测腿含「取消请求」→ `pendingRequest=true`。
  <!-- aidcp-edge c06fa2c: test/facebook/join-executor.test.ts covers classifyCtaLabel and jsdom pendingRequest=true. -->
- [x] 4.2 cloud：观测文本含「取消请求」（`pendingRequest` 兜底路径）→ pre-click `gated_skip`、post-click `pending_gated`。
  <!-- aidcp-cloud 19b83b4: test/agents/facebook-group-join-judge.test.ts covers pendingRequest=false text fallback in both phases. -->
- [x] 4.3 反例：确认不加裸「取消」——含无关「取消」按钮的页面不误判 pending（若审计新增短语，各自锚定不误命中）。
  <!-- edge/cloud tests cover bare 取消 as non-pending; no bare cancel phrase added. -->

## 5. 集成与部署（安全序列）

- [x] 5.1 edge：`typecheck` + `test:acceptance` + `test` 绿；cloud：改判官后先 `test:acceptance` 再全量 `test` 再 `typecheck`。
  <!-- validation: edge typecheck + acceptance 16 + full test 1077 passed; cloud acceptance 47 + full test 1880 + typecheck passed. -->
- [x] 5.2 edge master land + cloud dev 部署（安全序列）。
  <!-- land/deploy: edge master c06fa2c pushed; cloud master 19b83b4 pushed and deployed to dev, backup cloud.bak.20260712-152112.tar.gz + .env.bak.20260712-152112, healthcheck active/8787/8090/PG/Feishu onReady. -->
- [x] 5.3 真机验收登记 backlog：中文界面已 pending 群 → 观测正确报 pending、云端 pre-click 正确 gated_skip。归 FB 加群真机簇。
  <!-- docs/real-machine-acceptance-backlog.md cluster 32 updated with facebook-join-pending-label-audit live acceptance item. -->

## 6. 收尾

- [x] 6.1 `openspec validate facebook-join-pending-label-audit --strict` 通过。
  <!-- control 2026-07-12: openspec validate facebook-join-pending-label-audit --strict passed. -->
- [x] 6.2 tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注；archive。
  <!-- control 2026-07-12: tasks fully checked with edge/cloud sha and dev deployment notes; archive performed after final validation. -->
