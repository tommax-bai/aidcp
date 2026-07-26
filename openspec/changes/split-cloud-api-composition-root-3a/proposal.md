## Why

`aidcp-api` 仍不能拥有独立组装根：面板与客户 API 需要读取、修改 automation 属主的运行投影、四类限频配置、Facebook 群运营数据、群路由和告警，但这些依赖尚无完整的跨进程契约。若直接照抄单体组装根，api 要么跨库直连 automation 数据，要么把缺席依赖静默降级成空数据或假成功。

## What Changes

- 为 automation → api 的第一批单向能力建立版本化内部 HTTP 契约、服务端路由、客户端和契约测试：
  - 面板 automation 只读投影；
  - quota / pacing / session / resume 四类限频配置的完整面板外观；
  - Facebook 群目标/分配台账中不依赖 api 花名册回调的方法，以及账号自动化目录所需的 scope/audit 投影；
  - 团队群路由解析与管理；
  - 告警勾销。
- 保持四个限频 facade 归 `aidcp-automation`：automation 继续独占校验、写入、镜像版本推进与写后真态回读；api 只持 `aidcp-kernel` 的 `Panel*Config` 接口并由 HTTP 客户端实现，绝不直写 automation 表。
- 在单体组装根先注册 automation 服务端并在 dev 验证，再发布可由 api 组装根消费的客户端；任一远端写失败原样失败，面板计数/告警/互动读失败不得伪装成零。
- 保持 `group_route` 现有 automation 归属，经窄端口提供 api 与 `publish-card-exit` 所需解析；本 change 不顺手重判表或模块归属。
- 将 `importTargets` / `replaceTargetScopes` 明确留到 4a 与账号花名册端口配对：两者遇到新团队标签时必须先刷新 automation 账号投影，本 change 不删除该刷新语义，也不伪称完整 Facebook 群运营面已经可用。
- 回写批次 3/4 测绘结论，记录限频 facade 的既有定稿已经消除 §10.6 所述岔口。

## Capabilities

### New Capabilities

- `cloud-api-automation-owner-ports`: 规定 api 通过哪些单向内部端口访问 automation 属主能力，以及读写失败、新鲜度、真态回读和单写者边界。

### Modified Capabilities

<!-- None. The existing panel endpoints and DTOs keep their behavior; this change adds the owner transport they will consume when the api composition root lands. -->

## Impact

- 控制仓：本 change 的 proposal/design/spec/tasks，`docs/cloud-composition-root-trisection.md` 进度与裁决记录。
- 事实源 `aidcp-cloud`：`src/transport/`、automation 内部 API 注册、单体组装根接线及相应测试。
- 共享包 `aidcp-transport`：新增传输成员与版本；`aidcp-api`、`aidcp-automation`、`aidcp-content` 按实际消费更新固定 pin。
- 运行时：在事实源交付 automation internal route 与客户端，但保持 monolith 不新增内部监听；真正启动 automation internal API、重写并启动 `aidcp-api` 的 `main()` 属后续批次。后续接线不允许打开 automation 数据库连接。协议 v2、Edge、数据库 schema 与 OL 部署均不在本 change 范围。
