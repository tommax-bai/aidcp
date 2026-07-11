## Context

加群两次边缘调用（`src/facebook/join-executor.ts`）：
- 调用①（observe-only，`GroupJoinPayload.click` 缺省）：`Page.navigate` 到群页 → `observeUntilReady` → 回传观测 → 不点。
- 云端裁判观测。
- 调用②（`click=true`）：**再次 `Page.navigate`（join-executor.ts:397）到新页** → `observeUntilReady`（402）→ `relocateAndClickJoin`（325：页面内按词表重新定位加入按钮、`element.click()`）→ `observePostClickUntilSettled`（449）。

关键事实（评审坐实）：调用②在**新页**重新定位，调用①观测里的任何页内 DOM 句柄**必然失效**。故「点云端裁定的那个候选」不能靠页内句柄，只能靠**跨导航稳定的键**。当前调用②靠自己的词表（`classifyCtaLabel` / Join 关键词）重定位——某语种 Join 文案不在词表即定位失败、加群失败。这是本 change（L2）要治的点击动作定位语言相关缝。

分层定位：C1（[[facebook-locale-pin-en-us]]）治新号界面语言；L3（[[facebook-join-structural-verify]]）治成败校验、零协议、先上消灭重复加群；本 change（L2）治**点击定位**、触协议热点、思辨性收益（待真机坐实词表定位失败再实装）。

## Goals / Non-Goals

**Goals:**
- 调用②点**云端裁定的那个候选**、语言无关，不靠边缘词表二次分类。
- 跨调用①→②的 re-navigate 稳定：用精确原文 + 序号，非页内 DOM 句柄。
- 守反自残红线：绝不点一个复核不通过（非 Join-kind）的控件。
- 协议 additive、向后兼容、parity 靠 round-trip 断言把关。

**Non-Goals:**
- 不用页内 DOM 句柄当 token（评审证必失效）。
- 不做跨导航 token 持久化 / 不给按钮上视觉 / 不删词表（回落用）。
- 不改成败校验（那是 L3）。

## Decisions

**D1：`clickTarget` = 精确原文；反自残靠字面串相等，非 DOM 句柄、非序号位置（两轮评审坐实）。** 云端把裁定候选的**逐字原文**随 `click=true` 回传；调用②在新页重新观测的候选里按**精确字面串相等**（两侧同一 normalization）找回该候选、点它。逐字相等语言无关（不理解语义、只比字符串），比边缘词表分类稳。备选（页内 DOM 句柄）被否——调用② re-navigate 后必失效。备选（按钮坐标）被否——新页布局漂。

**D2：候选无条件全报，两 pass 同法重建。** 调用①观测把每个 Join/候选控件原文无条件写入观测（松类型通道），MUST NOT 因语种不在词表 `continue` 丢弃——否则云端拿不到候选、无从回传。调用②用**同样的无条件采集**重建候选列表再比字面串。

**D3：反自残硬闸 = 精确字面串相等（复验纠正）。** 第二轮复验证「点前 Join-kind 结构/标签复核」**做不到**——词表复核对未知语种 Join 返空（功能失效），结构复核分不出同结构的 Join/Leave（自残）；没有任何 label/structure 检查能既纳入未知 Join 又拒未知 Leave。**正解：精确字面串相等本身就是反自残硬闸**——Join 与 Leave/取消在任何语种都是不同字面串，Leave 永不等于被批准的 Join 字面串 → 永不解析 → 永不点。故：① 只点字面串等于 `clickTarget` 的候选；② **序号只在多个字面相等候选间消歧、绝不位置兜底**（新页无字面相等候选就 `stale_target`，绝不点 index N 处任意按钮）；③ 两侧 normalization **与来源字段**（`text||aria`）必须逐位对齐（下方 Open Question 收口为实装前定档），compare 侧绝不比 capture 侧更归一/更宽；④ **空字面 guard**：normalize 后为空/纯空白的 `clickTarget` 当作缺省（回落词表），绝不按字面相等匹配空文本控件——防 icon-only Leave（空 captured text）与空 key 碰撞。删掉原 D3 的「Join-kind 复核」——它要么失效要么自残。

**D4：缺 `clickTarget` 回落，向后兼容。** 旧云端不带 `clickTarget` → 调用②走既有词表定位，不回归。新页无字面相等候选 → 诚实 `stale_target` / `no_button`，绝不盲点位置猜测。

**D5：parity 靠 round-trip 断言，不靠 typecheck（评审揪出）。** `GroupJoinPayload` 加**可选**字段，两份 `protocol.ts` 的 `Record<MessageType,true>` 穷举**抓不到可选字段漂移**。故须补 edge+cloud 两侧 `AC-PROTO` round-trip 断言（镜像既有 `AC-PROTO-*`）专门护 `clickTarget` 编解码一致——这才是真闸。

## Risks / Trade-offs

- [误点 Leave/取消自残] → **D3 精确字面串相等硬闸**：Leave 字面串≠被批准 Join 字面串 → 永不解析 → 永不点。序号绝不位置兜底。
- [`clickTarget` 字面串在新页匹配不上（文案微变/多候选同文）] → 多字面相等候选用序号消歧；无字面相等候选诚实 `stale_target`，绝不盲点。文案微变致不等 = 安全侧退化（宁可 retry 不误点）。
- [normalization 两侧不一致致假不等/假相等] → D3-③ 两侧同一 normalization、实装前定档（非真机延后）。
- [协议可选字段漂移 typecheck 抓不到] → D5 round-trip 断言。
- [与并发 sibling（`facebook-scheduled-comment` 等动加群/协议命令）撞热点] → §7 单写者、串行、rebase 后 land。
- [收益思辨性、可能白做] → 故先上 L3、本 change 待真机坐实「词表定位失败」失败模式后再实装；proposal/design 先入库不浪费。

## Migration Plan

- **实装排序**：先落 L3（[[facebook-join-structural-verify]]）+ 真机坐实是否真有「某语种 Join 按钮词表定位失败」→ 有则实装本 change。
- 协议先行：两份 `protocol.ts` 同步加 `clickTarget` → `typecheck` → 补 `AC-PROTO` round-trip 断言 → `command-bridge` 回传 → edge 调用②重定位 + 反自残。
- 部署：edge dev land + cloud dev（安全序列，先 `test:acceptance` 含 `AC-PROTO-*` 再全量 `test` 再 `typecheck`）。
- 回滚：缺 `clickTarget` 即回落词表定位（天然回滚位）。

## Open Questions

- `clickTarget` normalization（原样 vs trim vs NFKC vs 去零宽/表情装饰）——**实装前定档**（非真机延后），两侧逐位对齐，令字面相等判定确定；宜偏保守（少归一 = 少假相等）。
- 多候选同字面文时序号消歧是否够，或需补一个语言无关结构判据做二次消歧——真机取证；先「字面相等 + 序号消歧」，无字面相等即 `stale_target`。
- 本 change 是否真需要——取决于真机是否复现「词表 Join 定位失败」；未复现则保持 proposed-not-implemented。
