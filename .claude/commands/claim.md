---
description: 自主认领一个无人在做的活跃 change 并实装(worktree=认领锁,先报再干)
---

自主领活。你将从活跃 change 中认领一个无人在做的,然后按 /impl 全流程实装。$ARGUMENTS 若非空则作为筛选提示(如指定仓或主题)。

1. **摸现状**:跑 `scripts/fleet-status` + `openspec list`。候选 = 活跃 change 中同时满足:
   - **无同名 worktree**(worktree 存在 = 已被别的终端认领,跳过);
   - **最近约 1 小时无人推进**(openspec list 的时间戳很新 = 有并发 session 正在做,跳过);
   - tasks.md 里有**代码可完成**的未勾 task(纯剩真机验收/部署收尾的不算)。
2. **选一个**:按就绪度(task 描述具体、依赖已解)与价值排序取第一;主要动热点文件(CLAUDE.md §7 清单)的候选降到最后。
3. **先报再干**:用一两句话向用户报出你认领了哪个、为什么,**随即开工不等确认**(用户可随时打断改派)。
4. **认领即上锁**:立刻 `scripts/new-change <repo> <该change名>` 建 worktree。若因分支已存在而失败 = 刚被并发终端抢先认领,回到第 2 步换下一个候选。
5. 之后完全按 `/impl <该change名>` 的流程执行(隔离开发→测试全绿→land-change 集成→tasks.md 回写→真机项登记 backlog→按需部署→归档)。
