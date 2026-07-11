## 1. aidcp-edge — 实例级 userData 隔离

- [x] 1.1 在 `src/electron/main.cjs` 顶部（require 之后、`requestSingleInstanceLock()` 与任何 `getPath('userData')` 之前）新增：`if (process.env.AIDCP_USER_DATA_DIR) app.setPath('userData', process.env.AIDCP_USER_DATA_DIR)`，带注释说明顺序约束与零回归守卫 <!-- aidcp-edge cdb7115 顶部 require 后插入守卫块 -->
- [x] 1.2 添加单元测试：设置 `AIDCP_USER_DATA_DIR` 时 userData 解析到该目录、未设时用默认；断言覆盖发生在锁与派生路径读取之前（以可测方式验证顺序 / 副作用） <!-- aidcp-edge cdb7115 test/electron/instance-userdata-isolation.test.ts 源码契约守卫4断言;坑=顺序断言先剥整行注释 -->
- [x] 1.3 `npm run typecheck` 通过 <!-- aidcp-edge cdb7115 干净 -->
- [x] 1.4 `npm test`（含相关 acceptance）通过 <!-- aidcp-edge cdb7115 964/0（960基线+4新测试） -->

## 2. 文档 & 运营前置

- [x] 2.1 在 edge 侧文档（如 `docs/` 或 README 相关处）记录 `AIDCP_USER_DATA_DIR` 用法与并存启动示例（dev + ol 两 GUI 命令），以及三条运营前置：分身不重叠、错峰启动、保持 AdsPower 模式 <!-- aidcp-edge cdb7115 README「同机并行两个 GUI」小节 -->
- [x] 2.2 在中控仓真机验收 backlog（`docs/real-machine-acceptance-backlog.md`）登记：同机两 GUI 各连 dev/ol、各用不同分身，能同时正常运行互不干扰 <!-- aidcp 本次 archive 提交，backlog 簇 46 -->

## 3. 集成与回写

- [x] 3.1 独立 worktree 开发；集成前 `git fetch` + rebase 到最新 edge master、解冲突、跑 `test:acceptance` + `typecheck` 再 ff 合并（热点文件 main.cjs：集成时逐位保留本段） <!-- aidcp-edge cdb7115 origin/master 238b1cb..cdb7115 干净 ff；base 未变无需 rebase。注：集成时共享 edge checkout 被并发清空、原 worktree git 绑定断，改从全新 clone 应用同源预留文件（diff 仅 +31 行三处）后 land -->
- [ ] 3.2 合并后 ff 更新 edge 主 checkout（用户在此跑 electron:dev） <!-- 阻塞：canonical checkout ../aidcp-edge 被并发清空（仅剩 scripts/）；待用户/fleet 恢复该 checkout 并 pull master cdb7115 后生效 -->
- [x] 3.3 用 HTML 注释回写各 task 的 commit-sha；validate --strict 通过后 archive <!-- aidcp 本次提交回写 + archive；validate --strict 通过 -->
