## Why

Facebook 群组目前是全局共享目标池，后台排期循环还会直接按全局开关和风控额度尝试加群，无法让不同账号分组只加入各自负责的群，也没有每账号独立开关、时段、上限和最近结果。需要把目标范围与自动加群配置显式拆出来，并纳入统一的账号自动化入口。

## What Changes

- Facebook 群目标仍保留一份全局事实目录，但可同时关联一个或多个现有账号分组；导入和群组管理页支持维护多分组归属。
- Facebook 账号只从其当前账号分组关联的目标中认领新群；未分组、分组无映射或目标已全局占用时 fail-closed，不回退全局池。
- 保留既有“一群全局只归一个账号”的原子锁；分组归属决定候选范围，不表示同一群可被多个账号重复加入。
- 已分配但尚未加入的目标在执行前重新校验账号分组与范围，失配则释放；已确认加入的成员事实不因范围移除而伪装成退群。
- 在“账号自动化”页为 Facebook 增加独立“自动加群”动作：每账号开关（默认关）、动作周历时段、每日上限和最近执行结果。
- 自动加群继续复用现有每分钟内容调度心跳、账号单飞、风险/会话额度和全局 kill switch；有效时窗为账号活跃时段、内容自动时段与加群动作时段的交集，每日准入取账号配置与风控日额度的最小值，每次执行仍须通过剩余会话额度。
- 手动 `/comment --join` 的裸目标选择使用账号分组范围；显式 `/comment --join=<url>` 保持人工作业覆盖能力，不受自动目标范围限制但仍保留既有物理闸与全局唯一归属。

## Capabilities

### New Capabilities

<!-- None. This change composes existing Facebook group, schedule, and panel capabilities. -->

### Modified Capabilities

- `facebook-group-target-catalog`: 群目标增量支持多个账号分组归属及分组过滤。
- `facebook-group-import-workflow`: 单条、CSV 和批量导入可选维护账号分组，缺省不清空既有映射。
- `facebook-group-membership`: 自动候选认领和执行前复核按账号当前分组 fail-closed，同时保持全局唯一群归属。
- `facebook-manual-join-comment`: 裸 `--join` 使用分组目标池，显式 URL 继续作为人工作业覆盖。
- `content-schedule`: Facebook 自动加群成为独立可配置的账号自动化动作，具有专属时段、上限和结果。
- `console-panel-api`: 群组范围、账号自动加群配置和最近执行结果通过权威读模型暴露。
- `console-write-operations`: 群组范围和自动加群配置经一等单写通道校验、写后回真态。

## Impact

- Cloud：新增可回滚的群目标分组映射与 Facebook 加群自动化配置表，扩展目标/成员/审计存储、内容调度器、面板 API 和写校验。
- Console：Facebook 群组页增加多账号分组维护与过滤；账号自动化页增加 Facebook 自动加群配置和最近结果。
- Control：更新上述 OpenSpec 契约；不改变 Edge/protocol，不移除全局 kill switch，也不自动把现有群映射到所有账号分组。
