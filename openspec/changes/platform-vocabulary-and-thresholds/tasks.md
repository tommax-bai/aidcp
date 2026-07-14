## 0. Blocker

- [ ] 0.1 Confirm `humanize-interaction-prompts` is archived before authoring any MODIFIED delta against `comment-interaction` / `interaction-appraisal`; author threshold MODIFIED against post-humanize spec text (do not revert humanize). <!-- STILL BLOCKED：humanize 22/23 未归档（其 9.4 卡 category-adaptive 先归）。故 4.1 的**代码**已落、**spec MODIFIED delta 未写**（见 4.1）。 -->

## 1. aidcp-cloud — Vocabulary platform-ization (ADDED capability)

- [x] 1.1 Extend `CommentPlatformProfile` with the site/content/metric nouns the browse-loop prompts need; keep it the single lexicon. <!-- cloud 695d5f3 **偏离（简化）**：现有 CommentPlatformProfile 已含 siteName/contentName/metrics.{like,collect} —— 8 prompt 替换**无需新字段**。foundation = dispatcher 把 `commentProfileForPlatform(accountPlatform)` 随 commonOptions 注入所有浏览闭环角色（缺该字段的角色因 spread 豁免 excess-check 天然忽略）。metrics.collect==='' 即「无收藏概念」信号。 -->
- [x] 1.2 Remove hardcoded 「小红书 / 笔记 / 收藏」 from the role prompts, reading from the profile; MUST NOT open a second lexicon table. <!-- cloud 695d5f3：6 角色去硬编码（content-evaluator/content-curator-role/comment-reviewer/comment-appraiser/comment-like-appraiser/concept-extractor-role），读 siteName/contentName/metrics；指标行**空收藏名词时省略收藏子句**（FB 不渲染「收藏：0」/「⭐0」）。**follow-agent 未做**（其「获赞与收藏」是作者主页指标、FB 经 C4 canVisitProfile 结构不访主页 ⇒ 惰性，归入 profile 层/后续）。3 路对抗评审：XHS 逐字节零回归 / FB 措辞正确无幻影 / 门槛安全，全 SAFE。 --> <!-- 补漏 cloud 1cfddb5：comment-composer.buildPrompt **此前漏了**——它有 profile 字段但 prompt 正文仍硬编码「笔记」「当前笔记：」。1cfddb5 把 contentName / maxCommentLength 读进 buildPrompt（缺省 profile=小红书 ⇒ XHS 逐字节零回归，新测锁死）。 -->
- [ ] 1.3 Parameterize `hot-lead/heat-velocity.ts` published-time parsing per platform. <!-- DEFERRED **且前提已被推翻**（2026-07-15 scout 坐实）：**Facebook 根本不上报发布时间**——edge 三条 FB 详情产出路径（inline-reader / post-reader / comment-handler）全无时间字段，`src/facebook/**` 零命中，`FacebookPostDetail`/`FacebookInlineReadResult` 无 temporal 字段。云端 `parsePublishedHoursAgo` 唯一外部入口 `hot-lead-detector.ts`，`heat-velocity.ts:37` `if (!text) return null` 先短路 ⇒ 加 FB 词元是**纯死代码**、零可观测行为。**要真做必须先 edge 落地**：在 FB 详情抓时间节点（真机 CDP 探针找选择器，FB 渲染成 header 里的 `<a>`/`<abbr>`）+ emit `publishedAtText`（协议已有该字段、无需四处同步），**再**云端写词元表（否则是猜）。且 FB 英文时间词（`2h`/`3d`/`Yesterday`）短、绝不可与 XHS 词表合并（防 `h`/`m` 误触发 XHS 地区后缀），须按平台分支、XHS 表逐字不动。红线：缺失/未识别时间**绝不**默认 0（会伪造无限速率、自动触发引流评论），fail-closed 到 `unparseable_time`。⇒ 重新定性为「edge-first 2 仓 + 真机探针」，非 C3 单仓小活；留独立后续。 -->
- [x] 1.4 Make `deep-reader.ts` image-vs-text heuristic platform-aware so a Facebook image post with empty content is not misjudged as a long-text post. <!-- cloud 695d5f3 **偏离（更小更对）**：根因是 `imageLed = textLen > 0 && ...` 的 `>0` 守卫把空正文误判长正文。改 `imageLed = textLen < SHORT_BODY_THRESHOLD`（含 textLen===0）：空正文按图文主导（提高翻图概率），符合「数据缺失≠低质量」。未穿 mediaType（NoteData 无该字段，穿它更重）——空正文启发式已解本 bug。 -->

