# Keep the note detail page open through approval; stop re-searching per comment

## Why

按需评论（`/comment` 命令 + 自动排期评论，两者走同一 `runTask`）当前对**同一篇笔记、同一个搜索词做三次独立的全量搜索**：发现（harvest）、读正文前复搜（prepare）、发评论前复搜（commit）。每次复搜都独立骑在小红书 AI 搜索「提交→导航到结果页」这个**不稳定入口**上，成功率 p 则整链 ≈ p³。

2026-07-11 Tmax 真实故障（dev ECS 日志 + 本机 edge.log + 代码三方交叉，7-agent 对抗验证）：

- 《AI自己改自己》：已选中、已读正文、**飞书已授权发布**，却在**发评论前的第三次复搜**以「未导航到结果页」掉链 → `target_not_found_on_commit`。人审白费。
- 《GPT-5.6 三档模型智价比》：**读正文前的第二次复搜**掉链 → `read_failed`。
- 决定性证据：同一搜索词「国产模型横向对比」13:55 成功两次、13:56:59 第三次失败——差别不在词，在于每次复搜时浏览器停在什么 URL。
- 这两条是**自动排期评论**（`ContentScheduler` 每分钟心跳 → `triggerComment` → `triggerManual(priority:'automatic')`）触发，非人工命令。自动路径失败更必然：送审时**放掉浏览器 → 自治浏览闭环立刻抢回、把页面带走 → commit 复搜必然找不回**。

根因是「一篇笔记要独立复搜三次」这个放大器，叠加复搜起点 URL 被残留 `search` 子串污染时**唯一可靠的提交按钮兜底被跳过**（`waitForSearchNavigation` 宽松 `includes('search')` 首轮即命中）。另发现一个假成功洞（Bug C）：诚实闸只验「是不是搜索页」、不验「是不是搜的这个词」，提交失败时浏览器赖在旧关键词结果页上会被当成功（edge.log 实证：命令搜「DeepSeek Claude成本」却报导航到 `keyword=facebook外贸开发客户`）。

## What Changes

**核心：keep-open —— 搜到一篇合适的笔记就攥住它，别再为它重搜。**

- 一次评论任务对每个搜索词**只做一次搜索**（发现）。搜到合格候选后：在**同一个持有中的边端租约**内打开该笔记 → 送飞书人审 → **审批期间浏览器停在该详情页等待**（租约不释放 → 自治浏览闭环拿不到浏览器、无法把页面带走）→ 通过则**原地发评论**。
- **不再有 prepare 复搜与 commit 复搜**。「commit 不信旧 DOM」的新鲜度不变量改由**发评论前就地重读当前详情页 `noteId` 核对**保证（不搜索、不重开）；被动过/失效则诚实终止、绝不在错笔记上发。
- **多次搜索只在「当前搜索词搜不到合格候选」时触发**（换下一个词）。一旦选中一篇，就提交到它：通过则发、超时/被拒/被动过则**直接结束本次任务，不再找下一篇**。
- **审批超时或被拒 → 结束发布流程**（释放浏览器、恢复自治浏览），不重试、不换词。
- 审批期间攥住浏览器对**自动排期评论**同样生效（原「标记只覆盖真 commit、不整段停浏览」的取舍在评论任务持锁期间被本 change 有意反转）；取舍：每次评论审批期浏览器被占 ≤ ~90s（受日上限管、风控 normal 才触发、<空闲看门狗阈值、像真人读笔记）。

**加固（发现搜索那一次仍要可靠）：**

- 边端 `waitForSearchNavigation` 判据改严：与 `browse-session` 的权威 `SEARCH_LIST_RE` 共用同一正则 + **要求 URL 相对搜索起点发生变化**，杜绝残留 `search` 子串让首轮误判成功、跳过提交按钮兜底。
- 关闭 Bug C：确认到达结果页时**核对 URL 的 keyword 参数等于本次要搜的词**，不等则不认作已导航（诚实回未到结果页）。
- 提交按钮兜底找不到元素时补 warn，便于真机定位。

**可观测性：**

- 终态结果卡**区分「自动排期评论」与「人工 /comment」**触发来源（当前通用模板不分来源）。

## Impact

- Specs: `comment-search-command`（MODIFIED 独占边端流程、择优/换词；ADDED keep-open 持锁贯穿审批、发前就地核对、发现搜索判据加固与关键词一致、回执区分来源）。
- Code: `aidcp-cloud/src/comment-agent/comment-scheduler.ts`（runTask 重构、租约时长、takeover 覆盖两路径、回执来源），`aidcp-cloud/src/comment-agent/edge-steps.ts`（去掉复搜步、日志措辞），`aidcp-edge/src/browse/browse-session.ts`（`interaction.comment` 发前就地核对 noteId），`aidcp-edge/src/browse/search-handler.ts`（nav 判据 + keyword 一致）。
- 无协议消息类型新增/删除（不触发协议四处同步）；`interaction.comment` payload 已带 `noteId`。
- 热点文件 `comment-scheduler.ts`/`browse-session.ts`/`search-handler.ts` 单写者，与并发 change `facebook-scheduled-comment` 串行。
- 红线守恒：MUST NOT 静默假成功——发前就地核对不过即诚实终止、绝不在错笔记上发；发现搜索未确认到结果页仍诚实回失败、绝不把 feed/旧页当结果。
