# Proposal: persona-wizard-mascot-theme

## Why

当前 Edge 客户端的账号人设浮层已经支持关键词选择、预览确认与按环境展示平台，但选择项仍使用偏重字重和旧蓝色选中态，未与 AIDCP 吉祥物的青绿、金黄、珊瑚配色形成统一设计语言；内容偏好的 `+` 还依赖字体字形，在不同字体栈下会出现视觉偏心。

同时，AIDCP 不只支持小红书。视觉升级必须保留现有 `xiaohongshu | facebook` 平台数据链：功能性选中态使用 AIDCP 品牌色，平台徽标继续分别呈现小红书与 Facebook 身份，不能把小红书文案或颜色写死到通用人设组件。

## What Changes

- 在人设浮层内部引入基于吉祥物的局部色彩令牌：青绿蓝作为功能交互色，金黄用于待确认/待更新，珊瑚作为小红书平台点缀。
- 降低选择项字重、收紧边框与阴影层级，让区块标题、分类标题、具体选项形成清晰阅读顺序。
- 将未选内容项和自定义入口的加号改为 CSS 几何绘制，避免字体基线导致的偏心。
- 保留并补测平台化身份：小红书显示小红书文案与珊瑚平台色，Facebook 显示 Facebook 文案与 Facebook 蓝；平台身份色与通用选中/步骤状态正交。
- 不改变人设关键词、生成、草稿、确认、持久化、闸三态或边云协议。

## Impact

- 代码仓：`aidcp-edge`
- 主要文件：`src/electron/renderer/styles.css`、`src/electron/renderer/renderer.js`、`test/electron/fleet-console.test.ts`
- 无云端、Console、数据库或协议改动。
- Edge 客户端源代码更新后需重新进入桌面发布流程才会影响已安装客户端；本变更默认不构建安装包。
