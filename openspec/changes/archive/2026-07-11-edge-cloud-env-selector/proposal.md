## Why

边缘客户端连哪个云端（dev / ol）目前**只能靠启动时的环境变量 `AIDCP_CLOUD_URL` 决定**，界面里没有任何入口能改：核心进程在启动时读一次该变量（`aidcp-edge/src/main.ts:113`，缺省回落 dev），外壳派生每个核心时整份继承进程环境把它带下去（`src/electron/main.cjs:1086-1090` → `fleet.buildEnvSpawnEnv`）。运营人员（用打包版、不设环境变量）因此无法自助切换 dev/ol，且界面顶部只显示「连没连上云」、看不出「连的是哪个云」，存在把线上生产（ol）误当测试（dev）操作的风险。

## What Changes

- 设置抽屉新增「云端环境」选择项：dev / ol / 自定义地址三选一，持久化到 `settings.json`。
- 云端地址解析改为**界面选择优先**：界面选了就以界面为权威（派生核心时显式覆盖继承来的 `AIDCP_CLOUD_URL`）；界面留空则回落启动环境变量、再回落缺省 dev —— **对现有以环境变量启动的 dev 流程零回归**。
- 沿用现成「保存只持久化、不打断在跑核心；显式重启才生效」范式（`main.cjs:2073` / `edge:restart`）：切换云端后提示需重启，并提供「全部重启并连接新云端」一键入口。
- 界面常驻显示「当前云端」（dev / ol(线上) / 自定义），ol 醒目标注；切 ol 需二次确认。**红线：显示的云端必须等于核心实际连接的云端**，「已切未重启」阶段显示为「待重启生效」，绝不显示成已生效。
- 两个正式云端地址（dev=`ws://121.89.85.150:8787`、ol=`ws://123.56.253.183:8787`）收敛到 edge 内**一处映射表**，取代散落的硬编码缺省。

非目标（YAGNI）：不改协议 / 云端 / 单实例锁；不做跨实例分身租约；**不做同一 GUI 内一部分分身连 dev、一部分连 ol 的按分身混连**（并行 dev+ol 同时跑仍走「两个 GUI + 各自独立数据目录」的既有 change `edge-multi-instance-isolation`，本 change 是其补充、省去手敲环境变量）。

## Capabilities

### New Capabilities
- `edge-cloud-env-selection`: 边缘客户端在设置中选择所连云端环境（dev/ol/自定义）、以界面选择为权威解析云端地址、显式重启生效、当前云端常驻可见且与实际连接一致、ol 二次确认。

### Modified Capabilities
<!-- 无：不改动任何现有 spec 的既定 requirement（现有 edge-companion-ui 是界面骨架，本 change 只在设置抽屉内追加一张独立卡；deployment-environments 是云侧/ECS 拓扑，不动）。 -->

## Impact

- **仅 edge（`../aidcp-edge`）**，无云端、无 ECS 部署。
- `src/main.ts`：云端地址缺省解析（提为一处映射常量）。
- `src/electron/main.cjs`：`DEFAULT_SETTINGS` 增字段；spawn 处按界面选择解析并显式钉 `AIDCP_CLOUD_URL`（adspower + self 两路）；设置 IPC 回带当前云端、保存后提示重启。
- `src/electron/renderer/`（`index.html` / `renderer.js` / `ui-logic.js` / `styles.css`）：云端环境卡 + 顶部「当前云端」徽标 + ol 确认。
- 测试：源码契约测试（沿用 `test/electron/instance-userdata-isolation.test.ts` 套路）断言解析优先级、覆盖时机、映射地址正确、留空零注入。
- 与既有 `edge-multi-instance-isolation` 正交互补：两 GUI 各自独立 `settings.json`，各自的云端选择互不影响。
