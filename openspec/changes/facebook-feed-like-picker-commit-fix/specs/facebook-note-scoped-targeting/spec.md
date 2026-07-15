## ADDED Requirements

### Requirement: Feed 两步点赞的反应浮层提交是 scoped 的、走真指针事件、且目标须在视口内

当 feed 态单击帖级中性反应控件（如「留下心情」）只弹出反应选择器浮层、按钮不翻转时，边缘 SHALL 补第二步在浮层里点「赞」项提交。该第二步 MUST 同时满足以下三条不变量，否则会点错帖、或点了不生效、或点在屏外空处：

1. **作用域限定在打开的反应浮层内（scoped，绝不全文档搜索）**：定位「赞」反应项 MUST 只在**可见的反应选择器浮层容器**（`[role="dialog"]` 等、且其内含 ≥2 个反应项）内部进行，MUST NOT 在整个 document 里搜第一个 `aria-label` 为「赞」的按钮。理由：feed 里**每张卡的中性 Like 按钮 aria-label 也恰是「赞」**（反应计数汇总按钮亦然），而浮层是 portal、document 序排在**所有 feed 卡之后**——全文档搜第一个「赞」在目标**非首卡**时会命中**上方另一张卡**的 Like 按钮，既点错了别的帖（违反 note-scoped「绝不点错卡」红线），目标帖的浮层又永不提交（verify 恒 `state_unchanged`）。含 ≥2 反应项这道闸 SHALL 排除「反应人数查看」toolbar（其项形如「赞：N位用户」，MUST NOT 被当成可点的「赞」反应项）。

2. **浮层反应项走 CDP 坐标点击、绝不 in-page `element.click()`**：提交 MUST 用 CDP 坐标点击（拟人化贝塞尔移动 + `mousePressed`/`mouseReleased`），MUST NOT 用页面内 `element.click()`。理由：浮层反应项监听真实指针事件（mousedown/mouseup），`element.click()` 只派发一个 `'click'` 事件、被 Facebook 当 hover 态忽略、不提交（返回 `clicked=true` 但反应不生效）。为防指针路径中途离开浮层 hover 区致其收起，移动起点 SHALL 设为目标卡的帖级 react 控件坐标（路径落在「控件→浮层」走廊）、且 MUST NOT overshoot。

3. **坐标点击目标须在可视视口内**：由于坐标点击只对可视区内的元素有效，滚动定位 MUST 把**帖级 react 控件**（而非仅文章顶部）带进可视视口，使其上方渲染的浮层落在屏内。定位浮层「赞」项后，若其中心坐标越出视口，边缘 MUST NOT 派发屏外坐标点击，SHALL 诚实回 `state_unchanged`，MUST NOT 静默假成功。

两步 SHALL 只补一次（防对已提交的赞二次点成撤销）。detail 态（单击即翻转、不弹浮层）MUST NOT 触发第二步，逐位不变。

#### Scenario: 目标非首卡时反应浮层「赞」项只翻转目标卡、不点到别卡
- **WHEN** 一条 like 命令携带信息流中**非首位**卡的 canonical 帖身份，单击其中性控件后弹出反应浮层，而上方其它卡也各有 `aria-label` 为「赞」的 Like 按钮
- **THEN** 边缘只在该浮层容器内定位并点击「赞」反应项，仅目标卡翻转为已赞态，MUST NOT 点到上方任何别的卡的 Like 按钮

#### Scenario: 浮层反应项用坐标点击提交、in-page click 视为未提交
- **WHEN** 需在反应浮层里点「赞」项提交
- **THEN** 边缘对该项中心坐标派发 CDP `mousePressed`/`mouseReleased`（拟人移动，起点为目标 react 控件），MUST NOT 依赖页面内 `element.click()`；提交后 verify 读到目标卡翻转（`isReactedState` 命中「移除赞」等串）才回 ok

#### Scenario: 浮层落在折叠线以下时先把 react 控件滚进视口
- **WHEN** 目标是长帖、其 Like 按钮/浮层落在可视视口以下
- **THEN** 边缘先把帖级 react 控件滚进视口再开浮层点击；若浮层「赞」项坐标仍越出视口，MUST 回 `state_unchanged`，MUST NOT 对屏外坐标空点、MUST NOT 假成功
