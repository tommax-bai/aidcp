## ADDED Requirements

### Requirement: Facebook feed 点赞资格以「已选中 + 已走到点赞判定」为据，不硬闸同级订阅者写的「已放行」集合

云端对 Facebook feed 自然互动（点赞）的资格判定 MUST NOT 硬闸一个由 `quality.pass` 的**同级订阅者**填充的「已放行」集合。理由：点赞判定角色由 `reading.done` 触发，而 `reading.done` 只可能在内容质量筛选放行（`quality.pass`）驱动深读→评论链走通后才发出——**能走到点赞判定本身即证明该帖已被质量筛选放行**。资格 SHALL 以「该帖已被选中」（`content_selected`）为闸；「已放行」集合 MAY 继续维护并写入诊断日志（作观测），但 MUST NOT 作为拦截点赞的硬条件。

此不变量是为消除 `EventBus` 同步 emit 下的**顺序竞态**：`quality.pass` 的多个同级订阅者中，深读角色先注册先跑、并在其自身处理器内**同步**一路驱动到点赞判定；若点赞闸依赖另一个同级订阅者稍后才写入的集合，检查时集合恒空 → 系统性误判「未通过质量筛选」、挡掉全部点赞。边缘用于关联的 noteId SHALL 归一到**规范帖身份**（帖数字 id），使「已选中」与「点赞判定」两处 key 在不同上报形态（feed 卡 vs 详情）下必然一致，MUST NOT 因形态差异误判不匹配。

#### Scenario: 已选中且走到点赞判定即放行、不被空集合误挡
- **WHEN** 某 Facebook feed 帖已被选中、且深读链驱动到点赞判定角色
- **THEN** 云端 MUST 放行点赞资格判定（进入 LLM 点赞决策），MUST NOT 因「已放行」集合此刻为空而回报「未通过质量筛选」拦截

#### Scenario: noteId 形态不同仍正确关联
- **WHEN** 「已选中」记录的 noteId 来自 feed 卡上报、而点赞判定处的 noteId 来自详情上报（同一帖、形态不同）
- **THEN** 云端按规范帖身份归一后判定两者为同一帖，资格关联成立，MUST NOT 因形态差异判不匹配而误挡
