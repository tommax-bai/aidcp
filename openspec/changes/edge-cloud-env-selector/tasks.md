# Tasks — edge-cloud-env-selector

> 仅 edge（`../aidcp-edge`，分支 master）。无云端、无 ECS 部署。实装后按 sub-repo 分节回写 sha。

## 1. aidcp-edge — 配置与地址解析（主进程）

- [ ] 1.1 在 edge 内建一处云端地址映射常量（dev=`ws://121.89.85.150:8787`、ol=`ws://123.56.253.183:8787`），并让 `src/main.ts:113` 缺省解析复用该表（一处真源，不改缺省行为）
- [ ] 1.2 `src/electron/main.cjs` `DEFAULT_SETTINGS` 增 `cloudEnvKey`（`''|dev|ol|custom`，默认 `''`）+ `cloudUrlCustom`（默认 `''`）；`loadSettings`/`saveSettings` 归一化（非法 key 归 `''`；custom 非 `ws(s)://` 拒绝并回错）
- [ ] 1.3 加一处解析器 `resolveCloudUrl()`：`cloudEnvKey` 非空→映射/custom URL；为空→`process.env.AIDCP_CLOUD_URL || 缺省dev`（返回 `{ url, key, fromSelection:boolean }`）
- [ ] 1.4 派生核心处（`src/electron/main.cjs:1083-1117`）：当 `fromSelection` 为真时，在最终 `spawnEnv` 上**显式钉** `AIDCP_CLOUD_URL`（覆盖继承值）；adspower 与 self 两路都钉；为空则不注入（零回归）

## 2. aidcp-edge — IPC 与生效流程

- [ ] 2.1 `settings:get` 回带 `cloudEnvKey` / 解析出的当前地址 / 友好名；`settings:save` 接受云端选择并持久化，保存后**不打断**在跑核心，回带「需重启才生效」提示
- [ ] 2.2 加一键「全部重启并连接新云端」入口（复用 `fleet:stopAll` + `startAll` 语义），有序全环境重启、避免裂脑
- [ ] 2.3 每环境状态里带出「实际连接的云端」与「目标云端/待重启生效」区分，供渲染层常驻显示（红线：显示=实际连接，不显示成已切换）

## 3. aidcp-edge — 渲染层界面

- [ ] 3.1 设置抽屉 `renderer/index.html:455` 顶部加「云端环境」卡：dev/ol/自定义 分段选择 + custom 地址输入框；复用 `settings-msg` 与 `apply-restart`
- [ ] 3.2 顶部「云端连接」徽标旁加「当前云端」常驻显示（dev / ol(线上) / 自定义），ol 醒目色；「待重启生效」态如实呈现
- [ ] 3.3 切到 ol 弹二次确认（连接线上生产云端）；取消保持原选择
- [ ] 3.4 `renderer.js` / `ui-logic.js` 接线：读写云端选择、显示当前云端、触发「全部重启换云」；`styles.css` 样式

## 4. aidcp-edge — 测试与验证

- [ ] 4.1 源码契约测试（沿用 `test/electron/instance-userdata-isolation.test.ts` 套路）：断言 ① 界面选了在合并之后显式覆盖 `AIDCP_CLOUD_URL`、② 留空则零注入、③ 映射两地址正确、④ custom 非法输入被拒
- [ ] 4.2 `npm test` 全绿 + `npm run typecheck` 干净 + `npm run test:acceptance`（协议红线不受影响，本 change 不动协议）
- [ ] 4.3 回写本 tasks.md 各任务 sha；登记真机验收 backlog（切 dev/ol/custom、重启生效、当前云端显示一致、ol 确认、并行两 GUI 各自选择独立）

## 5. 收口

- [ ] 5.1 `openspec validate edge-cloud-env-selector --strict` 通过
- [ ] 5.2 提交 + 推送 edge master；控制仓回写进度；部署 dev（edge-only 无 ECS，随安装包分发，标注无部署步骤）
- [ ] 5.3 全部完成 → archive
