## MODIFIED Requirements

### Requirement: Like verification is bound to the acted-upon card

The edge MUST perform like location, click, and post-verification against the same article: it MUST tag the resolved article with a transient operation marker, and post-verification MUST read only the node carrying that same marker and re-derive its canonical post id to equal the command's. Native Feed initial actuation MUST freshly resolve the target and invoke the unique structural post-level reaction control with its in-page DOM `click()`; it MUST NOT convert this primary control into a generic coordinate click. A reaction-count control (for example `赞：N位用户`) MUST never be treated as a like toggle, and post-level versus comment-level reaction disambiguation MUST be structural: the react control belongs directly to the target card, shares an action bar with one post-level comment control, and is not inside a nested `[role="article"]` or reaction-summary toolbar.

If the tagged node is gone or its identity changes after dispatch, the edge MUST return `verify_indeterminate` and MUST NOT retry the click. If the same tagged card remains but its unique reaction control does not expose a positive reacted state within the bound, the edge MUST return `state_unchanged`; absence of a positive state MUST NOT be promoted to success. The marker MUST be cleared best-effort at terminal completion.

#### Scenario: Disappearing target is not reported as a successful like

- **WHEN** the tagged target article is removed from the DOM between click and verification
- **THEN** the edge returns `verify_indeterminate`
- **AND** it does not report the like as reacted and does not click again

#### Scenario: Recycled target identity is not accepted

- **WHEN** the tagged article remains in the DOM but its canonical post identity changes after dispatch
- **THEN** the edge returns `verify_indeterminate`
- **AND** it does not rebind verification to a replacement card carrying the original identity

#### Scenario: Reaction summary does not capture the primary commit

- **WHEN** the exact card contains a reaction-count control plus one post-level reaction control sharing the action bar with its comment control
- **THEN** Native Feed like invokes only the post-level control through its DOM click handler
- **AND** no primary CDP coordinate click is dispatched

#### Scenario: Same card never exposes a positive reaction

- **WHEN** the DOM click was dispatched and the tagged card keeps the commanded identity but its unique post-level control remains neutral through the bounded verification
- **THEN** the edge returns `state_unchanged`
- **AND** it does not report success or repeat the primary DOM click

### Requirement: Target is scrolled into view before acting

Before locating the reaction control, the edge MUST bring the target's unique post-level reaction control into view with a bounded, humanized scroll: read the exact target and control position, step incrementally with human-like wheel deltas, re-resolve and re-scan each step, and stop within bounded rounds/time. Merely bringing the article top into view is insufficient because a long card's action bar and its reaction picker can remain below the viewport. The edge MUST NOT use unconditional instant centering. If the target or structural control disappears, changes identity, remains ambiguous, or cannot be brought into view within the bound, the edge MUST return a truthful not-started reason and MUST NOT act on whatever is currently centered.

#### Scenario: Off-screen target control is reached without teleporting

- **WHEN** the exact target article is in the DOM but its post-level reaction control is below the viewport
- **THEN** the edge uses bounded humanized steps and fresh exact-card reads until the control is in the eligible viewport band before committing
- **AND** it does not instant-center the article or act on another visible card

#### Scenario: Target control cannot be brought into view

- **WHEN** bounded scrolling ends without one visible structural reaction control on the exact card
- **THEN** the edge returns a not-started visibility or target failure
- **AND** it dispatches neither the primary DOM click nor a picker coordinate click

### Requirement: Feed 两步点赞的反应浮层提交是 scoped 的、走真指针事件、且目标须在视口内

当 feed 态单击帖级中性反应控件（如「留下心情」）只弹出反应选择器浮层、按钮不翻转时，边缘 SHALL 补第二步在浮层里点「赞」项提交。该第二步 MUST 同时满足以下四条不变量，否则会点错帖、或点了不生效、或点在屏外空处：

