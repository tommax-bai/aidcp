## Why

Facebook 账号来源的导出字段顺序和分隔符并不统一，当前客户端只按两种固定位置模板解析；新格式需要人工重排，既低效，也容易把密码、2FA、邮箱、Cookie 或 Access Token 错配。客户端需要在创建环境前以可扩展、可校验且失败关闭的方式识别常见账号记录格式。

## What Changes

- 将单建和批量建共用的 Facebook 账号解析入口改为可扩展的格式规则注册表，按行识别受支持的字段布局。
- 新增对 `uid|password|2FA|email|cookie|access_token` 记录的直接识别，同时保持现有两种格式兼容。
- 使用邮箱、Facebook Cookie、数字 UID、Base32 2FA、Access Token 等字段特征验证候选规则，并以 Cookie `c_user` 与 UID 一致性阻止账号错配。
- 仅在一个规则确定匹配时生成创建计划；未知或歧义格式按安全行号拒绝，整批不创建环境。
- 在导入区域展示支持自动识别的说明；Access Token 与其他无关字段仍只用于识别边界并立即丢弃。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `adspower-environment-provisioning`: Facebook 单建与批量建账号资料从两种固定格式扩展为经字段特征和身份交叉校验的多规则自动识别。

## Impact

- Edge：`src/electron/facebook-account-import.cjs`、导入区域提示文案及聚焦测试。
- OpenSpec：更新 `adspower-environment-provisioning` 的导入行为契约。
- 不新增运行时依赖，不改变 Cloud、Console、协议、数据库或 AdsPower 创建 API；不保存或回显原始凭据。
