## MODIFIED Requirements

### Requirement: 客户端 onboarding 关键词向导经边缘发起的 WS 请求触发云端生成

Electron 客户端 SHALL 在扫码登录、握手完成（账号身份已确立、真实 userid 而非 env-label）后提供人设向导：客户按维度选择关键词——**垂类（枚举快捷选 + 「自定义」自由文本兜底长尾，单选）、兴趣（少量高频标签多选 + 自由文本兜底长尾）、语气（枚举单选）**；并在“语气调性”面板下提供**点赞倾向（正常 / 喜欢 / 更喜欢，单选，默认正常）**。点赞倾向 MUST 有真实输出映射：客户端 SHALL 以受控标记随 `keywordSelections` 发送，云端 SHALL 在生成兴趣关键词前剥离该标记，并把档位写入人设 `behavior_guidelines.like_affinity` 与匹配账号兴趣的 `like_principle`；MUST NOT 把内部标记当作兴趣词或原样写入身份文案。除该有明确映射的点赞倾向外，客户端 MUST NOT 提供对生成产物零影响的互动偏好输入。

点击生成即由**边缘发起**一条 `persona.generate` WebSocket 请求。请求 MUST 携带握手绑定的 `accountId`（不由请求体自报覆盖）、关键词勾选（含自由文本项与受控点赞倾向标记）、idempotency key，并以 `timeoutMs ≥ 185s` 显式覆盖默认超时。触发 MUST 发生在账号身份已确立之后（`accounts` 行已存在，满足人设落库外键前提）。云端 MUST 对 `keywordSelections` 做轻量输入校验（单项长度上限 + 条数上限），超限诚实拒绝、绝不把超长/超量文本原样喂进生成 prompt（纵深防御：弱注入面在自助模型下影响面仅为该用户自己的人设、且产物经 `loadSoulFromValue` 结构复验）。旧客户端未携带点赞倾向标记时 SHALL 按“正常”生成，保持兼容。

#### Scenario: 握手后触发生成

- **WHEN** 客户在客户端新建环境扫码登录、握手完成后于向导选定关键词与点赞倾向并点击生成
- **THEN** 边缘发出 `persona.generate` 请求（携握手绑定 `accountId`、关键词勾选、受控点赞倾向标记、idempotency key、`timeoutMs ≥ 185s`），云端据此生成

#### Scenario: 默认正常并在预览中可核对

- **WHEN** 客户首次打开人设初始化向导且未主动调整点赞倾向
- **THEN** “正常”档被选中，预览摘要显示“点赞倾向：正常”，生成的人设以 `like_affinity=normal` 持久化

#### Scenario: 点赞倾向标记不污染人设兴趣

- **WHEN** 云端收到 `like_affinity:like_more` 或 `like_affinity:like_most` 受控标记
- **THEN** 生成器在构造身份/兴趣 prompt 前移除该标记，并只把其映射到 `behavior_guidelines`，MUST NOT 把内部 token 写入 identity、interests 或 seed keywords

#### Scenario: 旧客户端无标记保持兼容

- **WHEN** `persona.generate` 请求没有点赞倾向标记
- **THEN** 云端按 `normal` 处理并生成合法人设，MUST NOT 因字段缺失拒绝请求

#### Scenario: 身份未确立不触发

- **WHEN** 环境已建但尚未扫码登录 / 未拿到真实 userid / 未握手
- **THEN** 向导 MUST NOT 发起生成请求（此刻无可落库的 `accountId`），仅可本地暂存关键词与点赞倾向选择

#### Scenario: 超长或超量输入被诚实拒绝

- **WHEN** `keywordSelections` 某项超单项长度上限 / 总条数超上限（含经自由文本注入的超量内容）
- **THEN** 云端诚实拒绝该次生成、MUST NOT 把超长/超量文本原样喂进 prompt，边缘透传失败原因
