# Design — role-model-category-config

把三件相关但易过度设计的事（分类层 / 分类默认模型 / 全局默认正名）合到一个 change，并预埋账号维度数据缝。核心设计决策如下，重点是**优先级链**、**schema（含 account_id 缝）**、**解析器如何变**，以及**砍掉的超前抽象**。

## 1. 优先级链（precedence）

模型解析当前两层（坐实：`server.ts:151-154` `resolveModelForRole`）：

```
per-role 覆盖（role_config.model）  →  全局 textModel（model_config.text_model）  →  代码默认（'qwen-turbo'）
```

本 change 在中间插入「分类默认」，并把账号维度作为**最高优先级但本期不接线**的缝预留进契约。最终**契约级五层优先级**（自高而低）：

```
1. 账号覆盖    account_id 命中的 per-role / 分类行   ← item 9 缝，本期不接线（解析恒走 account_id IS NULL）
2. per-role 覆盖   role_config.model（account_id IS NULL）
3. 分类默认       category_config.model（该角色所属 category，account_id IS NULL）
4. 全局默认       model_config.text_model（item 7 正名为「默认模型」）
5. 代码默认       'qwen-turbo'
```

**本期实装的是第 2→3→4→5 四层**（第 1 层只建 schema 缝、不接线）。逐层「缺行 / 空串 / 无效」都向下回落，**任意一层不可达都不得 brick**——最坏回落到代码默认。

温度（`resolveTempForRole`，`server.ts:155-158`）**本期不引入分类层**：温度只对少数生成 / 改写类角色开放，按角色配已足够，加分类温度层是 YAGNI。保持两层（per-role → 构造默认）。

## 2. Schema（迁移 0009）

新增分类默认表，并在其上直接预埋可空 `account_id`（`NULL = 全部账号`）。**不**给 `role_config` 补 `account_id`——为避免改动既有表的主键（`role_id` 是 PK，加 account_id 进 PK 会动既有行语义）；item 9 的账号缝**集中在新表上验证形态**，待真多账号落地时再以同一形态把 per-role 账号行迁移到位（design 已记录此演进路径，不在本期做）。

```sql
-- 0009_role_category_config.sql
-- 分类级模型默认（item 5/6）+ 账号维度数据缝（item 9，本期不接线）。
-- account_id NULL = 适用全部账号；非空 = 某账号专属（本期不写入、不读取非 NULL 行）。
-- 与 src/config/category-config-store.ts 的 CREATE TABLE IF NOT EXISTS 同源（幂等）。
CREATE TABLE IF NOT EXISTS category_config (
  category_id TEXT NOT NULL,                 -- 稳定分类 key（与 role-catalog 导出的 category 一致）
  account_id  TEXT,                          -- NULL = 全部账号（本期恒 NULL）；预留按账号覆盖缝
  model       TEXT,                          -- 该分类默认模型；NULL/空 = 回落全局
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by  TEXT
);
-- 唯一性：每分类 × 账号至多一行。NULL account_id 用部分唯一索引保证全局默认行唯一。
CREATE UNIQUE INDEX IF NOT EXISTS uq_category_config_global
  ON category_config (category_id) WHERE account_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_category_config_account
  ON category_config (category_id, account_id) WHERE account_id IS NOT NULL;
```

说明：
- 用**两个部分唯一索引**而非把 `account_id` 放进主键——PostgreSQL 主键不容 NULL，而我们恰恰要 `NULL=全部账号`。部分唯一索引让「全局默认行（account_id IS NULL）每分类唯一」与「账号专属行每(分类,账号)唯一」并存，且账号缝零额外代码即可启用。
- 存储层读路径本期固定 `WHERE category_id = $1 AND account_id IS NULL`；账号缝启用时只需把 `IS NULL` 换成「先查账号行、miss 再查 NULL 行」，无需改表。

`category_id` 不入库成枚举表——分类清单由 `role-catalog.ts` 代码白名单导出（与 roleId 同样的白名单制），写校验拒未知 `category_id`，避免运营写脏分类。

