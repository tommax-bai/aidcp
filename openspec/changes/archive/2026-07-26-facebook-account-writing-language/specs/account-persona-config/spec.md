## ADDED Requirements

### Requirement: Soul 写作语言可选解析、受控写入并热加载
Soul 类型、YAML loader 与 serializer SHALL 支持可选顶层 `writing_language`，存在时只允许 `zh-CN/en/vi`；缺省时旧人设仍可解析。Facebook 新生成/更新由入口强制存在，非 Facebook 继续缺省。保存成功后运行时 SHALL 从账号热加载 soul 读取，不建立第二份独立语言事实源。

#### Scenario: 旧 soul 无语言仍可加载
- **WHEN** 加载一份只有 identity/interests 的存量 soul
- **THEN** loader 正常返回人设且 `writing_language` 缺省，MUST NOT 因 schema 扩展把账号误判为无人设

#### Scenario: 合法语言 round-trip
- **WHEN** 含 `writing_language: vi` 的 soul 经 serializer 再由 loader 读取
- **THEN** 结果仍为 `vi`，其它 identity/interests/behavior 字段保持不变

#### Scenario: 非法持久化被拒
- **WHEN** 面板或 Edge persist 尝试保存 `writing_language: vietnam`
- **THEN** 现有人设单写通道返回 `persona_invalid` 且不落库、不刷新镜像
