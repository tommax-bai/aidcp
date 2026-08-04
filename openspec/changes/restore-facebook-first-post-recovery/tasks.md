# Tasks

## 1. aidcp-edge — 群根导航补真落地等待

- [ ] 1.1 实读 `wait_for_facebook_ready`（`native/page-engine/src/facebook/shared.rs:812-836`）的**全部调用点**，
      判定是就地加地址判据、还是新增一个专用落地等待。**MUST NOT 在未清点调用点前改动共享函数语义。**
- [ ] 1.2 落地等待判据 = 文档就绪 **且** 当前地址解析到请求的群根；有界超时。
- [ ] 1.3 `navigate_first_post_group_root`（`runtime.rs:327-337`）改为导航后等待落地再返回；
      落地失败按姿态类返回（可被纠正预算消费），**MUST NOT 复用帖子身份原因值**。

## 2. aidcp-edge — 纠正预算与准备动作解耦

- [ ] 2.1 `runtime.rs:191` 的 `root_navigated` 拆成两个变量：`prepared_navigation`（记准备阶段，仅供日志）
      与 `corrective_budget`（初值恒为满额、只被失败递减）。
- [ ] 2.2 `runtime.rs:227` 的自救分支改读 `corrective_budget > 0`；用后递减。
- [ ] 2.3 预算耗尽的回执文案写「重试 N 次未成」，**不得**写成「做不到」。

## 3. aidcp-edge — 下滚预算按失败类别消费

- [ ] 3.1 把探测失败分成姿态类与身份类两组（穷举 `first_post_probe_failure` 的全部返回值，**不留兜底桶**；
      未识别的失败值按姿态类处置并具名标注）。
- [ ] 3.2 `select_first_post_candidate`（`runtime.rs:339-363`）循环：姿态类消费一轮后继续；
      身份类（绑定冲突 / 证据变了）立即返回。
- [ ] 3.3 两类在返回值上可分，且能被上层与云端分别识别。

## 4. aidcp-edge — 群根同一性判定不因入参装饰而失败

- [ ] 4.1 `facebook-router/40-group-join.js:173`：剥掉查询串与哈希后再比对，只对「非群地址形态」判无效。
- [ ] 4.2 该失败具名为「请求的群地址无效」，**MUST NOT** 复用帖子身份原因值。

## 5. aidcp-edge — 测试

- [ ] 5.1 Rust 单测：陈旧就绪文档不被当作已落地。
- [ ] 5.2 Rust 单测：准备阶段跳过后，纠正预算仍为满额、自救分支可达（**这条是死分支的回归断言**）。
- [ ] 5.3 Rust 单测：姿态类失败消费一轮后继续探测；身份类失败立即终止。
- [ ] 5.4 JS 分片单测：带跟踪参数的群链接不再判无效；非群地址仍判无效且原因可分。
- [ ] 5.5 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。
      Rust 侧按 memory `native-engine-cargo-path` 取 cargo（不在 PATH，须指 rustup toolchain bin）。

## 6. 交付

- [ ] 6.1 `openspec validate restore-facebook-first-post-recovery --strict` exit 0。
- [ ] 6.2 提交推送 `aidcp-edge` master + 控制仓 main，回写本文件 sha。
- [ ] 6.3 **不打安装包**（CLAUDE.md §6 长期授权：打包只在用户明确要求时做）。
      真机验收项登记 `docs/real-machine-acceptance-backlog.md`，写明「须等一次桌面打包才可观测」。

## 7. 明确不在本 change 范围（各自需配对的安全补充）

- 删除「区域唯一可解析」合取项 —— 必须与「给内容派生分支补同群校验」（`runtime.rs:459-473`，
  对照已有的 `:510-531`）**同批**落地，绝不只删不补。
- 查询串 / 哈希两项从硬合取降为「规范化后复测」。
