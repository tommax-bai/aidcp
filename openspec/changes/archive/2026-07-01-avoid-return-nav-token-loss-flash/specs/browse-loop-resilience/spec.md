## ADDED Requirements

### Requirement: 无浮层的整页离页返回必须直连来源列表、不得回踩失效笔记详情

边缘返回列表页时 MUST 以「返回瞬间头上是否盖着笔记浮层」决定返回方式，而非以「当前 URL 是否为作者主页」这一狭窄判据：

- **已在目标列表**（feed 匹配 explore feed、search 匹配搜索结果）→ MUST NOT 触发浏览器后退或整页重载（关浮层后列表即露出、滚动位由 SPA 保住）。
- **不在列表且头上盖着笔记浮层** → MAY 用浏览器后退（`history.back()`）回到来源列表以保住滚动位（卡片真实点击开的浮层，其上一条历史即来源列表，后退安全）。
- **不在列表且无笔记浮层**（通知巡视 / 作者主页深读 / 任意整页离页动作返回）→ MUST 直接前向导航（`Page.navigate`）回**来源列表页**（feed 来源回 explore、search 来源回搜索结果），MUST NOT 经浏览器后退回踩到 `xsec_token` 已失效的旧笔记详情页而闪现 `error_code=300031「当前笔记暂时无法浏览」`。

本要求是**预防**（不落到坏页），与既有「返回后须对 404/坏页健壮、健康校验通过再上报」互补而非替代：既有要求作为**落地后的安全网**原样保留；本要求消除「无浮层整页返回」这条会渲染出坏页并被旁路监测误报的触发路径。返回完成的 `action.completed{action:'back', ok:true}` 回执契约不变。

#### Scenario: 看笔记→开通知→返回，直连 feed 不闪坏页

- **WHEN** 会话在 explore feed 打开笔记（真实点击、URL 带 `xsec_token`）后离页进入通知巡视，随后收到 `navigation.back{reason:'back_to_feed'}`，此时头上无笔记浮层、当前在 `/notification`
- **THEN** 边缘直接 `Page.navigate` 回 explore feed，MUST NOT `history.back()` 回踩那条 token 已失效的笔记详情；返回过程中 `error_code=300031` 坏页 MUST NOT 被经过 / 闪现，地址栏直接落在 explore feed

#### Scenario: 搜索来源的无浮层返回回到搜索结果

- **WHEN** 会话 `sourcePageType==='search'`、离页动作后返回、且头上无笔记浮层
- **THEN** 边缘前向导航回**搜索结果列表**（而非 explore feed），同样不经浏览器后退回踩失效详情

#### Scenario: 笔记浮层盖在列表上的普通返回仍用后退保滚动位

- **WHEN** 返回瞬间笔记浮层仍盖在来源列表之上（未发生整页离页）
- **THEN** 边缘可用 `history.back()` 关浮层回到来源列表并保住滚动位，行为与本 change 前一致

#### Scenario: 万一仍落坏页，既有兜底照旧生效

- **WHEN** 因边界情形（如嵌套历史栈残留）前向导航或后退后仍落在非健康列表页（坏页 / 0 卡）
- **THEN** 既有「落坏页→`Page.navigate` 良好列表 + 健康校验后再上报 `page.cards`」兜底照常触发，MUST NOT 静默不上报而陷入边-云互等
