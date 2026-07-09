## Why

`edge-multi-environment-fleet` shipped multi-environment support but put environment management (AdsPower probe / list / multi-select add / create / manual profile id) and the account-persona wizard **inside the settings drawer**, while the left environment rail was only a status strip. The approved v2.3 mock and the operator both want environment management to live **in the left rail** (the rail is where the fleet lives), and the persona wizard to be a per-environment popover launched from each rail row. The operator also hit a concrete bug: clicking an environment showed "已加入" but it never appeared in the rail — because adding only mutated the renderer's in-memory roster and never persisted, so the shell (which builds the rail from saved environments) never learned about it.

## What Changes

- **Environment management moves out of the settings drawer into the left rail.** A "＋ 添加环境" button (rail head + a collapsed-state foot button) opens a dedicated popover with two tabs: **加入现有环境** (multi-select AdsPower profiles into the roster) and **新建环境** (template + platform create). Manual profile-id entry is a fold inside the join tab.
- **Adding / creating an environment persists the roster immediately** (`saveSettings` with `environments`), so the shell builds a handle at once and the environment appears in the rail as an offline row — fixes "点击显示已加入但左栏看不到".
- **Rail matches the mock:** environment count, run / attention / idle summary chips, severity grouping (需要处理 / 运行中 / 暂停·离线), each row = avatar + nickname + a per-row **persona icon** (after the nickname, before the status) + status dot/label.
- **Per-environment persona popover:** clicking a rail row's persona icon selects that environment and opens an independent persona wizard popover scoped to it (envId-routed generate/persist preserved — never binds to the wrong account). The persona wizard moves out of the settings drawer.
- **Settings drawer slimmed** to three cards: browser engine (with the AdsPower API key/base folded into its advanced section), window parking, and the developer-details toggle. The待配置 active-step now directs the operator to the rail add panel instead of the drawer.
- **Follow-up render fixes** (operator-reported on the real app): the add/persona popovers were pinned invisible because `open()` added `.open` but left the `.hidden { display:none !important }` class — `open()` now removes `hidden`; collapsed rail rows overlapped and are now fixed centered cells with the name block force-hidden and a smaller avatar; the expanded rail narrowed 216→168px.

## Capabilities

### Modified Capabilities

- `adspower-desktop-env-picker`: The configuration surface moves out of the settings drawer — AdsPower probe / environment list / multi-select add / manual profile id / create-environment now live in a rail-launched add/create popover; the settings drawer keeps only the browser-engine toggle (with API credentials folded into its advanced section), window parking, and the developer toggle. Steady-state first screen still carries no config form; the待配置 active step now opens the rail add panel.

### New Capabilities (folded into `edge-fleet-console`)

- `edge-fleet-console`: The left rail hosts environment management (add / create) and a per-environment account-persona popover launched from a per-row persona icon; adding/creating an environment persists immediately so it appears in the rail at once.

## Impact

- Affected repos: `aidcp-edge` only (renderer `index.html` / `renderer.js` / `styles.css`; no `main.cjs` behavior change beyond the already-shipped `saveSettings` env persistence). No `aidcp-cloud` / `aidcp-console` change.
- Landed on `aidcp-edge` master: `2f68469` (rail env management + persona popover + slim settings) and `833a4ee` (popover visibility + collapsed-rail layout fixes). Edge 791 tests + `test:acceptance` + `typecheck` green.
- Real-machine visual verification registered in `docs/real-machine-acceptance-backlog.md` 簇 24 (the fleet cluster).
