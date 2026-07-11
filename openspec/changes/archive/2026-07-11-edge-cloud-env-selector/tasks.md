# Tasks — edge-cloud-env-selector

> 仅 edge（`../aidcp-edge`，分支 master）。无云端、无 ECS 部署。全部实装于 edge master `4e69690`（单提交）。

## 1. aidcp-edge — 配置与地址解析（主进程）

- [x] 1.1 在 edge 内建一处云端地址映射常量（dev/ol） <!-- aidcp-edge 4e69690 main.cjs 加 CLOUD_ENV_URLS/DEFAULT_CLOUD_URL/CLOUD_ENV_LABELS。偏离：main.ts:113 的核心缺省字面量未改为消费该表（外壳/核心是两个模块，跨界耦合无收益）——核心缺省与 DEFAULT_CLOUD_URL 同值（dev），仅当外壳零注入且无环境变量时命中，行为一致 -->
- [x] 1.2 `DEFAULT_SETTINGS` 增 `cloudEnvKey`（`''|dev|ol|custom`，默认 `''`）+ `cloudUrlCustom`；`normalizeCloudSettings` 归一化（非法 key 归 ''；custom 非 `ws(s)://` 降级为未选择、不注入垃圾） <!-- aidcp-edge 4e69690。custom 非法在渲染层显式回错，主进程侧降级为安全网 -->
- [x] 1.3 加 `resolveCloudUrl()`：选择优先 > 环境变量 > 缺省 dev，返回 `{ url, key, fromSelection }`；`cloudSelectionView()` 供界面显示目标云端 <!-- aidcp-edge 4e69690 -->
- [x] 1.4 派生核心处（`startEdge`）：`fromSelection` 为真时在最终 `spawnEnv` 上**合并之后**显式钉 `AIDCP_CLOUD_URL`（adspower + self 两路共用一处注入）；为空则不注入（零回归）；stamp `handle.connectedCloudKey` <!-- aidcp-edge 4e69690 -->

## 2. aidcp-edge — IPC 与生效流程

- [x] 2.1 `settings:get` 回带 `cloudEnv`（目标云端视图）；`settings:save` 持久化云端选择、**不打断**在跑核心、broadcastFleet 让界面即时刷新 <!-- aidcp-edge 4e69690 -->
- [x] 2.2 新增 `cloud:restartAll` IPC：有序重启全部在跑/退避中环境按新选择重连，避免裂脑 <!-- aidcp-edge 4e69690 preload 暴露 cloudRestartAll -->
- [x] 2.3 状态里带出 `connectedCloudKey`（本次实际连接的云端），供渲染层与目标云端比对显示「待重启生效」（红线：显示=实际连接） <!-- aidcp-edge 4e69690 makeStatus 加字段、startEdge 启动时写入 -->

## 3. aidcp-edge — 渲染层界面

- [x] 3.1 设置抽屉顶部「云端环境」卡：dev/ol/自定义 分段 + custom 地址输入框（复用 seg 样式与 settings-msg） <!-- aidcp-edge 4e69690 index.html + renderer.js -->
- [x] 3.2 标题带常驻「当前云端」chip（运行中显示 live、否则目标；待重启加后缀 + pending 态；ol 醒目色）；抽屉内「当前连接」如实呈现 <!-- aidcp-edge 4e69690 updateCloudPending -->
- [x] 3.3 切到 ol 弹二次确认（连接线上生产云端）；取消保持原选择 <!-- aidcp-edge 4e69690 selectCloudEnv -->
- [x] 3.4 `renderer.js` 接线（选择/自定义落盘/全部重启换云/chip 点击开抽屉）；`styles.css` chip + 卡样式 <!-- aidcp-edge 4e69690 -->

## 4. aidcp-edge — 测试与验证

- [x] 4.1 源码契约测试 `test/electron/cloud-env-selector.test.ts`（7 断言）：映射两地址、受 fromSelection 守卫的覆盖、**覆盖在合并之后**、留空零注入、custom 非法降级、snapshot 带 cloudEnv、restart-all IPC <!-- aidcp-edge 4e69690 -->
- [x] 4.2 `npm test` 980/0 + `npm run typecheck` 干净 + `npm run test:acceptance` 16/0（协议红线不受影响，本 change 不动协议） <!-- aidcp-edge 4e69690 -->
- [x] 4.3 登记真机验收 backlog（簇 50：切 dev/ol/custom、重启生效、当前云端显示一致、ol 确认、并行两 GUI 各自选择独立） <!-- 控制仓 backlog 簇 50 -->

## 5. 收口

- [x] 5.1 `openspec validate edge-cloud-env-selector --strict` 通过 <!-- propose 时已过 -->
- [x] 5.2 提交 + 推送 edge master（`4e69690`）；主 checkout 已 ff 同步；edge-only 无 ECS 部署（随安装包分发，运营机 pull master + 重建后生效） <!-- aidcp-edge 4e69690 -->
- [x] 5.3 全部完成 → archive <!-- 本次 archive -->
