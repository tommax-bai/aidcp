## 1. aidcp-edge — 实例级 userData 隔离

- [ ] 1.1 在 `src/electron/main.cjs` 顶部（require 之后、`requestSingleInstanceLock()` 与任何 `getPath('userData')` 之前）新增：`if (process.env.AIDCP_USER_DATA_DIR) app.setPath('userData', process.env.AIDCP_USER_DATA_DIR)`，带注释说明顺序约束与零回归守卫
- [ ] 1.2 添加单元测试：设置 `AIDCP_USER_DATA_DIR` 时 userData 解析到该目录、未设时用默认；断言覆盖发生在锁与派生路径读取之前（以可测方式验证顺序 / 副作用）
- [ ] 1.3 `npm run typecheck` 通过
- [ ] 1.4 `npm test`（含相关 acceptance）通过

## 2. 文档 & 运营前置

- [ ] 2.1 在 edge 侧文档（如 `docs/` 或 README 相关处）记录 `AIDCP_USER_DATA_DIR` 用法与并存启动示例（dev + ol 两 GUI 命令），以及三条运营前置：分身不重叠、错峰启动、保持 AdsPower 模式
- [ ] 2.2 在中控仓真机验收 backlog（`docs/real-machine-acceptance-backlog.md`）登记：同机两 GUI 各连 dev/ol、各用不同分身，能同时正常运行互不干扰

## 3. 集成与回写

- [ ] 3.1 独立 worktree 开发；集成前 `git fetch` + rebase 到最新 edge master、解冲突、跑 `test:acceptance` + `typecheck` 再 ff 合并（热点文件 main.cjs：集成时逐位保留本段）
- [ ] 3.2 合并后 ff 更新 edge 主 checkout（用户在此跑 electron:dev）
- [ ] 3.3 用 HTML 注释回写各 task 的 commit-sha；validate --strict 通过后 archive
