## ADDED Requirements

### Requirement: 返回 feed 后不重复评估已看过的卡片

返回 feed（`back_to_feed`）后的续刷 SHALL 不对**已评估过**的可见卡片重复跑 LLM 内容评估。云端 SHALL 在会话内维护「已评估卡片集合」，对每张**被纳入一次内容评估**的卡片标记为已评估（跨轮保持）；内容评估的候选过滤 MUST 同时排除「已打开（visited）」与「已评估（evaluated）」的卡片。当返回后可见卡片均已评估过（候选为空）时，云端 MUST 立即产出 `content.no_valuable` 并据此滚动，MUST NOT 再发起一次 LLM 评估往返。滚动后**新出现**的卡片 SHALL 照常评估。

每张有 `noteId` 的卡片整个会话内 MUST 至多触发一次 LLM 内容评估；无 `noteId` 的卡片按现状处理（无法去重时仍可评估）。

#### Scenario: 返回到全已评估的 feed 立即滚动、零 LLM

- **WHEN** 返回 feed 后可见卡片均已在本会话被评估过（无新卡片）
- **THEN** 云端不调用 LLM，立即 `content.no_valuable` → 续刷滚动（消除返回后等待）

#### Scenario: 滚动后的新卡片仍照常评估

- **WHEN** 续刷滚动后出现本会话未评估过的新卡片
- **THEN** 云端对这些新卡片正常发起一次 LLM 内容评估

#### Scenario: 同一卡片至多评估一次

- **WHEN** 同一张有 `noteId` 的卡片在返回 / 重叠滚动中再次可见
- **THEN** 该卡片不再被重复纳入 LLM 评估（已评估集合命中即排除）
