## Why

客户端左栏的环境名从「账号昵称」退化成了「模板名」（如 `win11-intel`）。根因已定位：`edge-env-name-live-sync`（edge master 1d2620a）新增的实时名回填把每个环境的显示名刷成 AdsPower `user/list` 的 live 名，而客户端自建 profile 的 AdsPower 名一直就是模板 key；左栏取名优先级里这个非空的模板名遮蔽了本应显示的真实登录昵称。运维需要按昵称一眼认出每个环境，模板名对运维无意义，必须恢复「名即昵称」。

## What Changes

- **建号不再把模板名写进 AdsPower 环境名**：创建时不再下发 `name=templateKey`，交给 AdsPower 默认命名，空窗期左栏靠显示兜底显示昵称。
- **环境名渐进跟随真实昵称**：每个环境登录、核心读出真实平台昵称后，若 AdsPower 环境名与昵称不一致，桌面外壳经写客户端把该环境改名为昵称。存量环境随正常运营下次运行时自动改到位（**不做即时一次性批量、不引入云端依赖**）。改名幂等去抖（已一致不重复写）、遵守写客户端 ≥1s 串行限速、写失败诚实降级（保持旧名、绝不阻塞浏览、绝不假成功）。
- **写客户端 allowlist 窄放宽**：`user/update` 的放行从「仅限改代理」放宽为「改代理**或**改名」，新增一个只构造 `{ user_id, name }` 两键 body 的改名封装，fingerprint / remark / 分组等一概仍不经此口；回归断言从「仅两键代理 body」相应更新为「改代理两键 **或** 改名两键」。**BREAKING**（结构性红线 M7 的受控放宽，非行为破坏）。
- **左栏显示名优先真实昵称**：环境行显示名在已读到真实登录昵称时优先用昵称，兜住「刚建好未改名」空窗与改名写失败的情况，已知真实昵称时绝不回退模板名。

## Capabilities

### New Capabilities

（无。全部为对既有能力的要求修改。）

### Modified Capabilities

- `adspower-environment-provisioning`：① 创建时环境名不再写死模板名；② 写客户端 `user/update` allowlist 放行从「仅改代理」放宽为「改代理或改名」（新增 name-only 两键封装 + 更新回归断言）；③ 新增「环境名渐进跟随真实账号昵称」要求（登录读出昵称后改名、幂等去抖、限速、诚实降级、edge 本地触发不依赖云端）。
- `edge-fleet-console`：新增「左栏环境显示名优先真实登录昵称」要求（已知真实昵称时优先昵称、未知时优雅回落，绝不因实时名回填而回退模板名）。

## Impact

- **仓**：仅 `aidcp-edge`（edge-only，无 cloud、无 ECS 部署）。
- **代码**：
  - `src/electron/ads-write-api.cjs`：新增 `renameProfile({ userId, name })` 封装 + 更新 allowlist 两键约束回归断言。
  - `src/electron/ads-create-flow.cjs`：创建不再下发 `name=templateKey`（约 line 101、以及回执 name 字段）。
  - `src/electron/main.cjs`：身份事件处理处（约 line 1852-1855）新增「读到真实昵称→按需改名」触发；建号回执与花名册入册相应调整。
  - `src/electron/renderer/renderer.js`：`railDisplayName`（约 line 1198-1199）显示优先级调整；可选下沉到 `src/electron/renderer/ui-logic.js` 的 `fleetRailModel` 便于单测。
- **外部 API 假设（真机确认，列入真机验收 backlog）**：AdsPower `user/update` 支持改 `name`；建号不传 name 时 AdsPower 自动分配的名字形态（用 tom 分组测号确认）。
- **并行热点**：`ads-create-flow.cjs` / `main.cjs` 与活跃 change `self-contained-ads-runtime` 有热点重叠，实装时 rebase 到最新 master 协调，改名/命名两处为本 change 单写。
- **不改**：浏览器生命周期写面（`browser/start|stop|active` 仍核心子进程单写、写客户端仍直接抛错）；账号身份主键（昵称仍仅作显示名，不作主键，遵 `account-identity-resolution`）。