## 2. aidcp-cloud — Comments into compose + merge FB composers

- [x] 2.1 Add a comments field to `event-bus/types.ts` `NoteDetailData`; feed captured post comments into the browse-loop compose step. <!-- cloud 1cfddb5：`NoteDetailData` + 两处 `NoteData`（dispatcher / content-curator-role）加 `comments?: string[]`。**关键发现**：边缘 FB 三条详情路径（inline 读 / 详情深读 / /comment 开帖）**早就在 note.detail 里带 comments**、协议也早有该字段——此前唯一丢弃点就是云端事件类型没声明它（TypeScript 看不见 ⇒ 运行时 currentNote 里其实有、撰写器拿不到）。撰写器 onAppraised 现读 `note.comments`。**XHS 对等**：其 note.detail 不带评论，评论区正文只在 `action.completed{scroll_comments}.candidates` 里 ⇒ dispatcher 新增归集（就地写 currentNote.comments，noteId 匹配闸 + 空白过滤）。测试：composer note.comments→prompt（+1）、dispatcher harvest→compose 端到端 + noteId 错配不归集（+2）。 -->
- [~] 2.2 Merge the two Facebook compose paths into a shared draft helper with platform-specific callers. <!-- 部分完成 cloud 1cfddb5：**2.2 的真实价值（scout 挖出的活跃缺陷）已单独落**——浏览闭环撰写器 prompt **完全没有「用正文语言写」规则**（只有 server.ts 定向评论路径有），C3 门槛放宽（300+赞）刚放大了「往当地语言 FB 群丢中文评论」的暴露面。1cfddb5 给 `CommentPlatformProfile` 加 `composeLanguageRule?`（单一词表铁律：profile 一个字段、不另开表；FB 声明、XHS 缺省不渲染 ⇒ XHS prompt 零回归），并加 FB 空正文诚实提示（「没有文字正文、别臆造画面」）。**仍 DEFERRED**：把 server.ts `facebookCompose` 改成 CommentComposer 的 caller（真正的「合并」）——scout 标注该合并含 3 处**真实行为变更**（模型选型从全局默认→browse:comment_composer 配置=一次活跃发帖路径上的模型热切换 / sanitize @-strip 弱化诚实拒绝 / maxCommentLength 超长返回 null 丢失「过长」区分），风险高于收益，留后续 change 专门做。 -->

## 3. aidcp-cloud / aidcp-edge — Remove bare platform branches

- [ ] 3.1 Fold the dispatcher `platform==='facebook'` bare branches and edge `main.ts` branches into the driver/registry interface. <!-- DEFERRED（纯 cleanliness）：实测云端只 3 处裸分支（role-dispatcher :1611/1900/1921，非提案说的 6——另 3 已走 helper），edge 2 处（main.ts :1239/:1247）。留后续。 -->

## 4. Thresholds (post-humanize, MODIFIED)

- [~] 4.1 Parameterize the quality-comment threshold per platform: collect-less platforms relax only the collect conjunct, the main like threshold is preserved, MUST NOT degrade to no threshold. <!-- cloud 695d5f3 **代码已落**：comment-appraiser `hasCollect = metrics.collect!==''`；`collectOk = !hasCollect || collectCount>100 || likeCount>10000`；主 `likeCount>300` 恒保留。修「FB 只有万赞爆帖能评」旧 bug（collectCount 恒 0 让 collectOk 退化成只认 >10000）。测试：FB 500 赞/0 藏过、300 赞不过（无零门槛）、XHS 零回归。**spec MODIFIED delta 仍待 post-humanize 写**（0.1 未解），且需登记 spec↔code 门槛漂移（spec 1000/300 vs code 300/100/10000）。 -->

## 5. contentTruncated + N6 (conditional, C2 P1)

