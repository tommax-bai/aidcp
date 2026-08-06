## Why

「云端能对边缘下哪些命令、每条命令代表谁」这份知识，今天在边缘**同时存在四份**：一份集中式操作登记表（唯一被闸消费的那份）、`edge-client.ts` 里一长串 `env.type === '…'` 的路由分支、测试里一份 46 条的手抄清单 `routedActiveCommands`、以及身份闸里一份 6 条的手抄救援清单 `IDENTITY_RESCUE_OPERATIONS`。

登记表已经是真闸（云端出口 / 边缘入口 / 冷待机 / 身份闸四处消费，未登记一律 `operation_unclassified` fail-closed），但**它说得还不够，不足以支撑已经架在它上面的那些闸**——差的那一维只好由手抄清单顶着。刚归档的 `edge-addressing-layers` 判据里，四条尺子的第③条「判错了会不会在平台上留痕」，今天在代码里**没有任何机读形态**。

代价已经发生过一次：`align-cloud-edge-operation-registries` 实测坐实，漏一条登记的后果不是报错，而是云端出口闸静默拒发、投递数返回 0，而**编译期、两仓各自的验收用例、协议逐字对账三道现役闸门对它全部无感**。那次修的是「登记表漏两条」；本 change 修的是它的上游——**为什么会有三份东西需要跟登记表对齐**。

这一步也是后续两步的前置：「可重放动作的检查拆分」与「不可逆动作的检查拆分」都要先有一条机读的「这条命令会不会在平台上留下该账号名下的新痕迹」的线，否则「哪些能自愈重试、哪些绝不重放」只能靠人读代码判断。

## What Changes

- **Cloud→Edge 登记表描述符新增一维「平台留痕」**（这条命令会不会在平台上直接留下该账号名下的新痕迹），边缘与云端两份逐条判定并保持逐字一致。默认值 MUST 落在 fail-closed 一侧：未声明视为会留痕。**本地 IPC 那份 29 条不加**——它不经过身份闸、不参与重放决策，加一个没有消费方的维度正是本 change 反对的形态。
- **身份救援放行清单不再是纯手抄**：清单本体保留（「是不是解开身份终局所必需」不是命令的固有属性，而是该闸相对特定终局的策略，硬要推导就是把策略伪装成事实），但新增机械断言——清单每一条 MUST 在登记表里声明为「不留痕」。误把一条会留痕的命令放进救援清单，测试当场红。
- **删除测试里 46 条手抄清单 `routedActiveCommands`**。它与 `align-cloud-edge-operation-registries` 新加的反向结构断言（以登记表为事实源、逐条去源码找分派点）覆盖同一方向；而「源码路由了一条未登记命令」这一反方向在结构上不可能发生——入口 fail-closed 闸位于路由分支之前。删除前 MUST 用变异验证坐实这两条，验不出就保留并写明理由。
- **跨仓对表闸从「四字段」扩到「全部描述符字段」**，措辞不写死字段数量。
- **BREAKING（仅内部契约）**：三份登记表副本（边缘 / 云端 / 派生仓 `aidcp-automation`）必须同批更新，任一份漏字段即对表闸失败。

**明确不做**：不动两份 `protocol.ts`、不动动作↔消息映射、不新增消息类型、不改任何命令的运行时行为。本 change **零运行时行为变更**——新增的一维当前只被测试断言消费，不参与任何放行 / 拒绝判断。因此不需要出安装包、不需要真机验收。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `client-core-browser-executor-separation`: 集中式登记表的描述符维度从「类别 / 传输 / 身份 / 浏览器前置」扩到含「平台留痕」；新增一条要求——登记表之外 MUST NOT 存在与它平行、且能独立决定放行的手抄命令清单，确需保留的（如身份救援清单）MUST 由登记表机械约束其成员资格。

## Impact

- `aidcp-edge/src/client/operation-registry.ts`（Cloud→Edge 描述符类型 + 46 条逐条判定；客户端那 29 条不动）
- `aidcp-edge/src/client/identity-command-gate.ts`（救援清单新增断言，判据逻辑不变）
- `aidcp-edge/test/client/operation-registry.test.ts`（删手抄清单、加留痕断言）
- `aidcp-cloud/src/comm/operation-registry.ts`（同维度、逐字一致）
- `aidcp-automation`（派生仓，经 `scripts/sync-split-repos` 同步，MUST NOT 手工搬）
- `aidcp/scripts/operation-registry-parity`（比对范围扩到全部字段）
- **排期耦合**：`align-cloud-edge-operation-registries` 的 spec delta 里写着「四个字段 MUST 逐字相同」，该 delta 尚未归档。两条 change 的归档顺序会决定哪一份措辞留在主 spec 里——已列为本 change 的归档前置任务，MUST NOT 靠先后运气。
