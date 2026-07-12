## Context

边缘 pending 识别两处同源：观测腿 `GROUP_JOIN_OBSERVE_JS` 与点击腿 `GROUP_JOIN_CLICK_JS` 都用 `ctaKind(label)`（`join-executor.ts:240-249` / `:395-402`），member/pending 先判、join 后判，词表 `PENDING_CTA_LABELS`（`:197-201`）。`pendingRequest` 由 pending 类候选或 modal 文本命中 `PENDING_KW` 置真（`:335-336`）。云端判官 `facebook-group-join-judge.ts` 另有两处独立短语表：pre-click（:168）判 `gated_skip`、post-click（:197）判 `pending_gated`；均 `obs.pendingRequest || hasAny(text, [...])`——边缘 boolean 为主、云端文本表为兜底。

真机（pending 群，本群按钮「取消请求」`div[role=button]`）：`PENDING_CTA_LABELS` 有 `cancel request`（英）、`hủy yêu cầu`（越）、`cancelar solicitud`（西）、`batalkan permintaan`（印尼）、`annuler la demande`（法），中文侧只有状态词「待批准」「已申请」「待审批」——**无「取消请求」按钮形态**。故 `ctaKind('取消请求')` 返 ''（既非 pending 也非 join）→ `pendingRequest` 不置真 → 观测腿误报未申请。

## Goals / Non-Goals

**Goals:**
- 中文界面已 pending 群被如实识别为 pending，`pendingRequest` 正确置真。
- 边缘词表与云端判官两处短语表一致。
- 守裸词红线：只加明确短语，绝不加会误命中 chrome 的裸词。

**Non-Goals:**
- 不扩 N 语字典（守核心纠偏①）——只补已覆盖语种内的明确缺口。
- 不改 join/member/pending 分类顺序、不改 `structuralJoinConfirmed` 语义。
- 不动作用域/点击选取（那是 A）。

## Decisions

**D1：只加具体短语，守裸词红线。** 加「取消请求」「取消加入请求」「取消申请」「已发送请求」（后者对称英文 `request sent`）。**绝不**加裸「取消」——`join-executor.ts:185-186` 已记裸词事故（裸「退出」命中输入法「退出联想输入」），裸「取消」会命中页面各处「取消」按钮。四字短语「取消请求」足够具体、不误命中。

**D2：边缘 + 云端两处同步。** 边缘 `PENDING_CTA_LABELS` 是主判据（驱动 `pendingRequest`）；云端 pre/post-click 短语表是兜底（边缘 boolean 漏时按原始文本再兜）。两侧都补同族短语，保持一致——虽非协议 parity 类型热点，但语义须对齐防判定漂移。

**D3：审计限已覆盖语种、补明确缺口即止。** 对照真机 dump，核已覆盖语种（en/zh/vi/es/id/fr/de/…）里是否还有「状态词有、cancel-request 动作钮形态缺」的类似不对称。发现明确缺口就补具体短语；**不**借此把词表扩到未覆盖语种（那是方案明令禁止的 fail 模式）。本 change 只坐实并修中文这一处，审计作为一次性核查任务、发现即补、无则记录。

## Risks / Trade-offs

- [「取消请求」误命中无关 chrome] → 四字具体短语，实测无碰撞；不加裸词。
- [边缘/云端两处漂移] → D2 同步补齐 + 各自单测锚定。
- [审计诱发词表膨胀] → D3 硬约束：只补已覆盖语种明确缺口，禁扩 N 语；YAGNI。
- [pending 误判为可加入的残余] → 即便本词表仍有未知缺口，sibling A 的作用域 fail-closed 兜底（目标控件非 join → 诚实不点），不会因 pending 漏认而误点异群。

## Migration Plan

- edge 改 `PENDING_CTA_LABELS` + 单测；cloud 改判官两处短语表 + 单测。
- 部署：edge master land + cloud dev（安全序列，改判官先 `test:acceptance` 再 `test` 再 `typecheck`）。
- 回滚：纯词表增补，回退即删增补短语，秒级。

## Open Questions

- 已覆盖语种内是否还有其他 cancel-request / pending 按钮形态缺口——D3 审计一次性核查，真机 dump 为据；无明确证据不臆测补词。
