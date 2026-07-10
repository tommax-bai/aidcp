# Facebook browse+like — real-machine probe findings (2026-07-10)

> Probed the live desktop FB feed/detail DOM (test account Michelle Garcia `61591458584142`, env `k1ehveal` now desktop Mac UA — see memory `fb-test-env-desktop-ua-fix`). CDP direct-attach to the AdsPower browser. These pin the edge `src/facebook/` selectors for `page.cards` / `note.detail` / the like atomic action (tasks 2.1, 3.x, 7.7).

## Prerequisite: desktop UA is mandatory
- FB serves layout by **UA first**, width second. An iPhone-UA env gets the mobile site (private glyph fonts, NO `role=feed`/`role=article`) regardless of window width. The env must be a desktop fingerprint. `--start-maximized` added to the AdsPower launch path (edge `eaec298`).

## Feed (wide layout, innerWidth 1440)
- **Feed container**: `div[role="feed"]` (no aria-label).
- **Scroll container**: the **document/window** scrolls (NOT an inner overflow container). FB feed scroll = window scroll / `window.scrollBy`. (Contrast xhs which may use an inner container.)
- **Cards**: `[role="article"]`. FB **virtualizes** the feed — only in-viewport articles are hydrated; off-screen `[role=article]` are empty shells (no author/permalink/buttons). **Extraction MUST skip un-hydrated shells (no author link → skip), never fabricate.** Detect hydrated via presence of `h2/h3/h4 a` (author).

### Per-card fields (from a hydrated `[role=article]`)
- **author name + profile href**: `article h2 a | h3 a | h4 a` → `innerText` = name; `.closest('a')` href = profile URL (carries `__cft__`/`__tn__` tracking params — strip query for identity).
- **permalink (post identity)**: `a[href]` matching `/posts/|permalink|story_fbid|/videos/|/photos/|/reel/`; canonical form `/{page}/posts/pfbid0...`. Strip `?` query. Use as the note id + the URL to open detail.
- **media**: `article img` count / `article video` count. (Image posts, video posts, reels differ.)
- **reaction/comment/share counts**: read from the action-bar button labels/adjacent text (see below).
- **`collect`**: FB has **no favorite/collect** → honest default/absent, NEVER fabricated (spec).

### Action bar (bottom of each post) — LIKE DISAMBIGUATION (critical)
Buttons in the post action cluster, in DOM order:
1. `[role=button][aria-label="赞"]` **with numeric text** (e.g. `"3,829"`) = **reaction COUNT summary** (opens reactors list). **NOT the like toggle.**
2. `[role=button][aria-label="留下心情"]` **empty text** = **the LIKE ACTION button** (click = 赞/Like; hover = reaction picker). ← this is the like target.
3. `[role=button][aria-label="发表评论"]` (text = comment count e.g. `"66"`) = Comment button.
4. `[role=button][aria-label="发送给好友或发布到你的个人主页。"]` (text = share count) = Share button.
5. `[role=button][aria-label="赞：3,706位用户"]` = "liked by N" reaction detail.

- **The post action bar has NO `role="toolbar"`** — identify it as the smallest common ancestor of the like button (`留下心情`) and the comment button (`发表评论`).
- **aria-labels are LOCALIZED** (`留下心情`/`发表评论` are zh-CN). Need a multi-locale matcher (reuse the group-join `classifyCtaLabel` i18n precedent, memory `fb-group-join-observe-i18n`). zh-TW/en/es strings TBD — confirm during shadow.
- `aria-pressed` is **null/unused** — like state is NOT exposed via aria-pressed.

