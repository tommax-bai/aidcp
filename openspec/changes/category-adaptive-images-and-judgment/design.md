## Context

配图链路现状（`aidcp-cloud/src/publish-agent/`）：`ImageSetPlanner` 读正文产「几张图 + 每张中文主体」→ `ImagePromptComposer` 把每个主体翻成**英文**描述、并从系统侧无差别拼接一段**全局固定风格常量** `IMAGE_STYLE_BASE`（flat-vector + tech-blue + isometric + no人 + no字）→ `ImageGenerator` 调 provider（即梦 Seedream 5.0 中文原生 / 通义万相兜底）。该常量的作用本是「保图集内部风格统一」，但被实现成**全局单例**，于是把「一帖内一致」放大成「全平台所有帖一致」，并把所有题材锁死为技术图。

判定侧同型：质量评审只按「干货信息密度」打分且无人设入参；收藏判定 prompt 举例「代码/架构图才配收藏」；评论精品门槛写死固定绝对值 `likeCount>1000 且 collectCount>300`（`comment-interaction` spec 硬需求）；浏览卡片点击评估把「AI/技术」当默认兴趣、「娱乐/明星」钉死为无关；正文感叹号「整篇最多 1 个」一刀切。

约束：系统是通用全品类、人设驱动号；红线含「无声假成功」「图集帧内一致」「AC-PUB 不静默发布」；生成 prompt 与后台只读预览须同源；sub-repo 工作树当前有并发方 WIP。

## Goals / Non-Goals

**Goals:**
- 把「品类 + 人设自适应」作为一等输入贯穿配图、质量评审、互动/评论门禁、浏览相关性。
- 治同质化：帖内一致不变、帖间因品类/人设而异。
- 保守放开真人/封面文字（合规优先），补一道产后校验守「无声假成功」。
- 判定口味随品类，但**不动**发布放行闸与稀缺闸的存在性。

**Non-Goals:**
- 不改文本生成侧残留技术 few-shot（归 `persona-driven-content-pipeline` 4.6）。
- 不动 `buildDeAiRewritePrompt`「逐字冻结」prompt。
- 不加管理后台前端（运营手调门禁 UI 为后续 follow-up）。
- 不扩 `style.type` 四值枚举、不落库品类、不引入跨帖风格轮换器（YAGNI）。

## Decisions

### D1. 风格作用域：全局常量 → 「品类 → 风格档」注册表，每帖选一次
- **做法**：新增 `STYLE_PROFILES: Record<Category, StyleProfile>`（`StyleProfile` = 媒介/风格族 + 色板 + 光线 + 构图 + 质感 + 人物策略 + 比例 + 封面变体 + 品类 few-shot）与 `resolveStyleProfile(category, {cover})`。`Category` 为固定字面枚举（干货/知识、美妆护肤、美食、穿搭、旅行、家居、情感/治愈、职场/成长、技术示意图 + 安全兜底档）。
- **选档时机**：`ImageSetPlanner` 读正文时顺带判 `category` 写进 `ImageSetPlan`（未知/失败回落兜底档、绝不 brick）。因 `ImageSetPlan` 是 per-post 对象，档位天然「帖内锁定」。
- **注入时机**：`ImagePromptComposer` 取 `profile.styleBase` 逐字拼进本帖图 1..N、图 0 用 `coverStyleBase`。**不变量从「全局逐字一致」收敛为「帖内逐字一致」**——图集一致完全保留，帖间因品类而异。
- **备选**：① 让 LLM 每张自由产风格（否决：破帖内一致、且 LLM 产风格漂移不可控）；② 保留全局常量但按 persona 换（否决：persona 与内容品类不总一致，正文品类信号更直接）。风格 DNA 仍是模板常量、仍禁止 LLM 产（延续现红线），只是「一个串」变「一张表 + 一次解析」。

### D2. Prompt 语言：中文主体 + 英文风格 token
- 主体/场景/文化元素保留**中文**（Seedream 原生双语，直接吃中文语境；现在先翻英文是反模式）；风格族/光学/画质 token 用**英文**（西方美学/光学术语英文关联更强）。
- **校准**：「中文必碎、风格必须英文」在原生双语 Seedream 上适用性打折（对抗核验判 mixed）——故英文风格 token 是「低风险且划算」的默认，不是铁律；强中文文化主体允许风格词中英混排，最终以线上 A/B 为准。停止 `ImagePromptComposer` 的「翻成英文主体」指令。

### D3. 去 provider 侧第二风格源 + 竖版比例
- 现在 provider 客户端还把 4 值 `imageStyle` 枚举以「，风格：<enum>」二次拼进正文，与风格档冲突（Seedream 对冲突风格指令明显劣化）——生成时不再把该枚举传给 provider。
- `defaultSize` 由 `2048x2048` 方图改竖版 3:4（贴小红书信息流，占屏多约 40%）。**先核实线上实跑 Seedream 版本（代码默认 `4-5-251128` vs 台账 `5-0-260128`）允许的合法 size 串再改**，乱填会被 provider 直接报错；全帖同比例守帧内一致。

### D4. 真人 / 封面文字：分级 + 产后校验（保守口径，用户已定）
- 人物三档写进风格档：默认无人/静物 → 无脸匿名人体（背影/局部/POV/剪影）→ 需正脸用「明确非写实虚拟人物」，**绝不写实真人正脸**。
- 封面文字默认「留白 + 后期程序化叠字」（不让模型画中文长标题，避免糊字=假成功）；合规 AI 标识走已有 `ComplianceDecision.ai/aiEnforced` + 发布声明，不靠画面水印。
- **产后校验（新增诚实闸）**：仅对「含真人 或 封面出字」的图做——校验乱码字 / 是否像可识别真实·名人，命中即丢弃该张重生成，绝不因「prompt 写了 faceless/no-text」就假定生效。首版只覆盖这两类，其余靠内页 no-text + faceless 默认兜底。

