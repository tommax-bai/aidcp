## Why

The edge desktop companion always launches an AdsPower environment into xiaohongshu, because the platform is a process-level env (`AIDCP_PLATFORM`) that the desktop shell never injects and defaults to xiaohongshu. Operators cannot create or launch a Facebook environment from the app even though the platform runtime abstraction supports per-platform drivers. This adds a per-environment platform choice so a Facebook environment launches on facebook.com and reports the right platform at handshake — completing the entry-point side of Facebook support and closing the loop with the cloud (`accounts.platform` + the accounts-page platform column + Facebook comment config).

## What Changes

- Store a per-environment platform in the AdsPower profile remark at create time (`plat`), read back on list (legacy environments without it fall back to xiaohongshu).
- Add a platform selector (小红书 / Facebook) to the "create environment" UI, threaded through IPC to the create flow and into the remark.
- Show each environment's platform in the environment list; when an environment is selected, sync its platform into desktop settings.
- Inject `AIDCP_PLATFORM` into the core process from the selected environment's platform at launch (`buildProviderEnv`), defaulting to xiaohongshu (byte-identical to today).

## Capabilities

### Modified Capabilities

- `platform-runtime-abstraction`: the edge platform is selected per AdsPower environment from the desktop app and injected into the core at launch, instead of being a hidden process-level default that is always xiaohongshu.

## Impact

- Affected repos: `aidcp-edge` (Electron desktop shell only: `src/electron/*.cjs` + renderer). Does NOT touch `src/platform/*` or `src/facebook/*` (those live on the concurrent `facebook-browser-env-and-login` branch).
- Zero-regression for xiaohongshu: default platform is xiaohongshu, so `AIDCP_PLATFORM=xiaohongshu` is injected — the core already defaults to the xhs driver, so behavior is unchanged for existing environments.
- Forward-compatible dependency: selecting Facebook only fully works once the Facebook edge driver is registered on `aidcp-edge` master (currently on `facebook-browser-env-and-login`). Until then, launching a Facebook environment makes the core fail-fast honestly ("platform=facebook has no edge driver in this build"), not silently.
