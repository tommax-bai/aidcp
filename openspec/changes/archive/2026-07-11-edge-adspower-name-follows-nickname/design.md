## Context

客户端左栏环境名从「账号昵称」退化为「模板名」，根因已 root-cause（trace + 三路对抗验证）：

- 左栏取名优先级 `railDisplayName`（`aidcp-edge/src/electron/renderer/renderer.js:1198-1199`）= `row.name || status.account.name || 环境 …末4位`。
- 真实登录昵称落在第二档 `status.account.name`（`main.cjs:1852-1855` 写入，带 `source` 标记：`'xhs'`=平台真实昵称、`'env'`=环境名兜底；昵称来自 `self-identity.ts:170` 读 `.user-name` / Facebook `identity.ts` 读头像 `aria-label`）。
- 客户端自建 profile 的 AdsPower 名一直是设备模板 key（`ads-create-flow.cjs:101` 的 `name: name || templateKey`）。
- **回归点**：`edge-env-name-live-sync`（edge master `1d2620a`）新增 `reconcileRosterNames`（`renderer.js:1913-1930`），每次完整 `user/list` 拉取后把花名册名回填成 AdsPower live 名（=模板名）。回填后 `row.name` 恒为非空模板名 → 短路遮蔽第二档昵称。回归前 `row.name` 为空、才落到昵称档。
- 客户端原本**物理上改不了** profile 名：写客户端 allowlist（`ads-write-api.cjs:23`）里 `user/update` 仅经 `updateProfileProxy` 两键封装限改代理。

约束：纯 edge-only（无 cloud、无 ECS）；不碰浏览器生命周期写面（核心子进程单写）；昵称仅作显示名、非账号主键（`account-identity-resolution`）；写客户端 ≥1s 串行限速；「绝不静默假成功」红线。

## Goals / Non-Goals

**Goals:**
- 运维在左栏按真实账号昵称一眼辨识每个环境。
- 让 AdsPower 环境名本身也等于昵称（单一真源）：左栏、添加面板、乃至直接打开指纹浏览器客户端三处一致。
- 存量环境随正常运营渐进改到位，零额外数据源、零云端依赖。
- 空窗期（建好未改名）与改名写失败时，左栏仍显示昵称、绝不回退模板名。

**Non-Goals:**
- 即时一次性批量改名（用户已定案不做本次）。
- 云端侧 profile→昵称导出 / 任何 cloud 改动。
- 打开写客户端整张写面：仍只窄放行改名一个新用途。
- 触碰浏览器生命周期写面。

## Decisions

### D1：改名走写客户端新增 `renameProfile` 两键封装，而非放宽 allowlist 数组
`user/update` **已在** allowlist 内（`ads-write-api.cjs:23`），「仅限改代理」是靠「只有一个两键封装」这一结构性约束+回归断言保证的。故新增一个只构造 `{ user_id, name }` 的 `renameProfile({ userId, name })` 封装即可，不改 allowlist 数组。同步把那条「update 仅两键代理 body」的回归断言更新为「改代理两键 **或** 改名两键」，并分别锁住两个封装的 body 键集。
- 备选：直接放宽 `updateProfileProxy` 接受 name → 否决，会让一个封装身兼两职、破坏「一封装一用途」的可断言性。

### D2：改名触发点在主进程身份事件处理，按需、幂等、限速
在 `main.cjs` 收到核心「账号身份已确立」事件（`evt.account`，`main.cjs:1852-1855` 现有分支）且 `source` 表明是真实平台昵称时，比较该环境当前 AdsPower 名与昵称：不一致才经 `renameProfile` 改名，一致直接跳过（幂等去抖）。改名复用写客户端已有的 ≥1s 串行节流单链，天然不与核心本地 API 同秒并发。
- 当前 AdsPower 名的取值来源：优先用手头花名册/handle 名（`handle.name`），必要时以下次 `user/list` 读回校正。去抖以「昵称 == 当前已知名」为判据，避免每次身份事件都发写。
- 备选：渲染层触发 → 否决，写客户端在主进程、渲染层不持 API key。

