## Why

已 pending（申请已发出、等审核）的 Facebook 群，其按钮文案是「取消请求」。真机取证（2026-07-11，pending 群 `groups/311384382278852`）坐实：边缘 pending 词表 `PENDING_CTA_LABELS`（`join-executor.ts:197-201`）与云端判官两处 pending 短语表（`facebook-group-join-judge.ts:168` pre-click、`:197` post-click）**都只有 pending 状态词**（「待批准」「待审批」「已申请」/`pending`/`approval`）**而无中文「取消请求」按钮形态**——英/越/西/印尼/法的 cancel-request 形态齐全（`cancel request`/`hủy yêu cầu`/`cancelar solicitud`/`batalkan permintaan`/`annuler la demande`），恰好漏了简体中文这个。后果：中文界面账号在已 pending 群，观测腿 `ctaKind('取消请求')` 判不出 pending → `pendingRequest=false` → 观测腿误报「未申请」，云端 pre-click 确定性闸也漏认 → 误判可加入。

这是**状态上报**的 correctness 缺口，语言特定。安全侧由 sibling change `facebook-join-candidate-scope-guard`（A）兜底——作用域内目标控件是「取消请求」非 join，A 的 fail-closed 让点击腿诚实不点，即使本词表仍漏。本 change 独立修正状态识别的准确性：让 pending 被如实认出、不做无谓点击尝试、状态如实上报。

## What Changes

- **边缘 pending 词表补中文 cancel-request 形态**：`PENDING_CTA_LABELS` 加「取消请求」「取消加入请求」「取消申请」「已发送请求」等**具体短语**（守 `join-executor.ts:185-186` 裸词红线——只加明确短语，绝不加裸「取消」以免误命中页面 chrome 的「取消」按钮）。
- **云端判官两处 pending 短语表同步补齐**：`facebook-group-join-judge.ts` pre-click（:168）与 post-click（:197）的 `hasAny` 表加同族中文 cancel-request 短语，与边缘一致。
- **状态词审计（轻，非扩 N 语）**：对照真机 dump + 已覆盖语种，核 pending/member 按钮形态在**已覆盖语种**内是否有类似「状态词有、动作钮形态缺」的不对称缺口；补明确缺口即可，**不**把词表扩到未覆盖语种（守方案核心纠偏①「别把词表扩到 N 语当解法」）。
- **不做（YAGNI）**：不建 N 语字典；不改作用域/点击选取逻辑（那是 A）；不触协议、不改 join/member 分类顺序。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `facebook-group-join-observe-i18n`: pending 识别补齐中文 cancel-request 按钮形态（「取消请求」族）于边缘 `PENDING_CTA_LABELS` 与云端判官 pre/post-click 短语表，使已 pending 群被如实识别为 pending、`pendingRequest` 正确置真、状态如实上报；限已覆盖语种内补明确缺口，不扩 N 语字典。

## Impact

- 代码（**edge + cloud 判官，小改，无协议**）：
  - edge `src/facebook/join-executor.ts`：`PENDING_CTA_LABELS` 加中文 cancel-request 具体短语（守裸词红线）。
  - cloud `src/agents/facebook-group-join-judge.ts`：pre-click（:168）+ post-click（:197）`hasAny` pending 短语表同步补齐。
  - 测试：edge 单测——「取消请求」→ `ctaKind`='pending'、`pendingRequest=true`；cloud 单测——观测文本含「取消请求」→ pre-click `gated_skip` / post-click `pending_gated`。
- 部署：edge master land + cloud dev（安全序列；改判官后先 `test:acceptance` 再全量 `test` 再 `typecheck`）。
- 真机验收（落 backlog）：中文界面已 pending 群 → 观测腿正确报 pending、云端 pre-click 正确 gated_skip，不做无谓点击。归 FB 加群真机簇。
- 依赖：无新增。与 A 互补独立（A 灭红线错群、B 修状态上报）。
