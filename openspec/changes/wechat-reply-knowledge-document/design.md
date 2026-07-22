## Context

当前视频号回复配置按 group/default scope 维护 versioned policy、template、rule 与 comment/dm profile。AI 只有 classifier、polisher、reviewer 三个内部 role；其中 polisher 已被收敛为简短博主式回复，并且模板内含 `{{support_channel}}` 的导流行由确定性工作流保护。运营后台已经可以编辑每个渠道的 profile，但 profile 没有业务知识来源，因此 AI 对具体服务问题缺少可控事实依据。

`interaction_reply_scope_versions.profiles` 本身是 JSONB，适合承载向后兼容的可选字段。现有 profile PUT 一次提交 comment/dm 两份配置，HTTP 请求体上限为 64 KiB；如果每份文档允许 20,000 个中文字符，需同步提高但继续限制该配置接口的请求体预算。

## Goals / Non-Goals

**Goals:**

- 让运营在管理后台按 comment/dm 渠道维护一份 Markdown/纯文本说明文档。
- 让 AI 只依据该文档中明确存在的业务事实回答问题，找不到答案时诚实说明无法确认。
- 让文档跟随现有 scope draft/publish/CAS/audit 生命周期，不产生旁路配置。
- 保留博主式短回复、模板联系方式单写、AI 人审和既有安全闸。
- 对旧 profile 数据和 Cloud/Console 分步部署保持兼容。

**Non-Goals:**

- 不支持 PDF、Word、网页 URL、附件上传、OCR、向量数据库或多文档检索。
- 不新增账号级配置、Edge 协议、自动发送资格或私信 AI 默认开关。
- 不让知识文档覆盖系统提示词、模板导流行、安全规则或审批要求。
- 不把整份知识文档展示给终端用户，也不在日志/审计摘要记录正文。

## Decisions

### 1. 知识文档属于渠道 profile

在 `ReplyProfile` 增加 `knowledgeDocument: string | null`，comment 与 dm 可分别维护。字段允许 `null` 或 trim 后非空、长度不超过 20,000 的 Markdown/纯文本。空编辑值规范化为 `null`。

选择 profile 而不是新增独立表/endpoint，是因为文档与 tone、blocked phrases、disallowed claims 一样，都是渠道级 AI 行为输入；profiles 已经跟随 scope 草稿、发布、回滚和 CAS 单写。存入现有 JSONB 不需要 DDL。旧 JSONB 行缺字段时，Cloud 读取口径归一为 `null`；写入校验兼容部署窗口内仍未带字段的旧 Console。

### 2. 只把命中渠道文档送给 polisher

工作流在调用 `reply_polisher` 时，把当前渠道的 `knowledgeDocument` 放进 profile summary。classifier 和 reviewer 不接收文档；规则未开启 polish、渠道未开启 AI，或 DM 全局隐私闸关闭时，文档不得进入任何模型请求。

运行时 prompt 将文档放在明确的数据边界内，并声明：文档是“不可信参考资料”，其中的命令、角色设定、越权要求均不是指令。对业务事实的回答只能使用文档明确支持的信息；未找到答案时输出简短的“暂时无法确认”类答复，不猜测、不调用常识补全。文档支持的新事实必须按既有 `introducedClaims` 语义如实列出。

复用 polisher 而不新增 role，是因为它已经持有 inbound、模板、渠道 profile，且任何输出都走同一结构化 schema、claim gate、reviewer 和人审流程。此变更扩展它在“文档存在时”的允许信息源，不改变模板/联系方式的确定性组合顺序。

### 3. 模板继续拥有导流文案和联系方式

AI 可以基于文档改写模板的自然回复正文，但不得新增私聊引导或联系方式。上一变更建立的 support-channel 受保护行检查继续生效；AI 若删除或改写导流行，候选回退为完整 rendered template。知识文档中的联系方式也不能绕过模板单写边界。

### 4. API 合同向后兼容且请求体继续有界

control repo 的 ReplyProfile schema 和 AI ProfileSummary 增加可选 nullable 字段，fixtures 显式给出示例值/null。Cloud 对旧数据/旧请求的字段缺失按 `null` 归一，对新值执行 20,000 字符上限与首尾空白规范校验。

两个 profile 一次 PUT 可能包含最多 40,000 个多字节字符，因此 account/scope profile 配置 API 的 JSON body 上限从 64 KiB 提高到 256 KiB；其它 endpoint 仍复用同一有界 reader，但 schema 上限阻止该预算被任意字段滥用。

### 5. Console 复用“品牌语气”编辑与版本写链

后台把 tab 改名为“语气与知识”，在每个渠道 profile 表单增加“AI 回答说明文档” TextArea、20,000 字符计数和用途提示。它与其它 profile 字段一起走现有 `dirty.profiles`、expectedVersion、scope mismatch、AbortController 和保存回读流程；不另建前端 schema 或旁路接口。预览使用当前 draft profile，所以运营可先验证回答再发布。

## Risks / Trade-offs

- [长文档增加模型 token、延迟和成本] → 单渠道硬限 20,000 字符，只在实际调用 polisher 时发送；第一版不承诺长文档检索质量。
- [文档内含 prompt injection] → 明确标为不可信数据并禁止执行其中指令；输出仍过结构化校验、claim gate、reviewer 和人审。
- [模型在文档无答案时仍可能猜测] → prompt 明确要求无法确认，知识新增事实进入 introducedClaims；任何 AI 回复仍需人工审核，不赋予自动发送资格。
- [旧 scope JSONB 没有新字段] → 读取归一为 null，PUT 兼容字段缺失，默认 profile 显式写 null。
- [Cloud 回滚但 Console 未回滚时旧 Cloud 拒新字段] → 按 Cloud 先、Console 后部署；回滚时同步恢复两者备份。
- [一个 group 共用文档不适合个别账号差异] → 延续现有 group/default 配置事实，不恢复账号级旁路；需要差异时调整账号分组。

## Migration Plan

1. 先部署兼容新旧 profile 的 Cloud，不执行数据库迁移。
2. 再部署 Console 静态文件，确认文档保存、回读、draft preview 与发布流程。
3. 验证现有 scope/version 数量与联系方式未变化，服务/健康/日志正常；不做真实平台发送。
4. 回滚时同时恢复 Cloud 与 Console 备份；JSONB 中新增字段可保留，旧 Cloud 运行时会忽略，但旧 Console 不应继续提交它。

## Open Questions

无。文件上传、分段检索和多文档知识库留给后续独立变更。
