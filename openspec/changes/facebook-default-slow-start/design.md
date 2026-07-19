## Context

Edge 的 Facebook 单建与批量建最终都调用 `POST /environment-provisioning/complete`，Cloud 再在一个事务中插入 `client_environments`、写唯一客户归属并完成 intent。当前请求只含 intent、envKey、label 与 platform；插入也不带 `slow_start_since`，所以新环境默认关闭慢启动。

慢启动事实已经是环境级字段，允许账号尚未绑定时预设。现有 `PUT /environments/:envKey/slow-start` 可以在创建后补写，但会把一个逻辑创建拆成两个 Cloud 事务，产生“归属已成功、慢启动补写失败”的半成功窗口。

## Goals / Non-Goals

**Goals:**

- 所有经官方程序化创建链路新建的 Facebook 环境，从创建完成起默认开启慢启动。
- 单建和批量走同一平台判定，不靠 renderer 文案或模式推断。
- Cloud 原子确认归属与慢启动，使用服务端上海日界并保持 intent 幂等。
- 小红书和视频号请求、数据与 UI 行为保持没有慢启动概念。

**Non-Goals:**

- 不改变存量环境的慢启动状态，不批量回填历史 Facebook 环境。
- 不改变慢启动 7 天曲线、风控档位、动作节奏或账号风险状态。
- 不新增数据库列，不把慢启动写入 Ads CLI / SunBrowser profile、remark 或账号导入凭据。
- 不为本变更打包 Edge 安装器。

## Decisions

### 1. 由平台决定默认值，创建模式不参与

Edge 在主进程归一出 `platform` 后计算 `slowStartEnabled = platform === 'facebook'`。单个创建的无账号导入分支、单账号导入分支和批量分支都把同一个值交给归属完成函数。renderer 不提交该布尔值，因此绕过 UI 也不能把非 Facebook 冒充成慢启动创建。

### 2. 慢启动与权威归属在同一 Cloud 事务中完成

`environment-provisioning/complete` 接受可选 `slowStartEnabled`。省略保持旧客户端行为；`true` 只允许 `platform=facebook`。Store 在首次插入 `client_environments` 时同时写入 `slow_start_since = shanghaiDayStartMs(serverNow)` 和 `slow_start_initialized=true`，再写归属并完成 intent。任一步失败全部回滚。

不采用创建后补调 PUT：额外请求不能与注册原子提交，也会让部分失败回执难以判断环境是否真正处于慢启动。

### 3. intent 重试只读既成结果，不重放默认值

首次完成后，重试同一 intent 继续走既有 idempotent 分支，只读取已存在归属，不再次更新 `slow_start_since`。因此网络丢包重试不会把起点推进到下一天；若运营已通过既有开关关闭，陈旧完成请求也不会重新开启。

### 4. 回执只表达已确认事实

Cloud 完成成功后 Edge 才把 `slowStartConfigured=true` 放入安全环境摘要。Cloud 归属未确认、旧 Cloud 拒绝新字段或 customer-auth 不可用时，不声明慢启动成功，并沿用现有“不自动删除本地已建环境”的诚实部分成功语义。

## Migration Plan

1. Cloud 先兼容可选字段并原子落库，旧 Edge 请求保持原行为。
2. Edge 再开始为 Facebook 创建发送 `slowStartEnabled:true`。
3. 部署 Cloud dev 后验证接口与数据库状态；Edge 源码合入但不在未明确要求时构建安装器。

回滚 Edge 即停止发送新字段；回滚 Cloud 前应先回滚 Edge，避免严格请求校验拒绝新请求。已创建环境的慢启动设置作为真实用户配置保留，不自动清空。

