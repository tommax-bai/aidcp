## Context

人设 onboarding 当前把语气与内容关键词作为 `persona.generate.keywordSelections` 交给云端；生成器只产 `identity + interests`。Soul 模板已经存在 `behavior_guidelines.like_principle`，普通笔记点赞与评论点赞也都读取该原则，但没有结构化的倾向档位。另有 `mandatory_interactions` 确定性强制动作链，不能被本需求复用。

本变更横跨 Edge Electron 向导、Cloud 人设生成与两类点赞判定。需要同时保持旧客户端兼容、现有人设 YAML 可读、普通互动的安全闸不变，以及“不把偏好升级成强制授权”的边界。

## Goals / Non-Goals

**Goals:**

- 提供默认“正常”的“正常 / 喜欢 / 更喜欢”三档点赞倾向。
- 让档位随人设 YAML 持久化、热加载，并稳定影响笔记点赞与评论点赞。
- 高档位比低档位更容易点赞，但任何档位都允许 pass，且继续受内容判断、预算、比例、频控、风控与真实回执约束。
- 生成的 `like_principle` 同时表达账号兴趣口味与档位强度。

**Non-Goals:**

- 不新增、修改或自动生成 `mandatory_interactions`。
- 不提供“每篇必点”、绕过 LLM、绕过风控/配额或直接点击的能力。
- 不新增数据库列、消息类型或 command bridge 动作。
- 不改变收藏倾向、关注倾向和评论授权模式。

## Decisions

### D1：沿用 keywordSelections，以受控机器标记传档位

Edge 在既有 `keywordSelections` 末尾加入一个精确标记：`like_affinity:normal|like_more|like_most`。Cloud 生成器先解析并移除该标记，再把剩余关键词交给人设生成；旧客户端没有标记时默认 `normal`，未知/重复标记也回落 `normal` 并不污染兴趣关键词。

这样无需修改两份协议热点或增加消息类型，同时标记仍经过现有条数/单项长度上限。备选方案是给 `PersonaGeneratePayload` 新增字段，但会扩大协议同步与兼容面，本需求没有必要承担该成本。

### D2：档位落在 behavior_guidelines.like_affinity

Soul 新增 `LikeAffinity = 'normal' | 'like_more' | 'like_most'`，并在 `behavior_guidelines` 增加可选 `like_affinity`。loader 对存在的字段严格枚举校验，serializer 保留往返；字段缺省等价 `normal`，因此历史 YAML 不需迁移。

生成器在 LLM 产出合法 `identity + interests` 后，由代码确定性补齐 `behavior_guidelines`：`like_principle` 结合生成出的主兴趣与档位文案，其他行为原则采用现有克制基线。由代码补齐而不是要求模型一次多产四个必填字段，可避免提高 persona 生成失败率，并保证档位不会被模型忽略。

### D3：笔记点赞通过普通判定 prompt 调整，不改动作映射

`InteractionAppraiserRole` 在 prompt 与 persona source 片段中显示结构化档位及对应软指导：

- `normal`：保持当前选择性标准，多数普通内容 pass；
- `like_more`：对兴趣明确相关且带来真实正向感受的内容适度降低点赞阈值；
- `like_most`：对兴趣相关、安全、非低质内容明显偏向点赞，但仍允许 pass。

解析、预算过滤、dispatcher、RiskController 与 Edge 后验确认完全不改。特别地，本字段不参与 `mandatoryInteractionPrompt` 或 mandatory typed context，故不会进入确定性旁路。

### D4：评论点赞只调整既有随机克制概率，其他闸不动

评论点赞现有 Bernoulli 概率默认 0.6。按档位映射为 `normal=0.60`、`like_more=0.75`、`like_most=0.90`；显式测试/配置注入的 `likeProbability` 仍优先。候选过滤、LLM 价值判断、每场上限、约 15% note-like 比例、日配额、风控和成功回执计数不变，因此档位只提高进入判断的机会，不保证执行。

### D5：客户端默认值可见且预览可核对

“点赞倾向”面板位于“语气调性”下方，三项单选，“正常”初始 active。预览摘要使用中文标签“点赞倾向：正常/喜欢/更喜欢”，发送时再转换为机器标记；UI 不展示内部枚举。更新人设沿用同一选择与 persist 路径，确认前不改变当前生效人设。

## Risks / Trade-offs

- **[高档位被误解为必点]** → UI 与规范明确为“倾向”，runtime 始终保留 pass，测试断言不产生 `mandatory_interactions`，且既有安全闸全保留。
- **[机器标记污染 persona 兴趣]** → Cloud 在 build prompt 前精确剥离标记，测试断言原始 prompt 不含内部 token。
- **[历史 persona 无档位]** → loader/运行时统一按 `normal` 解释，零迁移、零行为突变。
- **[LLM 对软指导响应有波动]** → 结构化档位与档位文案确定性注入；只承诺单调倾向，不承诺固定点赞率。
- **[评论点赞上升触碰比例闸]** → 约 15% ratio gate 仍是更外层硬上限，高档位只能更快趋近上限，不能越过。

## Migration Plan

1. 先发布 Cloud：识别新标记、持久化新可选字段并读取倾向；旧 Edge 无标记时仍为 `normal`。
2. 再合入 Edge 客户端 UI；按规范不在未明确要求时构建安装包。
3. 回滚 Edge 只会恢复无标记请求；Cloud 自动按 `normal`。回滚 Cloud 前，新 YAML 中的可选字段会被旧 loader 忽略，但旧 serializer 更新该人设时可能丢字段，因此正常回滚顺序为先 Edge、后 Cloud。

## Open Questions

无。
