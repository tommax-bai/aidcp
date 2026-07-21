## Why

客户端现有浮层已同时承载环境加入、新建、平台修正、代理修改和删除，却仍以“添加环境”命名并用加号作为唯一入口，信息架构比真实能力更窄。运维还需要在同一处简洁地选择多个环境并按既有逐行代理格式重新分配代理，不能把复杂选择和配置继续塞进 176px 的左侧环境栏。

## What Changes

- 将左侧环境栏的“＋ 添加环境”入口改为明确的“环境管理”入口；左栏继续只负责环境切换、状态与运行操作。
- 将浮层标题改为“环境管理”，一级页签收敛为“环境”和“新建环境”；环境页直接列出当前客户可见环境，并只使用“已加入 / 未加入 / 加入 / 移出”等简洁文案。
- 保留刷新、加入、移出、平台修正、逐个二次确认删除和手动分身 ID 兜底；低频操作不常驻占据主视觉。
- 单环境代理编辑增加与 Facebook 批量建号一致的一行代理快速解析，解析后回填现有结构化字段，密码仍不回显。
- 环境页增加按需进入的“批量代理”模式：用户显式勾选关闭中的环境、选择一次代理类型、逐行粘贴代理，并在确认前看到固定目标与轮询映射摘要。
- 批量代理在主进程对目标归属和全部输入先行校验，随后按 AdsPower 限速串行写入；遇到失败停止后续并区分成功、失败、未执行，绝不把配置写入宣称为出口 IP 已验证。
- 不新增批量删除，不自动关闭运行环境，不把代理凭据写入设置或日志。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-fleet-console`: 左栏入口从添加动作升级为环境管理，管理浮层采用简洁的环境/新建两页，并以按需批量模式选择明确环境。
- `adspower-desktop-env-picker`: 环境列表、加入/移出、创建、代理和低频管理动作统一收口在环境管理浮层，保留手填兜底与即时落盘语义。
- `adspower-environment-provisioning`: 单环境代理支持逐行格式快速解析，新增安全的批量轮询分配、串行写入和部分失败回执契约。
- `client-customer-auth`: 单个和批量代理写入都必须绑定当前客户可见环境的明确 ID，鉴权或可见集不可信时失败关闭。

## Impact

- Control repo: OpenSpec deltas for the four modified capabilities.
- `aidcp-edge`: Electron renderer HTML/CSS/JS, proxy parser/normalizer, preload named IPC, main-process AdsPower proxy update orchestration, and focused renderer/main/unit tests.
- No Cloud or Console API change, no database migration, no new dependency, and no Edge installer packaging unless separately requested.
