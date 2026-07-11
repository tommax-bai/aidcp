# 实现说明 / 落地状态（durable，供 edge 仓恢复后一键补齐）

**状态（2026-07-11）**：edge 代码改动**已实现并全绿验证**，但**尚未 land**——集成阶段共享 edge checkout `../aidcp-edge` 被并发活动清空、整个 edge git 仓一度不可用，无法 commit。改动实现已在此 durable 记录（不依赖任何临时目录），edge 恢复后按下方三步补齐即可。

**验证结果（在隔离 worktree + `npm ci` 后跑）**：
- `npm test` → **964 pass / 0 fail**（960 基线 + 本 change 4 个新测试）
- `npm run typecheck` → 干净通过
- 新测试单跑 → 4/4 pass

---

## 改动 1：`src/electron/main.cjs`（顶部插入 userData 覆盖）

**锚点**（`require('./persona-notice.cjs')` 之后、AdsPower 只读客户端注释之前）——把下面这段插进去：

```js
} = require('./persona-notice.cjs');

// ── 实例级 userData 隔离（change edge-multi-instance-userdata-isolation）──────
// 同机并行多个监督者（如一个连 dev、一个连 ol）时，各实例需独立的单实例锁 /
// 设置(名册) / 界面状态 / 日志 / 内置运行时落地目录——它们全部从 userData 派生。
// 设了 AIDCP_USER_DATA_DIR 就把 userData 指到该目录；未设则用默认目录、行为逐字不变（零回归）。
// 必须在 requestSingleInstanceLock() 与任何 app.getPath('userData') 之前设置：锁文件落在 userData，
// 且所有 userData 派生路径读取均为 whenReady 之后的懒调用，故模块顶部此处即满足顺序约束。
{
  const instanceUserDataDir = (process.env.AIDCP_USER_DATA_DIR || '').trim();
  if (instanceUserDataDir) {
    app.setPath('userData', instanceUserDataDir);
  }
}

// 主进程侧 AdsPower 只读客户端（探测 + 环境列表 + 在跑分身对账）。单例持有本进程内**唯一**串行节流（1req/s）。
```

## 改动 2：`README.md`（新增「同机并行两个 GUI」小节）

在「关键环境变量」注释块之后、`## 与云端的关系` 之前插入：

```markdown
### 同机并行两个 GUI（如 dev + ol）

桌面客户端默认「一台机一个监督者」（单实例锁）。若要在同一台机器上并行两个 GUI（例如一个连 dev、一个连 ol），给每个实例设不同的 `AIDCP_USER_DATA_DIR`——它把该实例的**用户数据目录**（进而单实例锁 / 设置名册 / 界面状态 / 日志 / 内置运行时落地）整体隔离；未设时用默认目录、行为不变。

​```bash
# 实例甲：dev（默认目录）
AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm run electron:dev

# 实例乙：ol（独立用户数据目录）
AIDCP_USER_DATA_DIR="$HOME/Library/Application Support/aidcp-edge-ol" \
AIDCP_CLOUD_URL=ws://123.56.253.183:8787 npm run electron:dev
​```

> 并行前置（本机全局 AdsPower 服务与分身库两实例共享，仅 userData 被隔离）：
> - 两实例的 AdsPower 分身**不重叠**（同一分身被两实例驱动 = 两套操纵系上同一浏览器，且因连不同云不报错、静默互扰）；
> - **先起一个、待 AdsPower 本机服务稳定后再起第二个**（避免冷启动抢杀机器全局 50325 守护进程）；
> - 两实例保持默认 AdsPower 模式（self 模式会撞固定 9222 调试端口）。
```

## 改动 3：新增 `test/electron/instance-userdata-isolation.test.ts`（源码契约守卫）

沿用 `lifecycle-contract.test.ts` 的「读 main.cjs 源码做契约断言」方式（main.cjs 有顶层副作用、无法直接 require）。锁三条不变量：存在、受守卫（零回归）、且在单实例锁与任何 `getPath('userData')` 之前生效。**关键坑**：顺序断言必须按**代码**位置比较——先剥掉整行注释，否则本段代码注释里合法引用 `app.getPath('userData')` / `requestSingleInstanceLock()` 会污染 naive 源码搜索（已在本轮踩到并修正）。完整内容见随附测试文件（同名，落 `test/electron/`）。

---

## 落地三步（edge 恢复为健康 git 仓后）

1. 从 `origin/master` 新建分支 `edge-multi-instance-userdata-isolation`，应用上述三处改动（有恢复脚本可精确锚点替换、锚点不在即报错）。
2. `npm run typecheck` + `npm test`（应 964/0），再 `git add` 那三个文件、commit。
3. 按 `scripts/land-change aidcp-edge edge-multi-instance-userdata-isolation` 集成 → 回写本 change `tasks.md` 的 sha → `openspec validate --strict` → archive；真机项登记 backlog 簇 46（同机两 GUI 各连 dev/ol、各用不同分身、互不干扰）。
