## Why

账号人设初始化目前只能设置语气和内容偏好，客户无法表达账号对点赞的整体倾向；所有新生成人设因此沿用同一套克制点赞口径，与希望更积极表达认可的账号定位不匹配。需要新增一个可持久化、可解释的三档倾向，同时明确它只是普通互动判断的软偏好，不能借用或生成强制点赞规则。

## What Changes

- Edge 账号人设向导在“语气调性”面板下新增“点赞倾向”单选面板，提供“正常 / 喜欢 / 更喜欢”三档，默认“正常”。
- 预览摘要与生成请求携带所选档位；未选择或旧客户端请求按“正常”处理，保持兼容。
- Cloud 人设生成把档位写入既有 `behavior_guidelines` 模板，保留结构化 `like_affinity`，并生成与档位、人设兴趣相匹配的 `like_principle`。
- 普通笔记点赞与评论点赞读取该档位：档位越高越倾向点赞，但内容价值判断、随机克制、预算、频控、风控、去重和真实执行确认仍然生效。
- 明确禁止把点赞倾向转换为 `mandatory_interactions`、确定性点赞或任何绕过普通判断与安全闸的动作。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `persona-keyword-generation`: 人设初始化向导新增三档点赞倾向，并把选择稳定映射到云端生成的人设模板。
- `account-persona-config`: `behavior_guidelines` 支持可选、严格校验并可往返持久化的 `like_affinity` 字段。
- `interaction-appraisal`: 普通笔记互动判定按账号点赞倾向调整软偏好，且不得进入强制互动路径。
- `comment-like-interaction`: 评论点赞的随机克制概率按账号点赞倾向分档，但既有质量、比例、配额与风险闸保持不变。

## Impact

- `aidcp-edge`: Electron 人设向导 HTML/CSS/renderer 状态采集与 UI 回归测试。
- `aidcp-cloud`: persona generator、soul 类型/loader/serializer、笔记互动与评论点赞 appraiser，以及对应单元/验收测试。
- 不新增消息类型、不修改 command bridge；沿用 `persona.generate.keywordSelections` 传递受控偏好标记，避免协议热点扩张。
- 无数据库迁移；倾向随现有 `persona_config.soul_yaml` 持久化并热加载。