### D3：改名失败诚实降级，绝不阻塞浏览
`renameProfile` 返回 `{ ok:false }`（不可达 / `code≠0` / 撞限速）时：保持原名、记一次可观测日志、**不**重试风暴、**不**阻塞该环境浏览闭环；下次该环境再产生身份事件时自然再试。绝不把改名失败伪装成成功、绝不因改名而中断会话。

### D4：建号不再下发模板名，交 AdsPower 默认
`ads-create-flow.cjs` 的 `createProfile` 调用不再传 `name: templateKey`（`if (name)` 才下发，见 `ads-write-api.cjs:145`），标准建号路径 name 缺省 → AdsPower 默认命名。FB 批量导入路径保留其显式 name（`profileNameForFacebookImport`）不动。建号回执 `name` 字段相应改为「实际写入的名字或空」，入册花名册允许空名（回归前行为），空名交由 D5 的显示兜底。
- 真机确认项：建号不传 name 时 AdsPower 自动给什么名（tom 分组测号）。

### D5：显示层优先真实昵称，作为改名的兜底保险
`railDisplayName`（`renderer.js:1199`）优先级改为：真实昵称（`status.account` 且 `source` 表明为平台真实昵称）→ 花名册/环境名 → 「环境 …末4位」。这层独立于 AdsPower 是否已改名：即使改名尚未完成或写失败，左栏也已显示昵称。为可测，优先把该优先级逻辑下沉进纯函数 `fleetRailModel`（`renderer/ui-logic.js:336-349`，已接收 status）。
- 与 D2 互补：D2 让真源一致，D5 保证观感即时且不因写失败回退。

## Risks / Trade-offs

- **[改名与实时名回填打架]** 改名成功后 `user/list` 名变昵称，`reconcileRosterNames` 会把花名册名同步成昵称——方向一致、无冲突。空窗/失败期靠 D5 兜底，`row.name` 即使被回填成模板名也不遮蔽昵称。→ Mitigation：D5 显示优先级 + 回归用例覆盖「回填模板名不遮蔽已知昵称」。
- **[AdsPower `user/update` 是否支持改 name 未在代码内可证]** 属外部 API 假设。→ Mitigation：真机（tom 分组）确认 `user/update` 带 name 生效 + 建号空 name 的默认命名形态，列入真机验收 backlog；失败路径已由 D3 诚实降级兜住（不生效则退回原名，不自残）。
- **[写限速被改名占用]** 每环境登录期多一次潜在写。→ Mitigation：幂等去抖使稳态下几乎零写（名已一致即不发）；复用 ≥1s 串行节流不与核心并发。
- **[并行热点]** `ads-create-flow.cjs` / `main.cjs` 与活跃 change `self-contained-ads-runtime` 重叠。→ Mitigation：实装前 rebase 到最新 master；命名/改名两处为本 change 单写，避免与对方同段并行。
- **[FB vs XHS 昵称时序差异]** FB 头像 `aria-label` 即时可得；XHS 昵称须走 navigate 身份路径（`source='xhs'`）读到才有。→ Mitigation：两平台共用同一「有真实昵称即改名/显示」判据，时序差异只影响「多久解遮蔽」，不影响正确性。

## Migration Plan

- 纯 edge-only 前向变更，无数据迁移、无协议改动、无 cloud/ECS 部署。
- 上线即对新建环境生效；存量环境随各自下次登录渐进改名，无需一次性操作。
- 回滚：还原四处代码即可（改名封装、建号命名、身份触发、显示优先级）；已被改名的存量环境名保持为昵称、无副作用。

## Open Questions

- AdsPower `user/update` 改 name 的确切字段名与生效时机（真机确认；保守假设字段为 `name`）。
- 建号不传 name 时 AdsPower 默认命名形态（真机确认；无论何形态，D5 显示兜底 + D2 改名都会覆盖）。
