> **P0 correctness**：中文界面已 pending 群被误报「未申请」（「取消请求」不在 pending 词表）。小改、edge + cloud 判官、无协议。与 A 互补独立——A 灭红线错群、B 修状态上报准确。

## 1. aidcp-edge — pending 词表补中文 cancel-request

- [ ] 1.1 `PENDING_CTA_LABELS`（`join-executor.ts:197-201`）加「取消请求」「取消加入请求」「取消申请」「已发送请求」；守 `:185-186` 裸词红线——只加明确短语，**绝不**加裸「取消」。
- [ ] 1.2 确认 `ctaKind`（观测腿 + 点击腿两处同源）对「取消请求」返回 `'pending'`（member/pending 先判、join 后判顺序不变）。

## 2. aidcp-cloud — 判官两处 pending 短语表同步

- [ ] 2.1 pre-click `hasAny`（`facebook-group-join-judge.ts:168`）加同族中文 cancel-request 短语。
- [ ] 2.2 post-click `hasAny`（`:197`）加同族中文 cancel-request 短语，与边缘 + pre-click 一致。

## 3. 状态词审计（轻，一次性，禁扩 N 语）

- [ ] 3.1 对照真机 dump 核已覆盖语种（en/zh/vi/es/id/fr/de/…）内是否还有「pending 状态词有、cancel-request 动作钮形态缺」的类似不对称；发现明确缺口补具体短语，**不**扩到未覆盖语种（守核心纠偏①）。无明确证据不臆测补词。

## 4. 测试

- [ ] 4.1 edge：`ctaKind('取消请求')`==='pending'；观测腿含「取消请求」→ `pendingRequest=true`。
- [ ] 4.2 cloud：观测文本含「取消请求」（`pendingRequest` 兜底路径）→ pre-click `gated_skip`、post-click `pending_gated`。
- [ ] 4.3 反例：确认不加裸「取消」——含无关「取消」按钮的页面不误判 pending（若审计新增短语，各自锚定不误命中）。

## 5. 集成与部署（安全序列）

- [ ] 5.1 edge：`typecheck` + `test:acceptance` + `test` 绿；cloud：改判官后先 `test:acceptance` 再全量 `test` 再 `typecheck`。
- [ ] 5.2 edge master land + cloud dev 部署（安全序列）。
- [ ] 5.3 真机验收登记 backlog：中文界面已 pending 群 → 观测正确报 pending、云端 pre-click 正确 gated_skip。归 FB 加群真机簇。

## 6. 收尾

- [ ] 6.1 `openspec validate facebook-join-pending-label-audit --strict` 通过。
- [ ] 6.2 tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注；archive。
