## Why

3a/3b 已交付普通 owner HTTP 端口、受限恢复、审批触发与面板实时事件，但 api/automation
组合根仍把 11 组同步读绑定在另一进程的内存对象或属主存储上。直接包 HTTP 会改变热路径签名，
缺注入或把未装载值压成默认又会静默放行，因此独立组合根仍不能诚实启动。

## What Changes

- 以 `aidcp-cloud@67941e4` 重新固化 11 组 remaining inventory，并把它们裁成：
  automation → api 的运行投影、api → automation 的业务投影，以及无需跨进程镜像的共享静态表/
  本地新鲜度运行时；Edge presence 只含三个纯读，带副作用的 `resumeEdgesForAccount` 明确移交 4a
  的反向 automation command；3a/3b 已交付的异步 authority 与实时事件不重复开口。
- 为跨域投影建立统一的 owner snapshot + 单调 cursor 契约。automation 属主变化经本域
  transactional outbox 发布；api 属主变化优先复用现有 config-mirror bump/outbox，其他低基数
  花名册投影允许以全量 snapshot 作为承重自愈通道。
- 共享 persona/account/environment/config 事实和投影内容继续跨 DEV/OL 共享，并复用现有
  `config_mirror_version`/owner version；只把消费实例的 delivery cursor、readiness、health
  以及 target-specific runtime outbox 按 target 隔离，不为共享业务事实新造 target revision。
- 每个消费进程只同步读取本地已应用快照；启动必须完成所需镜像的首次装载并通过 ready gate。
  cursor 不连续、target 不匹配、来源不可达或超出新鲜度上限时保留最后好值并显式返回
  stale/unknown，安全闸 fail-closed，MUST NOT 用空数组、false、未绑定或代码默认伪造成功。
- 相同 cursor 的 owner 新鲜 fetch 若 payload 未漂移且 `asOf` 前进，允许只续本地 freshness；
  历史 envelope 重放不得续鲜，避免“配置长期不变即永久 stale”或“重放旧包伪造健康”。
- 分别保留参数镜像与安全闸镜像的既有语义：参数陈旧可继续使用最后好值但必须可观测；
  presence、环境出口闸、人设绑定等安全/身份事实从未装载或陈旧时拒绝相应动作。
- 将编译期排期自动化目录提为共享 kernel 数据，将镜像新鲜度判定实现改为每进程本地运行时；
  captcha 可用性改为带 `asOf`/ready 的启动投影，配置镜像健康按实际消费进程分域汇总。
- 为快照替换、cursor 重放、断链积压恢复、target 隔离、陈旧边界、进程重启与 unknown/fail-closed
  语义增加契约和组合根验收；单体 DEV 只证明零回归，独立 api/automation 双进程才证明 4b 生效。

## Capabilities

### New Capabilities

- `cloud-api-automation-sync-read-mirrors`: 规定 api/automation 跨进程同步读的 inventory、
  owner snapshot/outbox/cursor、本地镜像、新鲜度、ready 与失败语义。

### Modified Capabilities

- `console-panel-api`: 总览 presence、发布 lifecycle 和分域镜像健康在远端证据未知/陈旧时返回
  可识别 unavailable，而不是零、未下发或全局 fresh。
- `admin-publish-queue-page`: 管理后台在 dispatcher in-flight 证据不可用时显示证据暂不可用，
  不把稿件分类成等待人工或正在下发。
- `client-publish-queue`: 客户端发布四阶段在 Cloud 明确报告下发证据不可用时保持未知，
  不推断“等待发布”或“正在发布”。

## Impact

- `aidcp-cloud`: 事实源、owner snapshot/outbox、消费镜像、组合根接线、迁移与 acceptance 事实源。
- `aidcp-kernel`: snapshot/cursor/ready/unknown 的纯类型与共享静态目录。
- `aidcp-transport`: internal HTTP snapshot/cursor 传输、outbox delivery 与轮询/重放客户端。
- `aidcp-api`: automation 事实的本地读镜像及 api 组合根 ready gate。
- `aidcp-automation`: api 事实的本地投影、automation 组合根 ready gate 与热路径 fail-closed。
- `aidcp-console`: 总览 presence、发布队列和分域镜像健康的 unavailable 展示。
- `aidcp-edge`: 客户发布队列对下发证据 unavailable 的加性兼容；只做源码验证，不制作 installer。
- `aidcp` control：派生清单、跨仓 pin/边界校验、DEV 单体与独立双进程分层验收记录。