## 3. 分类目录层（role-catalog）

给 `RoleCatalogItem` 加：

```ts
category: string;        // 稳定分类 key（如 'browse_judge' / 'browse_compose' / 'publish_create' / 'publish_gate' / 'publish_image'）
```

并导出：分类清单（key + 中文显示名 + 排序）、`categoryOf(roleId)`、`rolesInCategory(categoryId)`、`isKnownCategory(categoryId)`。分类把现有 18 角色按「判定类 / 撰写改写类 / 发布创作类 / 发布裁决类 / 图像类」聚合（具体归类在实装时定，spec 只约束机制不钉死分类名）。

**边界（铁律）**：分类是**配置目录层**，只服务后台查看 / 编辑 / 模型默认解析。它**MUST NOT 进 `role-dispatcher.ts` 的运行时角色注册表**——运行时分发仍按 roleId，EventBus / SessionContext / 15-role 注册逻辑零改动。这条防止「为了配置分组而污染运行时编排」。

## 4. 解析器如何变（server.ts，本 stream 拥有的块）

```ts
// before（两层）
const resolveModelForRole = (role?: string): string => {
  const override = role ? roleConfigStore.getForRole(role).model : null;
  return override?.trim() || modelConfigStore.getCached().textModel;
};

// after（四层；account 缝恒 IS NULL）
const resolveModelForRole = (role?: string): string => {
  const roleOverride = role ? roleConfigStore.getForRole(role).model : null;
  if (roleOverride?.trim()) return roleOverride.trim();                       // 2. per-role
  const catId = role ? categoryOf(role) : undefined;                          // role-catalog 映射
  const catDefault = catId ? categoryConfigStore.getForCategory(catId).model : null; // account_id IS NULL
  if (catDefault?.trim()) return catDefault.trim();                          // 3. 分类默认
  return modelConfigStore.getCached().textModel;                            // 4. 全局默认（即「默认模型」）；store 缺省回 5. 代码默认
};
```

要点：
- 完全向后兼容——分类表为空 / 角色无分类时退化为原两层，**不传 role 仍走全局**（planner / select / 探活路径不受影响）。
- `categoryConfigStore` 缺/空/异常一律返回「无覆盖」→ 向下回落，**绝不抛、绝不 brick**（init 失败时 server.ts catch 块照现状 warn 并继续）。
- **本 stream 先落 server.ts 此块**；D（safety-quota）/ F（account-persona）只把自己的 store-init 与面板依赖 wiring **append** 在其后，不得改本块。

## 5. 正名（item 7，无新层）

全局 `textModel` 已端到端可改（`model_config` 表 / `PUT /api/config/model` / SettingsPage）。本 change **不新增任何全局层**，仅：
- UI 文案把「文本模型」正名为「默认模型」（SettingsPage + RolesPage 的回落说明）。
- spec 上明确：优先级链末端的「全局默认」就是这个既存 `textModel`，分类 / 角色页所说「回落到默认」即回落到它。

## 6. 砍掉的超前抽象（YAGNI / 对抗性自审）

- **不**做分类级温度层（温度按角色已够）。
- **不**做分类继承 / 多级嵌套分类（一层扁平分类足够运营分组）。
- **不**把 `account_id` 串进 LLM 调用点（item 9 明确只建缝）。
- **不**给 `role_config` 表改主键加 account_id（避免动既有行语义；账号缝集中在新表验证）。
- **不**做分类的运行时语义（坚决不进 role-dispatcher 注册表）。

## 7. 失败模式与回落自检

- 分类表 init 失败 → 解析退化为原两层（per-role → 全局 → 代码），系统正常运行。
- 运营给分类填了无效模型名 → 沿用既有保存前探活，**诚实拒绝、不落库、不假成功**。
- 运营删除某分类默认 → 该分类下角色立即回落全局默认（热加载，写库成功才刷镜像）。
- 误写未知 `category_id` → 面板写校验拒（白名单制，类比 `isKnownRole`）。
