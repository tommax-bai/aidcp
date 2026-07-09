# Facebook Group, Search, and Post Access Probe Findings

Date: 2026-07-06

Probe environment:

- AdsPower profile: `k1ebny3j`
- State: logged-in candidate after manual challenge handling
- Main probe artifacts: `/tmp/aidcp-fb-group-search-probe-2026-07-06T06-46-49-353Z`
- Post access/expand probe artifacts: `/tmp/aidcp-fb-post-access-expand-probe-2026-07-06T06-49-40-645Z`
- Probe mode: read-only navigation, DOM inspection, one non-writing expand click

No comments were submitted. No credentials, cookies, tokens, storage values, user names, search result text, or post body text were saved.

## Summary

Facebook Group navigation and search are feasible through URL-first flows, but Group commenting must remain blocked until membership/permission state is proven.

Key findings:

- A group can be entered by slug URL or numeric id URL.
- Slug and numeric group landing pages can render different levels of feed/editor surface.
- Group post permalinks work in both slug form and numeric `multi_permalinks` form.
- Direct Group search URL works and exposes post result links.
- Global group and post search URLs work and expose group/post result routes.
- Group pages/posts in this sample still showed `加入` / `加入小组`, so Group comment submit is not safe.
- A generic "expand" click can hit unrelated controls such as `查看更多探索内容`; body expansion must be scoped to the main post article.

## Group Entry

Observed routes:

```text
https://www.facebook.com/groups/facepagerusers
https://www.facebook.com/groups/136224396995428
```

Both entered the group while logged in. The slug page showed fewer surfaces than the numeric id page:

| Route | Articles | Editors | Notable Controls |
| --- | ---: | ---: | --- |
| slug group landing | 3 | 0 | `加入小组`, `在小组内搜索`, `发表评论`, `展开` |
| numeric group landing | 6 | 2 | `加入小组`, `在小组内搜索`, `发表评论`, editor controls |

The runtime should preserve both requested and discovered canonical identifiers:

- slug candidate: `facepagerusers`
- numeric id candidate: `136224396995428`

## Group Post Access

Observed equivalent post routes:

```text
https://www.facebook.com/groups/facepagerusers/posts/1038125326805326/
https://www.facebook.com/groups/136224396995428/?multi_permalinks=1038125326805326
```

Both reached a post/detail surface and exposed:

- article containers
- comment/reply controls
- one visible textbox/editor
- group join signal

The post page exposed additional numeric group id candidates through links. Some candidates may belong to related/recommended content, not the current post. The parser must prefer ids from current-post timestamp/header links and avoid blindly accepting every `/groups/<id>` link on the page.

## Search

### Group Internal Search

Direct route worked:

```text
https://www.facebook.com/groups/facepagerusers/search/?q=links
```

Observed:

- search result articles: `6`
- group-specific search input: `aria-label="搜索这个小组"`
- filters such as `帖子来源` and `标记的地点`
- result post link patterns like `/groups/facepagerusers/posts/<post-id>/`

This route is preferable for the first implementation because it avoids simulating the top search box and gives scoped group results.

### Global Group Search

Direct route worked:

```text
https://www.facebook.com/search/groups/?q=facepager
```

Observed:

- result articles: `2`
- global search input: `aria-label="搜索 Facebook"`
- filter switches such as `公开小组` and `我的小组`
- result controls included `加入小组...`

Global group search can discover group candidates, but the driver must distinguish result group links from join buttons.

### Global Post Search

Direct route worked:

```text
https://www.facebook.com/search/posts/?q=facebook%20posts%20links
```

Observed:

- result articles: `6`
- result link patterns:
  - `/groups/<numeric-id>/?multi_permalinks=<post-id>`
  - `/<page-or-profile>/posts/<post-id-like-token>`
  - `/search/posts/?q=...`
- several results showed `加入`, so membership gating still matters.

## Search Result Post Access

A post URL discovered from Group internal search was directly accessible:

```text
https://www.facebook.com/groups/facepagerusers/posts/1399888000629055/
```

Observed:

- final URL stayed on the slug post permalink
- title indicated a Group post detail surface
- article body was present
- editor existed with `aria-label="输入回答…"`
- `加入` was still present
- no login or unavailable state was detected

This confirms a URL-first search-to-post flow is feasible:

1. Navigate to Group search URL.
2. Extract result post permalinks.
3. Navigate directly to the selected post permalink.
4. Run blocking, membership, and editor probes before any interaction.

## Expand and Body Reading Caveat

The post access probe clicked an expand-like control labeled `查看更多探索内容`. It disappeared after click, but the main article text length did not change. This was not a main-body expansion control.

Implementation implication:

- Do not click every `查看更多` / `展开` control globally.
- Scope expand controls to the selected main post article.
- Re-measure the same article text length after click.
- Treat unchanged length as `expand_no_effect`, not success.

## Remaining Probe Needs

Before Group comment submit is considered:

1. Membership classifier:
   - `加入`, `加入小组`, `已加入`, `待批准`, `回答问题`, unavailable/private states.
2. Group internal search UI typing probe:
   - only needed if URL-first search is insufficient; direct URL search is enough for the first implementation.
3. Main-post scoped expand probe:
   - identify current post article and click only expand controls inside it.
4. Group editor permission probe:
   - determine whether `输入回答…` is a real comment editor, a membership-question input, or a restricted interaction surface.
5. Gated submit probe:
   - only on an operator-controlled disposable test post.
