## Why

现役风控在安全限额之上，又叠了一层**按账号年龄的冷启动养号爬坡**（代码注释标 `account-nurture-discipline-spine`，但该 change 在 openspec 里查无 spec、查无 change 目录——是纯代码默认，无规格约束）。它按 `accounts.created_at` 现算账号「入库天数」，用一条逐日放开的曲线把当日配额压低，`effectiveQuotas() = min(冷启动当日天花板, 风控缩放安全限额)`。

Facebook 曲线比小红书更保守：view 逐日为 `20 → 25 → 35 → 40 → 50 → 60 → 70`，第 7 天封顶 **70**。实测 dev 上唯一在跑量的 FB 号 `61591753702668`（07-08 入库、今日恰为冷启动第 7 天）浏览被压在 70 一线——这正是运营看到的「浏览上限 70」。该机制默认开（`AIDCP_COLDSTART_RAMP != 'false'`），对所有未满 7 天的账号（FB + 小红书）生效。

用户决策（2026-07-15）：**不要这条年龄冷启动爬坡机制**，浏览与互动一律直接走「安全限额配置」（管理后台 `/quotas` 可编辑的三档 × 全动作 × 三窗口，缺值回落 `quotas.ts` 写死默认）。新号从第一天起即按其风控档位的安全配额跑，不再被年龄压低。

## What Changes

- **cloud（核心）**：账号年龄冷启动爬坡由 **opt-out（默认开）改 opt-in（默认关）**。缺省不叠任何冷启动 clamp，`effectiveQuotas()` 直接返回安全限额配置（经配额提供者热加载，缺值回落写死三档）。仅当运维显式设 `AIDCP_COLDSTART_RAMP=true` 时才启用逐日养号爬坡（原机制、曲线、代码全保留，供养号需要时秒回退）。
- **cloud（一致性）**：生产接线默认（`src/server.ts`）与 `RiskController` 类默认（`src/risk/risk-controller.ts`）同步翻为「关」，避免「类说开、服务说关」的口径分裂。
- **不动**：安全限额**数字**不改（仍是 `quotas.ts` 三档 / `quota_config` 表当前值）；`warned` / `restricted` / `frozen` 对安全限额基准的缩放 / 清零语义不变；风控状态单写不变量不变；重启防 burst 的「重启冷启动静默期」（`ActionCooldownGate`，另一套机制、与年龄爬坡无关）保持原样；WebSocket 协议不动。

## Capabilities

### Modified Capabilities

- `interaction-risk-gating`: 新增要求——配额闸默认不做账号年龄冷启动爬坡，`effectiveQuotas()` 直接采用安全限额配置；年龄爬坡降级为 `AIDCP_COLDSTART_RAMP=true` 显式 opt-in，缺省关闭。

## Impact

- **cloud（aidcp-cloud）**
  - `src/server.ts`：`coldStartRampEnabled` 由 `process.env.AIDCP_COLDSTART_RAMP !== 'false'`（默认开）改 `=== 'true'`（默认关）；更新注释与启动日志文案。
  - `src/risk/risk-controller.ts`：`coldStartRampEnabled` 类默认由 `?? true` 改 `?? false`；更新构造注释。
  - `test/risk-cold-start-clamp.test.ts`：验证「启用态」的用例显式传 `coldStartRampEnabled: true`（机制作为 opt-in 保留、仍受测）；新增「默认关：年轻 FB aggressive 号走安全 view 配额、不再被 70 压」用例。
  - 未触碰：`src/risk/cold-start-planner.ts`（曲线数据保留）、`src/risk/quotas.ts`（安全限额数字保留）、`src/risk/risk-state-machine.ts`（状态语义不变）、`src/risk/action-cooldown.ts`（重启静默期无关）。
- **红线**：AC-RISK-* 全过（不自残、被禁 `record` 返 false 不变）；不动协议两份 `protocol.ts`。
- **部署**：dev（用户长期授权）。启动日志应显示「冷启动配额爬坡 已禁用」。
- **真机验收**：FB 号 `61591753702668` 现应可浏览超过 70、直至其档位安全 view 配额 → 归并入真机 backlog。