1. **绑定同一个仍有效的 Feed like operation**：浮层探针 MUST 要求对应 operation marker 仍绑定在命令目标卡上且身份未变化；缺少、错误或过期 operation id 时 MUST 返回不可提交，MUST NOT 使用页面上恰好可见的无关 reaction dialog。

2. **作用域限定在打开的反应浮层内（scoped，绝不全文档搜索）**：定位「赞」反应项 MUST 只在**一个可见的反应选择器浮层容器**（`[role="dialog"]` 等、且其内含 ≥2 个反应项）内部进行，MUST NOT 在整个 document 里搜第一个 `aria-label` 为「赞」的按钮。理由：feed 里**每张卡的中性 Like 按钮 aria-label 也恰是「赞」**（反应计数汇总按钮亦然），而浮层是 portal、document 序排在**所有 feed 卡之后**——全文档搜第一个「赞」在目标**非首卡**时会命中**上方另一张卡**的 Like 按钮，既点错了别的帖（违反 note-scoped「绝不点错卡」红线），目标帖的浮层又永不提交（verify 恒 `state_unchanged`）。含 ≥2 反应项这道闸 SHALL 排除「反应人数查看」toolbar（其项形如「赞：N位用户」，MUST NOT 被当成可点的「赞」反应项）。

3. **浮层反应项走 CDP 坐标点击、绝不 in-page `element.click()`**：提交 MUST 用 CDP 坐标点击（从已标记目标卡的帖级 react 控件出发，随后 `mousePressed`/`mouseReleased`），MUST NOT 用页面内 `element.click()`。为防指针路径中途离开浮层 hover 区致其收起，移动起点 SHALL 是同一 operation 下目标 react 控件的当前坐标，且 MUST NOT overshoot。

4. **坐标点击目标须在可视视口内**：由于坐标点击只对可视区内的元素有效，滚动定位 MUST 把**帖级 react 控件**（而非仅文章顶部）带进可视视口，使其上方渲染的浮层落在屏内。定位浮层「赞」项后，若其中心坐标越出视口，边缘 MUST NOT 派发屏外坐标点击，SHALL 诚实回 `state_unchanged`，MUST NOT 静默假成功。

两步 SHALL 只补一次（防对已提交的赞二次点成撤销）。detail 态（单击即翻转、不弹浮层）MUST NOT 触发第二步，逐位不变。

#### Scenario: 目标非首卡时反应浮层「赞」项只翻转目标卡、不点到别卡
- **WHEN** 一条 like 命令携带信息流中**非首位**卡的 canonical 帖身份，单击其中性控件后弹出反应浮层，而上方其它卡也各有 `aria-label` 为「赞」的 Like 按钮
- **THEN** 边缘只在绑定该 operation 的目标卡仍有效时，在唯一浮层容器内定位并点击「赞」反应项，仅目标卡翻转为已赞态，MUST NOT 点到上方任何别的卡的 Like 按钮

#### Scenario: 错误或缺失 operation 不接管无关浮层
- **WHEN** 页面存在一个可见 reaction dialog，但请求的 Feed like operation marker 缺失、已过期或属于另一张卡
- **THEN** 浮层探针返回不可提交
- **AND** 边缘不派发任何 picker 坐标点击

#### Scenario: 浮层反应项用坐标点击提交、in-page click 视为未提交
- **WHEN** 需在反应浮层里点「赞」项提交
- **THEN** 边缘从同 operation 的目标 react 控件坐标出发，对浮层项中心派发 CDP `mousePressed`/`mouseReleased`，MUST NOT 依赖页面内 `element.click()`；提交后 verify 读到目标卡翻转（`isReactedState` 命中「移除赞」等串）才回 ok

#### Scenario: 浮层落在折叠线以下时先把 react 控件滚进视口
- **WHEN** 目标是长帖、其 Like 按钮或浮层落在可视视口以下
- **THEN** 边缘先把帖级 react 控件滚进视口再开浮层点击；若浮层「赞」项坐标仍越出视口，MUST 回 `state_unchanged`，MUST NOT 对屏外坐标空点、MUST NOT 假成功
