## Why

边缘长期被描述为「重、不好理解」。盘点后发现这是**两个**问题：「重」大部分是**结构必然**——边缘同时承载四类按**不同编址单位**运转的东西，而云端只对其中一类有话语权；「不好理解」才是真问题——这四类今天全挤在同一个约 1870 行的 `main()` 闭包里，中间没有任何边界（该闭包的代码注释自陈「留在这个无导出的 `main()` 闭包里的判据，用例一行都驱动不了」）。

缺的不是又一张归属表，而是**一把裁决尺子**：面对边缘里任意一件事，凭什么判断它该留在本地、还是该由云端接管。没有这把尺子，每一次归属讨论都要从头论证一遍，且已经出现过用错判据的实例（见 `design.md` §4 判例二）。

## What Changes

- 在控制仓新增一份**分层判据文档**，确立「边缘按编址单位分四层」为边缘一切归属决策的裁决依据：
  - **宿主层**（编址＝机器，权威＝本地）
  - **环境层**（编址＝分身，权威＝本地）
  - **翻译层**（环境 → 账号，权威＝本地）
  - **账号层**（编址＝账号，权威＝**云端**）
- 确立**四条归属判据**（事实归属 / 时序 / 后果 / 性质），并给出三个已裁决判例作为用法示范。
- 写死一条**反模式禁令**：本判据 MUST NOT 派生出任何新的边缘归属表、归属清单或目录规则文件。
- 写死与既有 change `split-classic-client-edge-host` 的**正交关系与不重叠边界**：那条切「产品侧 / 引擎宿主」，本判据作用于**引擎宿主内部**；既有归属台账是本判据的**消费方**。
- 在 `docs/architecture.md` 增加一处指针。

**不含任何代码改动**：不改 `aidcp-edge` / `aidcp-cloud`，不新建归属表或门禁，不动 `split-classic-client-edge-host` 的 worktree 与台账，不部署，不出安装包。

## Capabilities

### New Capabilities

- `edge-addressing-layers`: 定义边缘的四层编址模型与权威归属、四条归属裁决判据、判据的适用边界（作用于引擎宿主内部、与产品/宿主拆分正交），以及「MUST NOT 派生第二张归属表」这条约束。

### Modified Capabilities

（无。本 change 只确立裁决依据，不改变任何已上线规格的需求。）

## Impact

- `aidcp/docs/`：新增分层判据文档（本 change 的主交付物）
- `aidcp/docs/architecture.md`：新增一处指向该文档的指针
- **消费方（本 change 不修改它们，仅建立引用关系）**：
  - change `split-classic-client-edge-host`（分支 `codex/split-classic-client-edge-host`，未合 main）的 82 条通道归属台账与 230 块行段清单
  - `aidcp/docs/edge-split-ownership-inventory.md`
- **不涉及**：`aidcp-edge`、`aidcp-cloud`、`aidcp-console` 任何源码；边云协议；风控与配额口径；部署与打包
