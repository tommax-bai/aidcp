# Facebook 评论「读了再写」+ 内容语言

## Why

首版 FB 定向评论的撰写器是**盲写**：只凭「账号人设 + 随机关键词」在**搜帖之前**就把评论写好，且 prompt 是中文、无输出语言约束。真机首测暴露两个问题：(1) 撰写器对一个**西班牙语**波多黎各群产出了**中文**评论（跟了 prompt/界面语言，而非内容语言）；(2) 评论与具体帖子无关（盲写、泛泛），被确定性相关性闸判 `weak_relevance` 拦下——一条都发不出去。小红书评论链本就是「先开帖读正文 + 滚评论区抓他人评论 → 再撰写」，FB 缺了这一环。

## What Changes

把 FB 评论链从「盲写」改成「读了再写」，对齐小红书：

> 搜群 → 选候选帖 → **开帖：读帖子正文（图片帖常空）+ 顶部他人评论** → **撰写（吃到正文+评论，用内容语言、顺着讨论写）** → 只拒不修校验 → 影子到此止步 / 真发提交+服务器确认

- **边缘**：`openPost` 抽帖子正文 + 顶部 N 条他人评论（嵌套 `role=article`，去作者名/界面词/纯人名标记评论、去重），经 `note.detail`（`content` + 新增 `comments?`）回传。图片帖无正文 → 诚实空、不臆造。真机在真帖上验证过抽取。
- **协议**：`note.detail` 加可选 `comments?: string[]`（复用消息、零新增类型）。
- **云端**：`runFacebookTargetedTask` 重排——撰写挪到开帖之后，撰写器吃到 `{keyword, container, postText, comments}`；相关性闸以「关键词 + 正文 + 评论」为语境（评论天然相关、on-topic 回复能过，仍守零重叠即拒）。撰写 prompt 带上正文 + 他人评论，指令**用与内容相同的语言写**（绝不用中文界面语言，除非原文是中文），顺着讨论回应。
- **影子模式语义变化**：由「纯云端、不下发任何 edge 命令」变为「**只读浏览**（搜+开帖）+ 撰写 + 校验，绝不提交」——因为撰写现在需要帖子上下文。安全不变量不变（影子绝不下发 `interaction.comment`）。

## Impact

- Specs: `facebook-scheduled-comment`（评论撰写依据 + 影子语义）。
- Code: aidcp-edge（executor/handler/protocol）、aidcp-cloud（edge-steps/scheduler/compose/protocol）。
- 无新增消息类型；防重复真发、成功记账、kill switch 收口均不变；对现役小红书零影响。
