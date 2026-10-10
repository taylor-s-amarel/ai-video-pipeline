# Agent awareness feeds: design (10 October 2026)

**Baltor should make staying current a capability of the agent, not another reading assignment for the engineer.**

> Connect a project once. Its agents receive the relevant developments, understand what those developments
> change, and can retrieve the evidence, implementation material and tests needed to act.

This covers both "something may break" and "something useful has become possible": a new API, released
model weights, a better rendering method or a newly supported file format can unblock a project as
meaningfully as a deprecation can threaten it.

Status: design and local implementation. The interfaces below are proposals implemented in this repository;
they are not live baltor.ai endpoints. The original research packet described 62 source and connector
records, 32 proposed feed products and 36 proposed component contracts; those are researched interfaces and
proposals, not operational collectors.

## 1. Feed agents decisions and opportunities, not articles

| Layer | Contains | Contract |
|---|---|---|
| Source observation | What a publisher, repository, API or newsletter actually says | `awareness_source_observation` |
| Normalized event | The specific change, identities, versions, dates and evidence | `awareness_event` |
| Project implication | Why it matters to a particular project or task | `awareness_project_implication` |
| Permitted next step | A bounded investigation, test, proposal or no-action result | `awareness_next_step` |

A newsletter is a discovery source, not the authority on an API's behaviour. A release note establishes what a
vendor claims, not that the customer's workflow passes. Agents do not load every source into context: they
receive compact, task-specific packets (`awareness_packet`) and retrieve supporting material on demand.

## 2. Sources Baltor can consume directly

Software, models, APIs and infrastructure:

