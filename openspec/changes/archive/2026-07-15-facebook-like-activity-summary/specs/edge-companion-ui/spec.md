## ADDED Requirements

### Requirement: Facebook 已确认点赞记录标识实际被点赞内容

客户端 SHALL 在 Facebook 点赞经后置校验确认成功后，使用点赞执行器从实际被作用帖子读取的见证数据生成活动流摘要；当作者与正文/标题开头可用时，摘要 SHALL 同时展示二者并进行单行空白规范化与有界截断。摘要 MUST NOT 复用上一条阅读记录猜测目标，MUST NOT 展示 permalink 或原始 note ID，也 MUST NOT 改变云端归账或本地点赞计数语义。

#### Scenario: 已确认点赞展示作者与稿件摘要
- **WHEN** Facebook 点赞后置校验成功，且实际被作用帖子的见证包含作者和正文/标题开头
- **THEN** 客户端新增一条同时包含有界作者与正文/标题摘要的“赞”活动记录
- **AND** 该记录贡献且只贡献一次现有本地点赞兜底计数

#### Scenario: 点赞见证字段缺失时诚实降级
- **WHEN** Facebook 点赞确认成功，但见证只包含作者或正文/标题开头，或两者都缺失
- **THEN** 客户端使用可用字段生成部分摘要，或回退为通用“点了个赞”文案
- **AND** 活动记录 MUST NOT 展示 permalink、原始 note ID，也 MUST NOT 从上一条阅读记录补齐缺失字段

#### Scenario: 非成功点赞不生成成功摘要
- **WHEN** Facebook 点赞处于 shadow、失败、已点赞、未找到目标或后置校验未确认状态
- **THEN** 客户端 MUST NOT 生成点赞成功活动记录或本地点赞成功增量