## Detail (open a post)
- Navigating to the `/posts/pfbid...` permalink opens the post as a **`role="dialog"` modal** over the feed (`inDialog: true`). `articleCount` jumps (post + each comment is a `[role=article]`).
- **Post body**: `[data-ad-comet-preview="message"] | [data-ad-preview="message"]`, fallback `div[dir="auto"]`. Extracted full body successfully.
- **Post-level like** (target for the browse-loop interact step): the `留下心情` button whose action cluster ALSO contains `发表评论` (post comment button). **Comment-level** react buttons (`aria-label="赞"` text `"赞"` + `留下心情` + `"N个心情"`) do NOT have a `发表评论` sibling → use that to exclude comment likes.
- **Comments**: each is a `[role=article]` inside the dialog; lazy-loaded (need scroll within dialog to load more). Comment text extraction + count TBD.
- **Detail scroll**: comments scroll within the dialog subtree (the dialog has its own scroll region), not window.

## Like post-action verification (task 3.2) — GROUND TRUTH STILL NEEDED
- The neutral like button = `aria-label="留下心情"`. The **exact "liked" state string** (after a successful react) was NOT captured (toggle probe hit a stale dialog). Expected: after react, the button's accessible name/text flips to the active reaction (text becomes `赞` in blue / aria-label changes). **Confirm during shadow (task 8.2)** on a disposable post: capture before/after aria-label+text, assert the flip; only `ok` on a real flip, else `no_target`. Do NOT rely on reaction-count increment (other users perturb it).

## Wide vs narrow layout (task 7.7 — user emphasized both)
> FB has xhs-like responsive breakpoints when the desktop window narrows. **With a desktop UA, a narrow window gives a condensed DESKTOP layout, NOT the mobile site.**

Clean single-navigate probes (desktop UA, env `k1ehveal`) at multiple widths:

| innerWidth | `role=feed` | hydrated `article` | `留下心情`(like) | `赞`(count) | right rail | left nav | notSupported |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1440 | ✓ | ✓ | ✓ | ✓ | ✓ | full labels | false |
| 900 | ✓ | ✓ | ✓ | ✓ | ✓ | **collapsed to icons** | false |
| 700 | ✓ | ✓ | ✓ | ✓ | ✓ | icons | false |

**Conclusion**: across 1440→900→700 the SAME width-agnostic selectors resolve — `role=feed` > `role=article`, the `留下心情` like button, and the `赞` reaction-count all persist. The chrome adjusts (left nav condenses to an icon rail ~900px; right rail stays) but the card/like DOM contract is unchanged. **No layout-specific fork is needed at the call site** (satisfies spec 7.7's "narrow resolves via the same selectors" + "duplicated wide/narrow control → pick visible").
- The ONLY way FB drops to the mobile layout (private glyph fonts, no `role=article`) is a **mobile UA** — eliminated by the desktop-UA env fix. So for FB, "narrow" ≠ mobile.
- **Probe hygiene gotcha**: rapid consecutive `Browser.setWindowBounds`+`Page.navigate` iterations (4 back-to-back) made the feed fail to hydrate (`feed:false` at ALL widths, incl. 1440) — a churn/soft-block artifact, NOT a real block. A single clean navigate per width + ~12s wait loads reliably. Space out real-machine navigations.
- Intermittent `/me` "这个浏览器不受支持" name is a first-paint interstitial the nickname probe reads before hydration; the feed itself loads fine (`notSupported:false`). Cosmetic; Change B's FB nickname probe should wait for hydration.

## Selector summary (edge `src/facebook/` targets)
| logical target | selector (DOM-first, width-agnostic) |
| --- | --- |
| feed | `div[role="feed"]` |
| feed scroll | window/document scroll |
| card | `[role="article"]` with author `h2/h3/h4 a` present (skip shells) |
| author | `article :is(h2,h3,h4) a` |
| permalink | `article a[href*="/posts/"], [href*="story_fbid"], [href*="/videos/"], [href*="/reel/"]` (strip `?`) |
| post like (feed & detail) | `[role=button]` in `{留下心情, Like, …}` whose action cluster contains a `发表评论`/comment sibling; pick visible/active |
| reaction count | `[role=button][aria-label="赞"]` with numeric text (NOT the toggle) |
| comment count | `[role=button][aria-label^="发表评论"]` text |
| detail open | navigate to permalink → `role="dialog"` |
| post body | `[data-ad-comet-preview="message"], [data-ad-preview="message"], div[dir="auto"]` |
