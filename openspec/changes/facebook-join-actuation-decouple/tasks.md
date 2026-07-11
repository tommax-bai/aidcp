> **实装排序**：本 change 触协议热点、收益思辨性。**先落 [[facebook-join-structural-verify]]（L3）+ 前置 [[facebook-join-candidate-scope-guard]]（作用域）+ [[facebook-join-pending-label-audit]]（状态词），并真机坐实「新页重定位保真度」失败模式**，再启动本 change 实装。以下任务为设计已定、待触发。**实装前以 proposal「2026-07-12 修订」块为准**（作用域承重、L4 随本 change 落地、管道走 edge-steps 非 command-bridge、schema 分 text/aria、触发门重述）。

## 0. 2026-07-12 修订前置（实装前必做，覆盖下方旧任务对应点）

- [ ] 0.1 依赖前置 change [[facebook-join-candidate-scope-guard]] 已 land：`clickTarget` 字面相等匹配**只在 `inTargetScope` 候选内**进行；作用域外字面相等一律 `stale_target`。序号降级为诊断字段、绝不作选取依据（推荐栏动态重排 + 去重后多字面相等候选不同时上报）。
- [ ] 0.2 云端**判官候选裁定模式**（L4=本 change 云端半）：`facebook-group-join-judge.ts` 加模式——全候选清单进 prompt、返回选中候选**字面串**（含匹配源字段 text/aria）或 fail-safe 弃权 -1、置信门控；产出即 `clickTarget`。缺此步本 change 在其立论场景不可实装。
- [ ] 0.3 管道订正：`clickTarget` 回传走**判官 → scheduler → `facebook-group-join-edge-steps.ts` 信封**（`group.join` 不走 command-bridge 动作映射，grep 零命中）；下方 4.1「command-bridge 映射」作废、以此为准。
- [ ] 0.4 候选 schema 分 `text`/`aria` 两字段（非合并 `text||aria`）；`clickTarget` 标明匹配源字段，两侧同源字段同 normalization。下方 2.2 的「`text||aria`」以此订正。

## 1. 协议同步（热点/串行 — 单写者，与其他动协议命令的 change 排序）

- [ ] 1.1 edge+cloud 两份 `src/comm/protocol.ts` 逐字一致：`GroupJoinPayload` 加可选 `clickTarget`（精确原文 + 序号）。
- [ ] 1.2 补 edge+cloud 两侧 `AC-PROTO` round-trip 断言 for `clickTarget`（镜像既有 `AC-PROTO-*`）——**因可选字段漂移 `Record<MessageType,true>` 穷举抓不到，round-trip 断言才是真闸**。
- [ ] 1.3 `npm run typecheck` + `npm run test:acceptance`（含新 `AC-PROTO` round-trip）绿；`docs/protocol.md` 涉计数/表则同步。

## 2. aidcp-edge — 候选无条件上报（两 pass 同法）

- [ ] 2.1 调用①（observe）观测：每个 Join/候选控件**原文标签无条件**写入观测（松类型通道），MUST NOT 因语种不在词表 `continue` 丢弃。调用②用**同样的无条件采集**重建候选列表。
- [ ] 2.2 定档 `clickTarget` normalization（trim/NFKC/去零宽等）**与来源字段（`text||aria`）**，两侧逐位对齐、偏保守、compare 侧不比 capture 侧更宽；令字面相等判定确定。
- [ ] 2.3 空字面 guard：normalize 后为空/纯空白的 `clickTarget` 当作缺省回落词表；绝不按字面相等匹配空文本控件（防 icon-only Leave 碰撞）。

## 3. aidcp-edge — 调用②按字面相等重定位（字面相等即反自残硬闸）

- [ ] 3.1 收到带 `clickTarget` 的 `click=true`：在新页候选里按**精确字面串相等**（同一 normalization）找回候选、点它。
- [ ] 3.2 **反自残硬闸 = 字面相等本身**：只点字面等于 `clickTarget` 的候选——Leave/取消字面串≠被批准 Join 字面串故永不解析、永不点。**删除**原「Join-kind 结构/标签复核」（对未知语种失效/自残）。
- [ ] 3.3 **序号只在多个字面相等候选间消歧、绝不位置兜底**；新页无字面相等候选 → 诚实 `stale_target` / `no_button`，绝不点 index N。
- [ ] 3.4 缺 `clickTarget` 回落既有词表定位、不回归；`edge-client.ts` 主动命令路由确认放行（若走独立下发）。

## 4. aidcp-cloud — 回传裁定候选

- [ ] 4.1 加群裁判把裁定为安全的候选的 `clickTarget`（精确原文 + 序号）随 `click=true` 命令回传（`command-bridge` 映射）。

## 5. 测试

- [ ] 5.1 edge：`clickTarget` 精确串新页重定位点击用例；候选无条件上报用例。
- [ ] 5.2 edge：反自残用例（同位置/结构现为 Leave、字面串≠被批准 Join → 无字面相等候选 → 不点、诚实 `stale_target`）；新页无字面相等候选 → 绝不点 index N 用例；多字面相等候选按序号消歧用例；**空字面 guard 用例（空/纯空白 clickTarget 或 icon-only 空文本控件 → 绝不字面匹配、回落词表）**；缺 token 回落用例。
- [ ] 5.3 cloud：回传 `clickTarget` 用例。
- [ ] 5.4 edge+cloud `AC-PROTO` round-trip for `clickTarget` 绿；两仓全量 `test` + `typecheck` 全绿。

## 6. 集成与部署（串行、安全序列）

- [ ] 6.1 与并发 sibling（动加群/协议命令的 change）排序；rebase 后 land。
- [ ] 6.2 edge master land + cloud dev 部署（安全序列）。
- [ ] 6.3 真机验收登记 backlog（`clickTarget` 重定位稳、反自残不误点、缺 token 回落不回归）。

## 7. 收尾

- [ ] 7.1 `openspec validate facebook-join-actuation-decouple --strict` 通过。
- [ ] 7.2 tasks.md 勾选 + `<!-- <repo> <sha> 备注 -->` 标注；archive。