| Source family | Collection route | Extract |
|---|---|---|
| GitHub projects | REST with conditional requests; webhooks where authorised ([docs](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)) | Releases, documentation changes, issue resolutions, maintenance signals, exact versions |
| PyPI | Native RSS for new projects, new releases and per-project releases ([docs](https://docs.pypi.org/api/feeds/)) | Relevant packages and versions; enrich selectively |
| NuGet | Chronological JSON catalogue ([docs](https://learn.microsoft.com/en-us/nuget/api/catalog-resource)) | Creations, unlisting, relisting, deletions, metadata changes |
| Hugging Face Hub | Repository and org/user webhooks ([docs](https://huggingface.co/docs/hub/webhooks)) | Model, dataset and Space changes; refs and commits |
| Official MCP Registry | Read-only API with cursors and `updated_since` ([docs](https://modelcontextprotocol.io/registry/registry-aggregators)) | New servers, versions, deprecations, deletions |
| APIs.guru | REST plus added/updated feeds ([repo](https://github.com/APIs-guru/openapi-directory)) | API discovery and schema changes, traced to original sources |
| Google Cloud | Release-note feed and BigQuery access ([docs](https://docs.cloud.google.com/release-notes)) | Capabilities, availability, behaviour changes |
| Cloudflare | Global, product and API-deprecation feeds ([docs](https://developers.cloudflare.com/fundamentals/new-features/available-rss-feeds/)) | Workers, storage, AI, networking changes |
| Stripe, Shopify | Developer changelogs ([Stripe](https://docs.stripe.com/changelog)) | API-version changes and platform requirements |
| AI provider lifecycle pages | Deprecation documentation ([OpenAI](https://developers.openai.com/api/docs/deprecations)) | Announcement and retirement dates, replacements, prerequisites |

Notes that shape the collectors:

- The MCP Registry is built to feed downstream aggregators, but it is in preview, has no durability guarantee
  and asks for infrequent polling (for example hourly). Baltor keeps its own history.
- Hugging Face webhooks can arrive out of order, are retried, can be suspended after repeated failures and
  have quotas. Collection needs reconciliation and health reporting, not only a receiver.
- API definitions can feed implementation analysis: diff two OpenAPI documents (for example with oasdiff),
  report affected operations and propose contract tests. Community-contributed definitions, lag and
  undocumented runtime behaviour are handled separately.

Enrichment and decision sources: deps.dev and OSV ([deps.dev](https://docs.deps.dev/api/v3/)) for package
identity and advisories (a match triggers investigation, not a conclusion about exploitability); CISA KEV
([repo](https://github.com/cisagov/kev-data)) for known exploitation; endoflife.date
([repo](https://github.com/endoflife-date/endoflife.date)) for support windows; Azure, AWS and Google Cloud
price catalogues ([Azure](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices))
for SKU/region/unit changes (inputs to a scenario, not the customer's invoice); MDN browser-compat-data and
web-features ([repo](https://github.com/mdn/browser-compat-data)); provider status APIs
([GitHub Status](https://www.githubstatus.com/api)); arXiv, OpenReview and Crossref
([arXiv](https://info.arxiv.org/help/api/user-manual.html)); Comfy Registry and engine release sources
([Comfy](https://docs.comfy.org/registry/overview)).

These let the agent answer: does this affect our installed version, is it actually available, which workflow
depends on it, and what should we test?

## 3. Newsletters, LinkedIn, social posts and videos as input channels

Seed publications: Simon Willison's weblog ([site](https://simonwillison.net/)), Latent.Space, Ahead of AI
([site](https://magazine.sebastianraschka.com/)), TLDR ([site](https://tldr.tech/)), Changelog, JavaScript
Weekly ([site](https://javascriptweekly.com/)), Last Week in AWS. The Pragmatic Engineer is a candidate whose
inspected URL did not expose article text.

Ingestion: a dedicated feed address, an approved label in an existing mailbox, or an authorised reader
integration. Gmail watch/history supports incremental handling; the watch must be renewed at least every seven
days ([docs](https://developers.google.com/gmail/api/guides/push)). A newsletter item becomes: new claim or
lead -> original source -> entity -> project implication -> optional test. Subscription content stays
tenant-private.

LinkedIn's Posts API documents restricted member-read and role-limited organisation access
([docs](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)); there is no
unrestricted API for reading a personal feed. Support approved API access, publisher crossposts, permitted
notifications and deliberately shared references; never bypass login restrictions. Other routes with different
permissions and delivery: X filtered stream ([docs](https://docs.x.com/x-api/posts/filtered-stream/introduction)),
Bluesky Jetstream, Mastodon APIs, the Hacker News API and YouTube channel notifications. Social content
discovers; the agent follows it to the strongest evidence. A repost is not independent confirmation; a video
notification is not permission to download or republish.

## 4. Feed products organised around the agent's job

| Group | Question the agent answers |
|---|---|
| New capabilities | Can I now do something that previously needed custom code, an expensive service or manual work? |
| Previously blocked projects | Has the exact reason we postponed this changed? |
| Better implementation choices | Is there a simpler native feature, stronger library or better API to compare? |
| Models and local computation | Are usable weights available, and do they fit our hardware and quality bar? |
| Research becoming usable | Did the paper gain code, weights, a reproducible example or independent evidence? |
| Creative production | Can we now produce a required representation, keep editability or remove a bottleneck? |
| Compatibility and lifecycle | Which dependencies, endpoints, engines or models need review? |
| Costs and availability | Did a relevant price, region, quota, permission or tier change? |
| Customer and product opportunities | Is there a concrete new job, integration route or repeated problem? |
| Evidence and coverage | Was an earlier claim corrected? Is a critical source stale or inaccessible? |

The strongest product may be **revisit this decision**: remember why work was postponed ("the method produces a
flattened image, but we need editable vectors"; "no commercial-use weights"; "does not fit our GPU"; "no API
access"; "wrong region") and revisit only when evidence suggests the blocker changed
(`awareness_decision_record`).

## 5. Two worked examples

**Risk.** On 9 October 2026 Cloudflare documented changes to Markdown for Agents: in-process streaming
conversion, a larger decompressed-HTML limit, removal of `x-markdown-tokens` and `x-original-tokens`, and
removal of `Content-Length` from converted responses
([changelog](https://developers.cloudflare.com/changelog/post/2026-10-09-markdown-for-agents-in-process-conversion/)).
Packet: potentially affected are components that read the removed headers or assume a fixed length; check
code and configuration for those names; test that missing token metadata stays unknown rather than becoming
zero and that streamed content still obeys local size limits; opportunity: the larger input limit. Applicability
is unknown until code is inspected.

**Opportunity.** Google Cloud's 9 October 2026 release notes state that Datastream added replication of SQL
Server `GEOMETRY` and `GEOGRAPHY` types ([notes](https://docs.cloud.google.com/release-notes)). A stored
decision "we cannot use this replication route because it does not support the spatial fields" is matched and
a targeted schema-and-data test is proposed.

## 6. Media reconstruction feed profile

The video reverse-engineering swarm gets its own profile: observe the reference (segmentation, tracking, text
recognition, camera estimation, audio alignment), recover a representation (layers, vectors, geometry,
animation, scene programs), construct the project (native APIs, procedural generators, import/export),
run within constraints (hardware, weights, endpoints) and verify (benchmarks, editability, temporal checks).
Example packet: "This development may improve the camera-fitting stage. It does not solve rigging. Here are
the requirements and the smallest useful comparison." Comfy Registry versions/deprecations and Replicate's
model/version schemas are evidence sources, not proof that a workflow passes.

## 7. Capabilities underneath

- Collection and change detection: native-feed discovery, incremental APIs, webhooks, permitted page-section
  comparison, newsletter parsing, repository/model metadata adapters. Feedly, Inoreader, Miniflux, RSSHub and
  changedetection.io already exist, so "RSS connected to an agent" is not differentiation by itself.
- Meaning and applicability: exact entity resolution, change classification (NuGet unlisting is not a
  release), original-evidence tracing, project matching. Published, source-updated, observed and effective
  dates stay separate.
- Decision support: capability cards, compatibility warnings, migration tests, example requests, benchmark
  fixtures, candidate adapters. **Agent Feeds identify what deserves consideration; Harness Files supply the
  material to carry it out.** Publication of a component remains a separate qualification step.

## 8. Quiet, task-aware delivery

Delivery moments: task start, task resume, an important tool or provider choice, and a bounded periodic
review. Interface (proposed): `feeds.changes(scope, cursor, token_budget)`, `feeds.explain(event_id,
project_scope)`, `feeds.evidence(evidence_ref)`, `feeds.revisit(decision_id)`, `feeds.coverage(scope)`, plus
`feeds.respond(event_id, action)` for not relevant, already handled, hold and no action needed. Notifications
carry references; agents expand within budget. Public collection is separate from tenant-private matching.
Reading automatically never implies changing production automatically: collection, analysis, testing and
change proposals are separate permissions.

## 9. Source health is part of the product

Visible states: no new items, collection failed, parsing failed, access expired, source withdrawn, webhook
suspended, coverage incomplete. Durable checkpoints, acknowledge after saving, reconcile missed and out-of-order
events, propagate corrections; deduplication does not make external actions exactly-once. External content is
inert: it never gains authority to reveal credentials, run commands or change agent policy.

## 10. Growing to thousands of sources

Follow relationships: package -> repository -> releases -> documentation; model -> card -> paper -> code ->
weights -> evaluation; API directory -> original schema -> changelog -> SDKs; creative workflow -> nodes ->
runtime -> models; customer problem -> workaround -> maintained implementation -> updates. Qualify a candidate's
identity, access route, parser, update behaviour and contribution before maintaining it. Ten topic filters over
one changelog are not ten publishers; 1,000 personalised feeds are views over one evidence base. Cadence is
source-specific (MCP Registry: infrequent; arXiv: its documented request spacing).

## 11. Commercial test

Offer "maintained awareness for your project", not "access to more news". Test with two customers that have an
explicit stack, unresolved decisions and acceptance tests: a software/API project and the media-reconstruction
workflow. Compare an existing reader or summary, the customer's current agent, and the same agent with
Baltor's project-matched packets. Measure important developments found, useful capabilities surfaced,
irrelevant interruptions avoided, decision quality, missed events, source failures, analysis cost and
unnecessary recommended work. This remains a hypothesis until demonstrated (see `showcases/`).
