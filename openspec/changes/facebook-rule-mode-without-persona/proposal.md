## Why

Facebook 规则模式的全部动作都不需要人设：选卡按上报顺序、点赞是固定意图、评论正文来自模板。但今天三道人设闸把它挡在门外——会话启动闸要求账号已绑人设、模式裁决闸要求已绑人设、评论触发口也要求已绑人设。运营为了跑一个完全不读人设的模式，仍须先为每个账号配一份从不被使用的人设，这是纯粹的空转工作量，也让「人设是账号运行的前提」这条不变量失去解释力。

规格现状把这条约束写死了：`facebook-rule-mode-cadence` 明确要求规则模式账号「仍须满足现有绑定人设入口闸」。所以这是改约束，不是补实现。

## What Changes

- 规则模式成为「人设是账号运行的前提」的一处**窄例外**：Facebook 账号在规则模式下 SHALL 无需绑定人设即可启动会话、浏览、点赞与执行加群联系评论。例外仅限规则模式，普通浏览与发布的人设闸逐字不变。
- 会话启动闸增加同一处例外：环境已启用规则模式且平台为 Facebook 时，未绑人设 MUST NOT 被短路为 `needs_persona_setup`。
- **规则批次的评论段强制走模板正文**：有效正文方案 MUST 为模板（账号显式模板、或账号未显式选择时按既有默认走区域通用模板）。账号显式选择生成方案时，规则批次的评论段 MUST 以具名原因如实标为不可执行，该批次只做浏览与点赞，MUST NOT 调用生成器、MUST NOT 以任何替代人设撰写。
- 模板正文继续经过既有的确定性正文校验、联系方式分离注入、审批策略、目标复核、平台确认与真实终态记录；本变更 MUST NOT 削弱其中任何一项。
- 未绑人设的规则模式账号在 Console 与客户端 SHALL 如实呈现为「按规则运行、未绑人设」，MUST NOT 呈现为待补人设，也 MUST NOT 呈现为已绑。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `mandatory-account-persona`: 为 Facebook 规则模式增加一处窄例外——该模式的浏览、点赞与模板评论不要求账号绑定人设。
- `persona-gated-session-start`: 会话启动闸对已启用规则模式的 Facebook 账号取消未绑人设短路。
- `facebook-rule-mode`: 取消规则模式的绑定人设入口闸，并把评论段的正文方案收窄为模板，生成方案下评论段如实不可执行。
- `comment-interaction`: 明确人设注入只约束生成式评论链，规则模式的模板正文不读人设、不做人设口吻改写。

## Impact

- **Control**：本变更文档与交付记录。依赖 `facebook-rule-mode-cadence`、`facebook-global-group-regional-comment-templates` 与 `facebook-join-contact-first-post` 先行归档——三者的能力规格尚未并入 `openspec/specs/`，本变更的对应 delta MUST NOT 先于它们生效。与 `environment-level-rule-mode-and-approval` 无功能耦合，两条可并行实装；若两条都改 `facebook-rule-mode`，归档时按先后合并即可。
- **Cloud**：会话启动闸与模式裁决闸增加规则模式旁路；规则批次调用评论编排前先解析有效正文方案，非模板方案以具名终态收敛；评论触发口的人设闸对规则批次来源放行。
- **Console / Edge**：未绑人设的规则模式账号的呈现口径。
- **Data / protocol**：不新增迁移，不修改边云协议，不改变规则定义版本。
- **Out of scope**：普通浏览与发布的人设闸不变；系统仍不存在默认或兜底人设；本变更不授权 OL 部署、Edge 打包或真实账号写入验收。
