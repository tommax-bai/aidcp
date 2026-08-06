## Why

词汇蓝图批 2（`docs/edge-command-grammar.md` §6.2/§6.3）。七条非页面命令（读身份 ×2、验证码协助 ×2、租约 ×2、会话收尾）今天全登记为 `page_automation` / `page_account`——分类被「都需要浏览器」污染。类别错了，身份闸按类别一拦全拦，只好手工挖六个洞（`IDENTITY_RESCUE_OPERATIONS` 救援清单）。**救援清单的存在本身就是分类错误的补丁**（判例四）。本批根治：类别按「在编址什么」重归，补丁摘除。

同批落**平台段校验闸**基础设施（语法规格「平台能力命令 MUST 以平台为顶层命名空间」的出入闸半边）：命令名首段 ∈ 平台枚举时必须与账号平台一致。当前词汇尚无平台段命令，闸落地即休眠，批 4/5 改名后自动生效——先有闸再有名，防止批 4 落名时无闸可校。

## What Changes

- **说明书类别词汇扩容**（edge + automation 两份逐字一致）：新增 `page_observation`（需浏览器、读页面、不代表账号动作；身份维 `local_environment`）与 `environment_assist`（环境处置）。
- **七条改类**：`identity.read_current` / `identity.read_self_profile` → `page_observation`；`captcha.assist.capture` / `.click` → `environment_assist`；`edge.task.release` / `session.end` → 编排收尾（identity 降为非 `page_account`）。**`edge.task.acquire` 保持 `page_account`**——认领租约＝即将以该账号名义动作，属准入，身份未落定时 MUST 仍被拦（决策见 design）。
- **摘救援补丁**：身份闸的六洞清单删除——改类后被拦集合自然收敛为「真页面动作 + acquire」，清单失去存在理由。行为对照表逐条验证（哪些命令在身份未落定时的处置前后不变 / 有意变化）。
- **平台段校验闸**：出口（automation 下发前）与入口（edge 收到时）各一道——名字首段 ∈ 平台枚举 ⇒ 必须等于账号所属平台，不符拒绝并如实回执；无平台段命令按原逻辑放行。当前休眠，带变异测试证明它醒着。
- **BREAKING（行为变更）**：身份未落定时 `edge.task.release` / `session.end` / 读身份 / 验证码协助的放行不再依赖手抄清单（结果不变、机制变）；无其他命令的拦放变化。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `client-core-browser-executor-separation`: 分类词汇从六类扩为八类，类别判据显式绑定「在编址什么」（语法规格 R6 的实装）；身份闸判据从「类别 + 救援清单例外」收敛为「身份维 + 零例外清单」。

## Impact

- `aidcp-edge`：`src/client/operation-registry.ts`（类别类型 + 7 条改类）、`src/client/identity-command-gate.ts`（删救援清单 + 判据收敛）、`src/client/edge-client.ts`（入口平台段闸）、相关测试（含 close-account 刚加的救援清单断言——清单删除后该断言对象消失，测试随之改写为「被拦集合 = 身份维推导」）。
- `aidcp-automation`：`src/comm/operation-registry.ts`（同扩容同改类）、出口平台段闸（`src/comm/ws-server.ts` 出口路径）、测试。
- 不动 `protocol.ts`（类别是登记表侧）；与批 3（动协议）并行安全。
- 部署 dev；边缘行为变更**不出包也不回退安全**（旧客户端仍带救援清单逻辑，两套判据对七条的放行结果一致——对照表见 design）。
