## Why

客户端已经有账号人设生成向导，但当云端因账号未绑定人设而拒绝启动时，客户端没有足够主动地把问题弹到用户面前；同时现有关键词选择结构过粗，无法按用户给的「语气调性 + 内容偏好」样式配置账号口味。浏览器自身的地理位置等授权请求也需要在客户端有明确策略，避免自动化过程中被原生权限弹窗卡住或误授权。

## What Changes

- aidcp-edge Electron 客户端在已登录、已连云且账号未绑定人设时，主动弹出账号人设浮层，并通过系统通知提醒；同一账号/环境只在需要处理时提醒一次，避免刷屏。
- 账号人设浮层改为两个面板：顶部「语气调性」，下方「内容偏好」。内容偏好按截图样式分「垂类/行业」标题与二级兴趣按钮，新增首个品类「招聘求职」及指定二级项。
- 每个内容偏好分组后提供「+」自定义入口，允许为该行业追加自定义兴趣；自定义项参与 `persona.generate` 的关键词输入，继续复用现有云端生成与落库通道。
- Electron 主窗口增加浏览器权限请求处理：地理位置等自动化无关敏感权限默认拒绝并在客户端弹出说明/系统通知；通知权限等低风险权限按既有行为保持可控，所有拒绝都不假装页面正常。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-companion-ui`: Electron 客户端的人设设置提醒、人设关键词面板结构、自定义内容偏好、浏览器权限弹窗处理行为。

## Impact

- 代码：`../aidcp-edge/src/electron/main.cjs`、`../aidcp-edge/src/electron/renderer/index.html`、`../aidcp-edge/src/electron/renderer/renderer.js`、`../aidcp-edge/src/electron/renderer/styles.css` 及 Electron 渲染层测试。
- 协议：不新增边云消息类型，继续使用现有 `persona.generate` / `persona.persist` 与 `keywordSelections`。
- 云端：不改 `persona_config`、判绑闸或 LLM 生成人设结构。
- 部署：edge 客户端本地代码改动；无 ECS 部署。
