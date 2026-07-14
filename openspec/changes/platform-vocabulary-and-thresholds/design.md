# Design — platform-vocabulary-and-thresholds (C3)

> cloud-only、无协议。**依赖 `humanize-interaction-prompts` 归档**（它 MODIFY comment-interaction/interaction-appraisal 同名 header）。所有 `文件:行` 为 2026-07-14 HEAD 实核。

## 1. 为什么门槛部分要等 humanize 归档

`humanize-interaction-prompts`（活跃 22/23）的 spec delta MODIFY 了：
- `comment-interaction`「精品门槛与每账号每日评论上限（后台可配、与风控配额取小）」
- `comment-interaction`「评估→撰写→去AI味→审批四段单职责角色」
- `interaction-appraisal`「点赞是选择性互动、收藏是更稀有的选择性互动」「互动筛选全程从严」

C3 的门槛平台化要改的正是「精品门槛」。若现在对着当前 main 文本写 MODIFIED，归档合并时会把 humanize 的改动顶掉。所以：**C3 现落的 spec delta 只含不冲突的新能力**（ADDED `platform-content-adaptation`）；门槛 MODIFIED 在实装期、humanize 归档后、对着 post-humanize 文本写（tasks 0.1 / 4.1）。

## 2. 词汇平台化：扩现有 profile，不另开表

现有 `CommentPlatformProfile`（`registry.ts:14`）已被 `comment-search-term-generator.ts`/`comment-target-picker.ts` 注入消费。C3 扩它承载浏览闭环 8 处 prompt 需要的站点名/内容名词/指标名词，**不另开第二张 lexicon 表**（否则同一事实两个源）。8 处 prompt 改从注入的 profile 取词，角色 MUST NOT 出现 `platform==='x'` / import registry。

## 3. 门槛平台化（post-humanize）

判据现状 `likeCount>300 && (collectCount>100 || likeCount>10000)`（`comment-appraiser.ts:28-31,107-108`）。平台化：`hasCollect=false`（FB）只放宽**收藏合取支**，主条件 `likeCount>阈值` **保留**（MUST NOT 退化为无门槛——否则 FB 任何帖都能评）。同时登记 spec↔code 漂移（spec 1000/300 vs 代码 300/100/10000），不在错 spec 上叠 MODIFIED。

## 4. comments[] 接进撰写

云端事件层 `NoteDetailData`（`event-bus/types.ts`）现无 comments 字段——协议 `NoteDetailPayload.comments[]` 到了 handler 就被丢。C3 补 `NoteDetailData.comments`，浏览闭环撰写器消费；合并两套 FB 撰写器（浏览闭环 `comment-composer.ts` 小红书口径 vs 定向评论 `server.ts facebookCompose` FB 口径）为共享 helper + 平台专属 caller。

## 5. contentTruncated + N6（条件，与 C2 P1 联动）

若 C2 探针 P1 证明 See more 展开路径需要显式截断标志：`note.detail.contentTruncated` 字段与其消费者护栏（N6：数据缺失≠低质量）**同批落、同旗标门控**，字段 MUST NOT 先于消费者上线。若 P1 证明全文本就在 DOM（textContent），则永久不加此字段。C2 阶段先抬高三处硬 slice 上限规避主要截断。

## 6. 不做

- ❌ 另开第二张词汇表（扩现有 profile）。
- ❌ 现在写门槛 MODIFIED（等 humanize 归档）。
- ❌ 改配额数值 / like-view 比阈值（需 C2 灰度真机数据重估，另开 change）。
- ❌ 角色内 `platform==='x'`（走注入闭包/profile）。