- [ ] 5.1 Conditional truncation flag + consumer guards. <!-- DEFERRED（条件性）：C2 P1 实测 textContent 捷径对无折叠帖成立、折叠帖点展开读全文 ⇒ 就地读拿的是全文，暂无显式截断标志需求。若灰度观测到截断再落。 -->

## 6. Verification

- [x] 6.1 Cloud unit tests: FB threshold no longer requires ten-thousand likes while a low-heat post is still blocked; prompts carry no 「小红书/收藏」; DeepReader empty-content post not misjudged as long text. <!-- cloud 695d5f3：comment-appraiser.test 门槛平台化 4 例（FB 500/300/301 + XHS 零回归）；deep-reader.test 空正文 random=0.5 翻图；prompt 去硬编码由 6 文件 diff + 对抗评审覆盖。compose consumes comments[] 随 2.1 DEFERRED。 -->
- [x] 6.2 `npm run test:acceptance` → `npm test` → `npm run typecheck`; AC-RISK green. <!-- cloud 695d5f3：acceptance 50/50 + full 2035/2035 + typecheck 净。 -->
- [x] 6.3 Rebase, integrate, push cloud to `master`, deploy dev; register cluster 69. <!-- cloud 695d5f3：串行接 C4（19b2e13）后 ff-merge pushed；dev 部署（backup cloud.bak.c3vocab-20260714-232627.tar.gz，healthcheck active/NRestarts=0/8787/PG select 1/飞书长连接）。簇 69 backlog 登记 TBD（随批）。 --> <!-- 2026-07-14 dev deployed -->

## 7. Change Record

- [x] 7.1 Update this task record with commits and validation. <!-- 台账已回写（cloud 695d5f3 + dev 部署）。`openspec validate --strict` + archive 待 0.1（humanize 归档）解 + spec delta 写完；C3 仍 ACTIVE。 -->

### Landing status（2026-07-14）

**cloud master `695d5f3` LANDED + DEPLOYED dev**（接在 C2 开关 `c04051e` + C4 `19b2e13` 之后串行）。core = 词汇平台化（6 prompt）+ 门槛平台化代码（FB 评论 bug 修复）+ deep-read 空正文启发式。3 路对抗评审全 SAFE/severity none。

**行为影响提醒**：门槛修复**放大 FB 评论**（FB 现对正常热度帖=300+赞评论，不再只万赞爆帖）。仍过人审闸（除非账号 auto_approve），dev only。

### Landing status 追加（2026-07-15）— 2.1 + 2.2 语言规则 + 1.2 补漏

**cloud master `1cfddb5` LANDED + DEPLOYED dev**（backup `cloud.bak.c3-21b-20260715-064818.tar.gz` + `.env.bak.c3-21-20260715-064818`；healthcheck active/NRestarts=0/8787/飞书长连接/PG select 1；部署前 --checksum dry-run 确认 5 个 src 文件与 695d5f3 base 逐字相符、无并发覆盖）。含：**1.2 补漏**（comment-composer.buildPrompt 此前漏去硬编码、仍写死「笔记」，现读 contentName）+ **2.1**（comments[] 入撰写：FB 走 note.detail 早已带回但被未声明的事件类型静默丢弃、XHS 走 scroll_comments candidates 归集）+ **2.2 的活跃缺陷部分**（浏览闭环撰写器补语言规则 composeLanguageRule + FB 空正文诚实提示；治 C3 门槛放宽后「中文评论进当地语言 FB 群」的暴露面）。acceptance 50/50、full 2042/2042、typecheck 净。7 新测锁死。

**新增 DEFERRED**：2.2 的 server.ts `facebookCompose` → CommentComposer caller 的**真正合并**（含 3 处活跃行为变更，风险高，留专门 change）。

**DEFERRED（C3 仍 ACTIVE，留后续 / 解阻塞后做）**：1.3 heat-velocity 平台时间解析（**前提已被推翻 = FB 不上报发布时间 ⇒ 需 edge-first + 真机探针，见 1.3 更新注**）、2.2 撰写器真正合并（见上）、3.1 裸分支收口、4.1 的 spec MODIFIED delta（阻塞于 humanize 归档）、5.1 contentTruncated（条件性）。**归档前置**：0.1（humanize-interaction-prompts 归档）+ 上述 spec delta。
