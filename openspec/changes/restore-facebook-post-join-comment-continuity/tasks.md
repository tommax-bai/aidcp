# Tasks

## 1. aidcp-edge — 首帖滚动测量与实际滚动容器对齐

- [ ] 1.1 在 `native/page-engine/src/facebook-router/20-feed.js` 把「解析真正在滚的元素」提成一个共享 helper，`feedScrollMetrics` 由它派生，行为不变。
- [ ] 1.2 `native/page-engine/src/facebook-router/90-dispatch.js` 的滚动分支改用该 helper 实际滚动并测量位移/到底，替换 `window.scrollBy` 与窗口坐标读数。
- [ ] 1.3 补回归：文档不可滚（滚动条在 feed 祖先容器）时，位移非 0、到底判据不恒真、四轮预算可跑满；窗口正常可滚时行为不变。
- [ ] 1.4 `20-feed.js` 新增 `Đi đến Bảng feed` 的唯一可见目标探针并随 `feed_probe` 上报；JS 只返回视口坐标，不调用 DOM `click()`，模糊/离屏均失败关闭。
- [ ] 1.5 Native Feed 初扫/滚动在看到该探针后前台化并重新定位，发送一次 CDP `mouseMoved → mousePressed → mouseReleased`；控件消失且 home surface 确认后才继续，否则按是否已发点击返回未开始/结果不明。
- [ ] 1.6 补路由与 fake-CDP 回归：精确越南语文案可识别、近似文案/多目标不可执行、零 DOM click、仅一组 CDP 点击、缺失 home 后置状态不报成功。

## 2. aidcp-edge — 首帖时间预算与命令上限

- [ ] 2.1 `native/page-engine/src/facebook/runtime.rs`：首帖身份回读窗 8s → 20s，首帖评论框绑定窗 4s → 12s。
- [ ] 2.2 `src/native-page-engine/browse-session.ts`：首帖开帖命令的原子上限从默认 30s 提到 90s（与加群命令同值，避免上限种类膨胀）；仅对「首帖选择」这一形态生效，普通开帖不变。
- [ ] 2.3 补回归：首帖开帖命令取到 90s 上限，关键词开帖与其他命令仍取默认值。
- [ ] 2.4 加群侧任何预算**不得改动**（proposal「Constraint To Resolve Explicitly」）。

## 3. aidcp-edge — 租约抑制命令必须回执

- [ ] 3.1 `src/main.ts` 租约抑制分支由「打日志后 return」改为回一条具名的未执行回执（成功位为假）。
- [ ] 3.2 补回归：抑制时回执被发出、成功位为假、原因具名；正常归属命令不受影响。
- [ ] 3.3 接上 `facebook-first-post-comment-confirmation` task 5.6（该 change 明确留给后续）。

## 4. aidcp-cloud — 首帖开帖步上限

- [ ] 4.1 `src/comment-agent/facebook-edge-steps.ts`：新增仅用于首帖开帖的步上限 105s（= 边端 90s + 传输余量），关键词开帖仍用现值 45s。
- [ ] 4.2 更新该常量处的注释推导（边端窗口构成 + 为何云端只做兜底上界）。
- [ ] 4.3 补回归：首帖步用新上限、关键词步用旧上限。

## 5. aidcp-cloud — Reels 再入死锁与滚动无目标处置

- [ ] 5.1 `src/orchestrator/role-dispatcher.ts`：普通 feed **确认为空 / 确认到底**时同样把 Reels fallback 状态解回可授权态，不再只认「非空 feed 回归」。
- [ ] 5.2 `src/orchestrator/role-dispatcher.ts`：为「滚动回执失败且原因为无目标」补处置分支——给出下一步或诚实终止会话，杜绝无命令无终态悬停。
- [ ] 5.3 补回归：空首页账号被送回首页后仍可再次授权切 Reels；滚动无目标不再产生零命令悬停。

## 6. 验证

- [ ] 6.1 edge：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（含 native 引擎构建）。
- [ ] 6.2 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。
- [ ] 6.3 安全红线全过：`AC-PROTO-*`、`AC-PUB-*`、`AC-RISK-*`。

## 7. 集成与部署

- [ ] 7.1 edge / cloud 分别 `land-change` 合回各自 master。
- [ ] 7.2 cloud 部署 dev（按 CLAUDE.md §5 安全序列：先备份 → rsync → restart → healthcheck）。
- [ ] 7.3 edge 改动**须重新打包桌面客户端**才在运营机生效；按 CLAUDE.md §6，打包属用户显式触发动作，本 change 不含出包。

## 8. 真机验收（登记 backlog，不在本 change 内判定）

- [ ] 8.1 慢群页（越南代理）加群后首帖评论一次跑通：确认四轮下滚真的发生、身份回读在 20s 内完成。
- [ ] 8.2 空首页账号被送回首页后可再次切到 Reels，不再出现零命令悬停到冷待机。
- [ ] 8.3 取一次首帖返回的目标身份原值，判定 design §6 那条「就地绑定指纹不含固链、身份回读却依赖固链」的线索成立与否。
