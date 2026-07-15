## Why

小红书搜索账号（尤其已灰度 AI 搜索、搜索框为 `textarea[name="aiSearchTextarea"]`、结果落 `/search_result_ai` 的账号，如 dev 的「工程师大白」）在自动化下**几乎每次排期评论都栽在搜索这一步**：2026-07-15 dev 日志显示该账号一天触发 14 次评论任务，仅 7 次走到选卡，约 30 次搜索以 `not_on_search_page`（未导航到结果页）或「搜索超时/无卡片」告终，账号几乎评不出。

真机逐项取证（CDP 复现边缘现有序列 + A/B）定位根因——**边缘提交搜索的两条路在 AI 搜索框上都不生效**：

1. 边缘用**程序化 `el.focus()`** 聚焦搜索框（`buildFocusClearJs`）。AI 搜索框的「回车导航」不认程序化聚焦，需要**真实用户手势**（真实指针点击）才会响应。
2. 边缘的**回车事件不带 `text` 字段**（`pressEnter`→`dispatchKey('Enter','Enter',13)`），只产生裸 `keydown`、不产生 `keypress`；配合程序化聚焦，回车在该框上是**空操作**（真机实测连试 5 次 0 跳转）。
3. 兜底的**提交按钮 `.bottom-box-right-submit-button` 在 AI 框上存在但不可见（0×0）**，取不到坐标、点不了，兜底形同虚设。

真机验证的可靠修法（含中英文关键词、连续命中，零 URL 跳转）：**真实点击聚焦 → 逐字输入 → 约 700ms 停顿 → 带 `text:'\r'` 的回车 → 未跳转即重试回车**。该组合在 dev「工程师大白」浏览器上对 6 个含空格中英文关键词 6/6 首次命中。

`/search_result` 与 `/search_result_ai` 两种结果页的 URL 判定、关键词双重编码归一、卡片提取**均已支持**（真机两页各抓到 30 张 `.note-item` 卡）——本 change 只补「可靠提交」这一环，两种页型随之打通。这是既有 `comment-search-command`「搜索采卡前须确认到达结果页 + 诚实回失败」诚实契约的**对称补全**：既有契约保证「到不了就不撒谎」，本 change 保证「用对手势真的到得了」。

## What Changes

- **`aidcp-edge` `cdp-util.ts`**：`pressEnter` 的回车事件补上 `text:'\r'`（`dispatchKey` 增加可选 text 参数），使合成回车具备真实 `keypress` 形态。
- **`aidcp-edge` `search-handler.ts` `executeSearch`**：聚焦搜索框改为**先派发一次真实指针点击**（取可见搜索框中心坐标，复用现有 `dispatchClick`）再清空/聚焦；并保证输入完成到回车之间有一个**停顿地板**（约 700ms），让 AI 搜索框内部状态就绪。
- **`aidcp-edge` `search-handler.ts` `executeSearch`**：**用「回车重试」取代坏掉的「点提交按钮」兜底**——回车后在有界窗口内未确认跳转即再次派发回车（有界次数，如 ≤3 次），全部失败才走既有诚实失败分支（`onSearch=false` → `not_on_search_page`，不采/报当前页）。保留提交按钮点击**仅作可见时的附加兜底**、不作为唯一路径。
- **`aidcp` OpenSpec**：`comment-search-command` 规格新增「搜索提交须用真实用户手势 + 未跳转须重试」要求，作为既有导航确认契约的补全。

## Impact

- `aidcp-edge`：`src/browse/search-handler.ts`（`executeSearch` 聚焦/停顿/重试）、`src/browse/cdp-util.ts`（`pressEnter`/`dispatchKey`）；相关单测。行为改动**只影响搜索提交这一步**，不动协议、云端调度、风控配额、发布链。
- `aidcp`：`comment-search-command` 规格新增一条要求（ADDED），既有导航确认/诚实归因要求不变。
- 真机验收 gated：需在 dev AI 搜索账号（工程师大白）上跑真实排期评论，确认搜索连续命中、评论能发出。桩测覆盖不到指纹浏览器上的真实手势与导航时序。
- 不涉及边云协议消息变更（无新增/删除 MessageType），不触碰协议四处同步与角色注册等热点。