### D5. 质量评审：接人设 + 品类自适应维度（不动放行闸）
- `buildAssemblerPrompt` 加 `soul` 入参（`quality-scorer.ts` 的 `extractInput` 从 `snapshot.trigger.generateInput.soul` 直接取，无新跨阶段 plumbing）；「内容价值」维度按品类切子标准，「真实感」改「贴合人设声音」。
- **红线**：只改**打分口味**，`gatekeeper` 的 `auto_publish>=75` / `manual` / `abort` 分支、`QualityScorer` 降级公式、`getDefaultOutput=50` 一律不动（AC-PUB）。改函数签名须同步 `prompts-preview.ts` 补 `EXAMPLE_SOUL`/style（typecheck 会红以守同源）。

### D6. 门禁品类自适应：调口味不移闸
- 收藏判定：去「代码/架构图」技术示例，改品类中立可复用性、具体类型交上文已注入的收藏原则；收藏率数值地板改为按人设/品类可配（审美/灵感类放宽或旁路），**保留地板存在性与「0 赞不收藏」防线**。
- 评论门槛：把固定绝对值 `collectCount>300` 这一必要条件改为**品类自适应/比例/按账号可配**；**首选比例/百分位而非纯 OR**（纯 OR 会让更多笔记落到昂贵 LLM decide，违背「最便宜阶段拦」的设计）。保留「必要非充分」的硬闸存在性、每日上限、风控取小、LLM 精品判定 + 飞书人审多道稀缺闸。
- 浏览相关性：`content-evaluator` 删固定题材名，改从账号兴趣派生相关性；保留「无匹配诚实 skip、不编造」，另加一个「无论人设都不碰」的全局品牌安全禁区兜底。

### D7. 感叹号按品类分档 + 双侧口径同步（唯一真正的两侧 sync）
- `buildCreatorPrompt` 感叹号上限按品类/人设分档；**同时** `post-processor.ts` 的感叹号检测与「过量感叹号」虚拟命中须接受同一品类/人设参数——否则生成放宽了、后处理仍判过量、把生活类正文推向 rewrite/人审。这是生成约束与检测口径共用一份、必须两侧一起改的地方（区别于「preview 只读镜像」那种自动同源）。评论侧复用发帖 `PostProcessor` 的部分按短评软化（保留自然口语感叹）。

## Risks / Trade-offs

- [Seedream 合法尺寸未知，乱改 `defaultSize` 会让 provider 直接报错] → 改前先核实线上实跑版本与其允许的 3:4 尺寸串；不确定则保持方图、只上品类风格档（比例改动可拆到后续小批）。
- [放开真人抬高肖像/换脸合规风险] → 保守分级（默认无脸、需正脸用非写实虚拟人物）+ 产后校验；不允许写实真人正脸。
- [语言因果 mixed，中文主体+英文风格未必对 Seedream 最优] → 当默认不当铁律，强中文主体允许中英混排，上线后 A/B。
- [评审/门禁口味放宽可能让更多内容进 auto_publish / 更多笔记进评论] → 评审不动放行阈值；评论门槛首选比例而非纯 OR、保留每日上限与风控取小；变更点用 `log` 显式记录，避免「静默放宽」。
- [分类器可能又收敛到少数几档，在品类层面重演同质化] → 首版观察即可；必要时再加跨帖去重（YAGNI，暂不做）。
- [并发方 WIP 占用同文件（`prompts.ts`/`role-catalog`/`server.ts`）] → 实装排期与 `split-topic-roles`/`persona-driven` 协调、避开脏文件；分批小改、每批测试全绿再提交。

## Migration Plan

- 品类为每帖运行时派生、不落库；无 DB 迁移、无协议改动。
- 分批落地（每批独立可测可部署）：① 配图风格档 + 中文主体 + 去第二风格源（比例改动视 Seedream 尺寸核实结果决定同批或拆后）；② 质量评审接人设 + 品类维度（补 preview 同源）；③ 感叹号双侧分档 + 禁用词校准；④ 互动/评论门禁品类自适应；⑤ 浏览相关性去偏见 + 评论去 AI 味接人设。
- 每批：`test:acceptance` → `test` → `typecheck` 全绿（AC-PROTO/AC-PUB/AC-RISK 必过）→ commit → 按需走安全序列部署（备份 → rsync → restart → healthcheck → 失败回滚），绝不碰 isales。
- 回滚：纯 prompt/逻辑改动，按批 revert commit + 重部署即可；无状态迁移不可逆项。

## Open Questions

- 线上实跑 Seedream 到底是 `4-5-251128` 还是 `5-0-260128`？其同步 `/images/generations` 允许的 3:4 尺寸串是什么？（决定 D3 比例改动能否与风格档同批。）
- 产后校验（乱码/肖像）用什么实现——轻量规则 + 可选二次模型判定？首版是否只跑「含真人/封面字」子集即可（当前倾向是）。
- 收藏率地板/评论门槛「按账号可配」的配置载体：复用 `category_config` 面 vs 新配置项？本 change 先给代码级品类默认，运营可调 UI 留后续 console follow-up——确认可接受。
