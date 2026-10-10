# Creative Media and Game Production Reference

Version 1.0 · 10 October 2026 · Private reference

Current creative direction includes the 09:26 UTC correction: realistic, large photography covering most of the frame. The new illustrated story treatment was rejected; its technical evidence remains in the history.

This handbook brings together the creative strategies, reusable source kits, animation methods, speech systems, research, rendering procedures and game assets considered or used across this project. It is designed to help choose the right existing route, understand what has actually been demonstrated, and make the next production more reliable.

The strongest established route for frequent short-form work is the existing CPU composition pipeline: realistic original or authorized imagery where requested, explicit frame timelines, measured natural-speed narration, independently moving backgrounds, crisp text, checkpointed encoding and exact deliverable verification. Native Blender and Godot add genuine geometry, animation and interaction where those capabilities matter. The earlier stick-figure work and open-source animation research remain useful, but their evidence is different from the later completed film receipts.

This is an inventory and practical handbook, not an instruction to install every candidate or rebuild working systems. New generative-video options are explicitly separated from historically considered tools. An open-source engine does not make every model, voice, texture, photograph or soundtrack open source.

## Contents

1. Evidence and status language
2. Fast decisions by intended result
3. Existing reusable production systems
4. Current photographic contract and illustrated-story history
5. Background architecture and layer controls
6. Animation methods from 2D to native 3D
7. Speech, captions and music
8. Practical production recipes
9. Research and editorial methods
10. Rendering costs and capacity
11. Quality and acceptance
12. Recovery and reproducibility
13. Rights and source admission
14. Baltor interfaces and reusable capability design
15. Open-source video production and new model candidates
16. Cheap experiments and next questions
17. Historical animation repository and game asset ledger
18. Selected artifact and source register

## 1 Evidence and status language

Use several status fields, rather than a single “done” badge.

| Term | What it establishes | What it does not establish |
|---|---|---|
| Considered | Named or reviewed as a possible route | Installation, execution, suitable output or rights clearance |
| Source inspected | Specific code, license, configuration or archive inspected | That code ran successfully |
| Installed | A binary, package or model is present at a known version | Runtime compatibility, successful render or visual quality |
| Isolated execution | A bounded run happened in a separate test/project environment | Live integration or general portability |
| Headless tested | Logic, import, physics or rendering ran without the ordinary interactive GUI | Human controls, editor ergonomics, real graphical playback or gameplay capture |
| Graphically checked | A specified native window, capture or visible output was inspected | Every interaction or frame, unless explicitly covered |
| Encoded and decoded | The full media stream is structurally readable with measured dimensions and timing | A good story, audible pronunciation, seamless motion or owner acceptance |
| Sampled visual review | The named output frames or temporal samples were viewed | Uninterrupted real-time viewing |
| Delivered | The exact file was saved and the delivery route accepted it | That the recipient opened, liked or accepted it |
| Owner accepted | Explicit approval of the stated item or feature | Approval of all later revisions, rights, publication or software behavior |
| Rejected | A specified creative or technical criterion failed | That every part of the artifact is unusable |
| Blocked or unverified | A concrete missing dependency, permission, input or evidence remains | That the route is impossible in every environment |
| Rights unknown | Evidence is insufficient for the proposed use | That the material is necessarily infringing, or that private access authorizes redistribution |

A source archive, a master, a compact copy and a contact sheet are four artifacts for one film. Fifteen treatments of one narration are fifteen edits of one story, not fifteen independent researched stories. Presets, scenes, diagnostic loops and source templates are not automatically finished films.

### Evidence precedence

For conflicting records, use the latest exact artifact receipt and its stated scope, then the actual source/configuration, then dated validation records. Historical summaries and project-site text are useful discovery evidence but can overstate completion. Do not silently erase disagreement. A partial MP4, a successful source test or a plan promising a trailer cannot prove the trailer exists.

The current contract below supersedes earlier neon-header, 88%-photo, opaque-text and mid-frame-title defaults in historical source guides. Those older designs remain reusable historical variants; they are not the present default.

## 2 Fast decisions by intended result

| Intended result | First existing route to inspect | Why it fits | Main remaining check |
|---|---|---|---|
| Narrated portrait or relationship short | Current large-photo compositor | Existing 60–103-second films, natural-speed Kokoro, timed captions, moving margins | Subjective voice review and current owner style approval |
| Original stick-figure comedy or action | Recover Final Boss/Kinetic source; deterministic skeleton route | Pose readability, inexpensive revisions, explicit story beats | Original engine/source accessibility; do not rebuild from title alone |
| Illustrated person who actually walks | After the Rain mesh source | Two-bone IK, textured triangles, planted-foot handling, secondary motion | New character atlas/rig fit and full motion review |
| Gentle movement in a still portrait | A Passing Breeze CPU mesh source, when permitted | Small, local mesh deformation | Likeness/asset permissions, tearing and expression stability |
| Accurate science or algorithm explanation | Analytic geometry plus eight-format templates | Exact quantities and reproducible visual states | Scientific assumptions, code-to-picture consistency and perceptual clarity |
| Fast atmospheric moving background | Cinematic Background Factory / current procedural layers | Seekable deterministic scenes, palettes, independent clocks | Loop seam, contrast and visible motion under foreground |
| True 3D environmental film | Moonlit Range Blender source | Real camera, geometry, water and light animation | Render budget, noise/flicker and shot quality |
| Playable game or room interaction | Exact Godot project/asset integration | Native scenes, controllers, collisions, reset lifecycle | Actual graphical controls and supported capture on the target machine |
| Repository or product walkthrough | Genuine supported screen capture plus editorial cuts | Preserves actual UI interaction and source provenance | Readable pacing; no invented UI or implied execution |
| Mixed-media episode with different sections | Story Composer 1.0 | Images, checked movies, groups, type, masks and inherited settings | Exact schema, media/color support and source bindings |
| Local authoring UI | Frame Foundry 0.2 source | Backend and guarded-frame work exists | Browser interactions/full-film wrapper remain unqualified at recorded version |
| Diffusion-generated video shot | Separately qualified model workflow | Potential for motion unavailable from simple composition | Hardware, weights/terms, temporal identity and exact reproducibility; no current production qualification |

### Decision tree

1. Does the viewer need to see a specific physical interaction or control response?
   - Yes: use native game/3D or a tested skeletal/mesh animation route. A zoomed still cannot stand in for an animated hand, nod, walk or collision.
   - No: image-plane composition may be sufficient.
2. Must the frame express exact quantities, a source-code step or a factual comparison?
   - Yes: prefer deterministic geometry and explicit labels tied to source evidence.
   - No: original procedural or generated illustration may provide atmosphere.
3. Does an existing source already produce the required outcome?
   - Yes: reuse it unchanged first, then make one bounded revision.
   - No: compare the simplest direct implementation with one candidate kit before creating a new abstraction.
4. Does the whole story run at least 60 seconds and resolve an arc?
   - No: it is a production test, animatic, loop or excerpt. Keep that label.
   - Yes: continue full-film QA; duration alone still does not establish a complete story.
5. Are rights, source identity, playback and delivery evidence adequate for the intended audience?
   - No: hold that release stage and specify the missing evidence.
   - Yes: private review may proceed. Publication remains a separate decision.

## 3 Existing reusable production systems

### 3.1 Kinetic Remix Lab and the early baseline

The historical project names include Kinetic Remix Lab, `remix_engine.py`, Effect Atlas and Signal Garden. Their legacy Library references are:

| Historical reference | Library identity | Current evidence |
|---|---|---|
| Kinetic Remix Lab / engine | `libfile_ba61b1c150748191bb4efde53f64fa06` | Referenced in history and later reuse reviews; direct source was not recoverable in this audit |
| Effect Atlas | `libfile_447547e123fc81918b70d2b64685f9e6` | Historical effect reference; direct source not recoverable |
| Signal Garden | `libfile_7284141738f48191b4774763ca9ae4e7` | Historical baseline to preserve; direct source not recoverable |

The same accessibility limitation was recorded in AV-20261005-076. This handbook preserves those identities instead of asserting that later factories are byte-for-byte reuse of unavailable source. The recovered conversation describes a liked 70-second stick-figure short, Final Boss: The Door. Treat its story/style history as recovered evidence, and its exact current film/source bytes as a recovery task unless a receipt identifies them.

### 3.2 Cinematic Background Factory

Recorded source: `Cinematic_Background_Factory_Source_and_Presets_v1.zip`, Library `libfile_c81461d095b48191adfca346c531557d`, version 0, SHA256 `49655e8cdc4e4f3c83e286c8f3d888003c789708e153277e0ffa4b4b65ab98da`.

Implemented original layered 2.5D scenes:

- Ember Archive: warm arcades and particles
- Moonlit Range: mountains, lake and pines
- Golden Sky: clouds and an imaginary monument

The frame API supports deterministic seed, arbitrary seek order, palette, layer/camera motion, speed, loop duration, protected text area and contrast. Three 12-second 1080×1920 loops are production assets. The 60-second sampler has deliberate chapter cuts and is not a seamless loop or a third researched history story. The first batch passed bounded technical checks but received negative owner feedback on background quality, leading to layer-by-layer polish.

Reusable principle: separate silhouette, atmosphere, light, reflection, particles and typography so each weakness can be improved without changing the entire composition. A text-protection mat does not certify arbitrary caller text.

### 3.3 Layered lake routes

Two distinct systems exist:

- Layered 2.5D lake: image/shape planes, parallax and composited atmosphere. Moonlit Range 66-second full film source is `libfile_e1c7fbd937508191a88cdd109595986d`, v0. The three-style factory source is `libfile_6d9442214304819196f55ecc2df2b257`, v0.
- Native 3D lake: Blender Cycles CPU, actual water surface shape keys, moving ripple normals, camera glide, keyed lights/sky and depth-derived haze. The original completed 66-second 540×960 film is `libfile_32ce533cb0488191b43b456f1be80e05`, v0. Source/recovery archive is `libfile_a31e5c2e0b1c819191141357cd2d11c5`, v0.

The 3D source establishes real geometry and all-frame rendering. It does not establish a real-place scan, interactive game or 1080p native detail. Later polish and improved versions must be selected by their own receipt, not the oldest baseline.

### 3.4 Video Recipe Factory 2.1 and shared motion

`Video_Recipe_Factory_v2_1_Editable.zip`: Library `libfile_9d157cd0e12c8191b1dfefba33d73b7a`, Library version 2. Package version and Library version are different fields.

The same motion helper was used in a complete 60-second Small Things v4 film and the factory. Helper SHA256: `d139be5a6994c937989709b25433c6c86120142aa4e487e6dcef8cde0aaa6a83`.

Recorded controls include lake glide/arc/sweep camera presets, held or scroll-up-then-hold text, and legacy/gentle-parallax/portrait-depth foreground modes. The first hook is settled on frame zero; scrolling text holds at least four seconds; the final card does not disappear into a terminal exit. Twelve helper tests overlap the 72-test factory suite and must not be added as a second unique test total.

The local settings editor exports JSON. Its presence is not browser-interaction qualification. Short 6- and 8-second internal excerpts tested motion; they are not additional completed 60-second factory films. The actual complete consumer is `libfile_b8d0e271e464819184eeb6764bc3febe`, v0, with source `libfile_465c07a422e881919670aea247c194b1`, v0.

### 3.5 Layered Stories and Story Composer are distinct contracts

The earlier Layered Stories guide appears in the supplied `Pasted text(1).txt`, Library `libfile_3f7f878b130481918fe7227d6fc05f6f` (no Library version exposed). It describes typed image/video/text/shape layers, rational clocks, masks and strict local asset admission. It explicitly lacks generic blur, shader blend modes, live engine execution and arbitrary audio mixing.

Story Composer 1.0 is a later, separate delivered system. Full source: `libfile_c9b24282c8908191ad242cca5ba330b8`, v0. Compact source: `libfile_e5a0a9d00f6481918cad9c5309bde061`, v0. The complete 64-second example, The Window Maker, is `libfile_b0eaf47058848191b6484ad1b314a94b`, v0.

| Area | Story Composer 1.0 recorded support | Boundary |
|---|---|---|
| Structure | Episode → contiguous sections → layers/groups; persistent overlay scope | Exact hierarchy and defaults matter |
| Media | Verified images, opaque movies, rendered-scene media, audio and fonts | Native `.blend`, Godot or Babylon projects are not executed by the compositor |
| Geometry | Normalized box/crop; contain/cover/stretch; focal alignment; rotation/scale/position/size tracks | No arbitrary executable expressions |
| Alpha | Straight/premultiplied image handling; isolated groups | Output MP4 is opaque; transparent RGBA PNG is supported |
| Blend | Normal, multiply, screen source-over | Do not infer soft-light or arbitrary shaders |
| Masks | Rectangular, rounded, elliptical; clipping | No raster/luma/depth/shader mask adapter |
| Timeline | Integer frames, half-open intervals, hold/linear/smoothstep | This recorded version accepts exactly 24/1 fps |
| Media color | Explicit admitted 8-bit limited-range YUV interpretation and conversion | HDR, alpha video, contradictory tags and unsupported full-range/RGB rejected |
| Sound | Explicit music fades/mix; timed story-card SRT | Story cards are not word-aligned spoken subtitles |
| Inheritance | Style → episode → section → layer; objects merge, arrays replace | Array replacement must not accidentally drop required overlays |

Its clean package replay checked 48 payload hashes, 34 packaged tests and a known frame hash. The film had 1,536 decoded unique frames and zero adjacent duplicates. Neither proof implies live Blender/Godot adapters or recovered exact neon Girl Facts source.

### 3.6 Local Video Factory and Frame Foundry

- Local Video Factory 0.1 full source: `libfile_3f73d2ee206881918cb5acc9717c1135`, v0
- Compact source: `libfile_f15a107e9f588191b026430000bd4705`, v0
- Frame Foundry Studio 0.2 app source: `libfile_e83984f5d2ec81918a963a42b8d36a2b`, v0

The recorded CLI had 17 frame smokes across five source families, pinned vendor files, tests and a relocated matching-frame reopen. The compact archive omits 25 assets and requires exact restoration; small does not mean self-contained. Studio had backend tests, proof images and one real guarded frame. Browser startup was blocked before navigation, full-film wrapper execution was disabled, and HD/4K/narration requests were typed planned intents rather than qualified outputs. Reuse the backend evidence without calling the UI or all wrapper films production-ready.

### 3.7 Eight original format templates

The 72-second showcase and compact source establish one complete showcase, not eight finished individual episodes.

| Template | Demonstrated content | Semantic boundary |
|---|---|---|
| Algorithm/code | Legal five-disk Hanoi sequence | 2.5D disks, not a volumetric model |
| Signal console | Simulated traces and dashboard | Simulated data, not live telemetry |
| Search comparison | A* vs greedy on one grid | 21 vs 23 steps, 75 vs 29 visited cells are one case, not universal superiority |
| Pipeline | Batch vs ongoing stream | Conceptual movement, not measured system latency |
| Science poster | Force/motion relationships | Static carts with emphasis, not a physical trajectory simulation |
| Quiet list | Original communication guidance | Advice, not empirical behavior findings |
| Editorial graph | Nodes/messages | Not a trained graph-learning model |
| Urban story | Original fiction with source-tracked city art | Illustration, not authentic recorded urban activity |

Compact source: `libfile_8a2a93f854fc8191a3b0f54cbba7e308`, v0. Showcase: `libfile_dc9ff54256cc819185cc850176d165ec`, v0. The recorded full source was v3 at `libfile_6310e7fd28988191ba04a47293c903df`. Restore its exact WAV from included lossless FLAC with the supplied utility before rendering; this is decompression, not fresh speech synthesis.

## 4 Current photographic contract and illustrated story history

### 4.1 Global rules

- Every finished video is at least 60 seconds and has a complete story, explanation, gameplay sequence or trailer arc.
- Keep large imagery dominant. Do not shrink the photo to manufacture a separate title zone.
- For the current photographic pair, canvas is 1080×1920 and photo bounds are `(54,96)` to `(1026,1824)`: exactly 972×1728.
- The 5% inset is per side. The photo occupies 90% of width and height, or 81% of canvas area; 19% remains outside its rectangle.
- Keep the exposed border visibly moving from the first frame through the ending.
- Each authored/composited visual layer must remain at or below 98% opacity. The conservative 8-bit cap is 249/255, approximately 97.65%.
- Use feathered edges, low clutter and independently moving backgrounds. A flat black margin or a frozen background fails the visual intention even if the foreground moves.
- Use a short, bold yellow/orangish-yellow editorial title over the upper photograph, around y=320. The editorial title is distinct from faithful narration captions.
- Preserve meaningful framing, faces, eyes, hands, props and any required image coverage through every crop/motion state.
- Real frosted backing samples and blurs the current underlying composite. A translucent solid rectangle by itself does not meet that requirement.

### 4.2 Latest verified baseline and current revision

The v7 source manifest records two complete 66-second films with the five-layer/four-panel treatment:

| Film | Compact Library identity | Library version at v7 receipt | SHA256 |
|---|---|---:|---|
| Ever Felt Misunderstood | `libfile_35a73062b0d48191a9493c2e8605661c` | 5 | `ae85d3d9e1abebc77749d80a74646f5f025b61a381109dd6e3b1da1c425450cd` |
| When They Go Quiet | `libfile_bf9d4ca4e1fc81919968acd4e78973b5` | 2 | `8bea377e1c5c041bbd511f177a7e197184016f9df16332a0ad15778de5523866` |

These are pinned historical baseline versions, not a claim that a later update cannot exist. The v8 source adds genuine sampled glass. Its source/preflight evidence is covered here; final v8 delivery must be established by a terminal film receipt. Full decode, caption/timestamp checks, sampled visual/temporal review and exact Library readback passed for v7. Those checks do not imply owner final acceptance, listened audio or unrestricted public-image rights.

### 4.3 Exact title geometry retained in the photo pair

| Film key | Title lines | Font | Glyph bounds | Hold end |
|---|---|---:|---|---:|
| clear | FEELING / MISUNDERSTOOD? | 72 px bold | x162–917, y246–394 | 3.6667 s |
| room | WHEN THEY / GO QUIET | 72 px bold | x295–785, y241–399 | 3.7083 s |

Both glyph boxes center at about y320. Text uses a dark outline and controlled shadow. Glass fits behind these existing positions; the photo does not change size to accommodate it. Earlier mid-frame and reserved-empty-title-zone directions are superseded.

### 4.4 Current realism preference and the rejected illustrated treatment

At 09:26 UTC on 10 October, the owner rejected the new illustrated News/Job look because the images were not realistic and did not occupy enough of the frame. The current direction is realistic, large photography with the established 972×1728 photo footprint and dominant coverage. Keep the upper yellow title, real frosted backing, moving border and five-layer/four-panel system. Photorealistic replacements were being prepared at this snapshot; they are not completed deliverables in this handbook.

Who Gets to Tell It? had already completed a technically qualified 68-second illustrated export, but it is creatively rejected. The illustrated Take the Whole Job master is being preserved; compact encoding and delivery are held. The following records describe that preserved implementation, not the accepted default.

Who Gets to Tell It? and Take the Whole Job are original fictional scenarios about permission to share news and owning a complete household task. Their scripts avoid factual claims about all men, women or couples. The preserved production contract specifies 68 seconds, 1,632 frames at 24 fps, natural-speed narration and measured pauses.

The artwork consists of generated still vignettes with consistent adult character references. The generation tool is proprietary, not an open-source model. Transparent PNG files can contain faint near-zero-alpha speckles outside visible art. Placement therefore uses alpha-128 content bounds plus padding, rather than the raw nonzero-alpha rectangle. The source pixels remain preserved. The current prepared art uses a 1050×1830 transparent canvas with content positioned around y240; a 40-pixel placement correction protects an opening eye without reducing the art to reserve title space.

Camera/framing motion and original animated story graphics are implemented separately. A script beat saying “thumb approaches,” “nods” or “lifts a phone” is not proof that still character art performs that motion. The final representation must state which movements actually exist.

## 5 Background architecture and layer controls

### 5.1 Implemented five-layer foundation

Order is back to front. Values below come from the current photo-film layer contract.

| Layer | Role | Maximum recorded alpha | Important behavior |
|---|---|---:|---|
| Continuous full-frame background movie | Base moving fluid-light field | 247/255 | Covers the full canvas, including exposed border |
| Translucent blurred moving layer | Soft depth/flow | 51/255 | Clipped to the 5% inset in this implementation |
| Animated perspective grid | Structural depth cue | 31/255 | Continuously changes; not a static decorative grid |
| Slow color haze | Atmospheric separation | 31/255 | Independent low-frequency movement |
| Drifting particles | Fine depth cue | 63/255 | Controlled density/contrast |

“Original fluid-light movie” describes the procedural asset. Do not call waves or gradients recorded ocean footage.

### 5.2 Implemented independent 2×2 panels

All four effects occupy one quadrant below the main photo, with 28-pixel feathered seams in the current code. This is different from the reference sheet's proposed 48–96-pixel range.

| Panel | Bounds | Effect | Clock scale | Offset | Initialization |
|---|---|---|---:|---:|---|
| Top left | 0,0 to 540,960 | Flowing wave field | 0.64 | 0.0 s | Deterministic geometry/phase |
| Top right | 540,0 to 1080,960 | Moving depth grid | 0.91 | 3.7 s | Deterministic geometry/phase |
| Bottom left | 0,960 to 540,1920 | Drifting defocused lights | 0.53 | 8.4 s | Seed 509 |
| Bottom right | 540,960 to 1080,1920 | Ribbon and particle flow | 1.07 | 13.2 s | Deterministic geometry/phase |

The local alpha limit is 122/255 and final panel-layer maximum is 119/255. Only the defocused-light panel uses a numeric random seed. It would be inaccurate to describe all four as independently seeded. Independence comes from distinct functions, speeds and offsets, not merely four copies of one synchronized clip.

Existing motion evidence includes two 4-second frozen-photo controls, each decoded as 96 frames, with isolated panel changes and temporal visual review. A static four-panel diagram alone does not establish this behavior.

### 5.3 Genuine frosted glass

Current implementation sequence:

1. Obtain the actual text glyph rectangle without moving the text.
2. Pad it and clamp the backing inside the approved composition.
3. Sample the current composite, including what is visibly underneath that text, with a 48-pixel blur margin.
4. Apply Gaussian blur radius 18 pixels.
5. Crop back to the fitted backing; add a restrained dark/cool tint and small pearl lift.
6. Use a rounded mask with 2.2-pixel feathering, then apply the layer opacity cap.
7. Composite a faint, softened rim.
8. Draw sharp text above it.

The mask's raw maximum is 228, while the applied glass maximum is 223/255 after the 0.98 cap. That distinction prevents an apparent inconsistency. A recorded blurred-vs-unblurred pixel difference is a useful implementation check, but the backing also needs visual review against bright, detailed and dark moments.

This glass serves opening titles, faithful captions and music credits. Its source function SHA256 is `58f43fccb2bad83888964c97681288a719edd17b74a836cc853bce285be76338`. It does not require scaling the photo, moving the title or replacing the current underlying scene with a generic blurred stock plate.

### 5.4 The proposed 30-slot background architecture

The six-page reference book is Library `libfile_faf334985ee08191914392c50d7f0a12`, v1. Its 36-look atlas and 30-slot stack are static design references, not 36 actual movies or a fully implemented 30-layer engine.

| Group | Slots and possible responsibilities |
|---|---|
| Base 1–4 | Base color field; primary moving movie; soft moving duplicate; secondary color flow |
| Atmosphere 5–9 | Low fog; high haze; aurora/ribbons; far dust; near particles |
| Structure 10–14 | Perspective grid; contour waves; dot matrix; wireframe flow; scan sweep |
| Texture 15–18 | Fine grain; paper/fabric detail; analog scratches; glass/frost detail |
| Four panels 19–22 | Top-left, top-right, bottom-left, bottom-right independently clocked sources |
| Light 23–26 | Bloom; edge light leak; rays; lens reflection |
| Finish 27–30 | Shared color glaze; luminance guard; soft edge vignette; final background mix |

The conceptual background frost slot is separate from text-local genuine backdrop glass. Thirty available slots should not mean thirty competing active effects. The reference suggests starting with four to eight active choices; the current five-plus-four implementation already has a specific audited stack. Alter that only for a concrete visual benefit and compare against its baseline.

The four visual directions are Ocean Glass, Aurora Editorial, Warm Cinema and Signal Space. They describe color/atmosphere recipes, not actual ocean footage or newly rendered native 3D worlds.

### 5.5 Controls every reusable layer should expose

A useful proposed cross-renderer layer description records source identity, rectangle, z order, active frame interval, local clock, crop/fit/anchor, opacity, alpha convention, feather/mask, blend operation, color intent, seed when used, motion amplitude, motion frequency, phase, safe/protected regions and output audit identity.

That is a design checklist, not a claim that every historical schema accepts those exact keys. A renderer must reject unsupported keys rather than silently ignore them. Keep independent clocks seekable: asking for frame 100 before frame 10 should not change either frame. Separate background movement from camera movement, character deformation, caption timing and encoding.

## 6 Animation methods from 2D to native 3D

### 6.1 Deterministic stick figures and skeletal motion

A stick figure is a compact performance system: joints, bones, constraints, poses, timing and contact. The strongest reusable approach is a small explicit rig, a pose library, semantic action phases and deterministic interpolation. A rendered head/body/limb hierarchy is more controllable than repeatedly asking a generative model for matching poses.

Useful phases for a short comic action: anticipation → attempt → contact → reaction → escalation → reversal → resolution. Pose silhouettes should remain legible without facial detail. A prop such as a door should have a fixed pivot, collision/contact target and state timeline, so the joke does not depend on limbs passing through it.

Inverse kinematics is appropriate for hands on a handle and feet on the floor. A 2D rigid-body engine adds falls, swinging doors and prop interactions when those physics improve the story. It is unnecessary overhead for a simple authored pose sequence. The historical Fullik, Planck.js, Rapier and Motion Canvas candidates are mapped in the repository ledger; consideration is not evidence that those engines made Final Boss.

### 6.2 Cutout and textured mesh puppetry

After the Rain's detailed revision is a concrete demonstration: 590 character vertices, 710 triangles and 12 layers; two-bone linear-blend skinning/IK; a 62% stance and 38% swing gait; camera-compensated planted-foot targets; head, torso, hair and coat secondary motion. Its umbrella uses a 34-vertex, 32-triangle articulated canopy with carefully controlled shaft/hand/torso ordering.

This is 2D/2.5D textured mesh animation. A character walking over a layered street has genuine mesh motion without being a volumetric human model. Its source is `libfile_8f3b611a913481918cfa3e2ac217d47e`, v0, and full film `libfile_a0ed510093188191a57e65f12ea939ba`, v0.

Reusable checks: bone lengths, weight normalization, triangle inversion, limb attachment, planted-foot drift, hand/prop contact, alpha halos, front/back ordering and deformation of important facial details. Camera motion must be included in foot-plant calculations, or apparently stationary world-space feet slide in the image.

### 6.3 Subtle photo mesh motion

A Passing Breeze uses a CPU 2D mesh over the supplied portrait. The 64-second film is `libfile_16473f6fdda88191ba1957f5f399f4dd`, v0; source/proof `libfile_72db3c180a6c8191be3920dba7e501e8`, v0. The neutral frame matched the Lanczos-resized source exactly.

This route is useful for local cloth/hair/background motion with restrained deformation. It is not a substitute for a full acting rig, physically accurate depth or permission to alter a real person's likeness. Keep an undeformed reference and test high-frequency regions, face landmarks and occlusion boundaries. It was independently implemented; do not attribute it to an upstream mesh-avatar studio merely because that studio was also researched.

### 6.4 2.5D parallax and camera planes

Separate foreground, midground, distant landscape, atmosphere, light and particles. Move near planes more than distant planes, keep enough overscan to avoid exposed borders, and coordinate color/contrast so depth remains readable. A camera over flat planes is still 2.5D. Multiple color grades of one lake do not create new locations.

The main benefit is controlled motion at relatively low cost. The limit is parallax disocclusion: moving a cutout reveals missing pixels. Avoid large lateral moves unless background plates or modeled geometry genuinely fill those regions. The current photo films intentionally use conservative whole-image motion rather than claiming body animation.

Cedar Vale also demonstrated a depth-projection route: six native Cycles color/depth masters produced 1,440 2.5D composites for a 60-second film, not 1,440 newly rendered native 3D views. The encoded file had 1,432 unique frames and eight adjacent repeats. Disocclusion filling extended adjacent farther pixels rather than reconstructing hidden geometry; room motion was reduced to 30% to limit silhouette artifacts. Film: `libfile_a477b9a24fa0819193f08b1fd97c6012`; full source: `libfile_3b3de527c790819188b623dd8a627929`. This is a distinct performance/quality trade-off from either simple flat-plane parallax or all-frame 3D rendering.

### 6.5 Analytic and procedural animation

When Waves Meet is a delivered 72-second mathematical ribbon-mesh film: a 128×8 quad mesh, 129×9 vertex array, two component outlines and an unnormalized sum centerline. It illustrates constructive/destructive interference and standing-wave nodes. Its displacement is an ideal linear one-dimensional model, not a fluid simulation or measured ocean.

Source `libfile_b1747a6cd57481918047e75cb81880e1`, v0, includes original procedural background and deterministic animation. The technique generalizes to waves, orbital paths, flows, algorithms and geometric teaching, provided captions accurately name assumptions.

Keep the model values, rendered geometry and narrative labels linked. Do not normalize away a doubled peak while explaining constructive interference, or change a search grid between algorithm comparisons. Decorative glow must not conceal the quantitative relationship being taught.

### 6.6 Native 3D and interactive engines

Blender adds true geometry, perspective, shading, articulated/shape-key animation and rendered camera movement. Godot adds native scene/controller/physics lifecycle and real-time interaction. They are complementary rather than interchangeable evidence.

- A `.blend` that opens is not a complete film.
- An imported GLB is not proof that materials, normals, animation, collision and scale are correct.
- A headless controller test is not a graphics or player-control pass.
- A scripted replay is not necessarily live human gameplay.
- A real-time engine label in a composition manifest may merely describe where an already-rendered movie originated.

For a portable asset, retain units, axes, transforms, pivot, material maps, collision representation, LOD policy, animation names/ranges and source/export hashes. For interaction, add state transition rules, input bindings, reset, failure/success and observable audit outputs.

### 6.7 Hybrid production

A practical hybrid can combine a native Blender background, a 2D character, deterministic effects, genuine screen capture, natural-speed speech and editorial captions. Admit each through its own provenance and compatibility checks, then bind them to one explicit output clock. A hybrid does not need to execute every engine during final assembly; verified pre-rendered media can be reused.

The useful design question is: what visible requirement needs each layer? Remove effects that merely increase counts or obscure the story.

## 7 Speech captions and music

### 7.1 Actual open-source and open-weight TTS auditions

All three requested systems ran locally on CPU on 9 October. The four samples used the same Curie/Lovelace passage, produced mono 24 kHz PCM16 WAV, decoded without error, had zero clipped samples, and matched their saved Library readback hashes. Naturalness, emotion and pronunciation were not assessed by listening.

| Engine and voice | Installed audition version | Output | Synthesis wall time | Approximate real-time factor | Peak memory reported | Disk including environment/models |
|---|---|---:|---:|---:|---:|---:|
| Kokoro Heart `af_heart` | kokoro-onnx 0.6.1; ONNX Runtime 1.31.0 | 19.869 s | 11.335 s | 0.57 | 0.87 GiB | 0.51 GiB shared Kokoro setup |
| Kokoro Bella `af_bella` | Same setup | 20.243 s | 11.461 s | 0.57 | 1.05 GiB cumulative process peak after Heart | Same setup |
| Pocket Alba | pocket-tts 3.3.0; torch 2.8.0+cpu | 18.000 s | 7.474 s | 0.42 | 1.03 GiB | 1.32 GiB |
| Qwen VoiceDesign | qwen-tts 0.1.1; torch/torchaudio 2.8.0+cpu | 19.280 s | 139.132 s | 7.22 | 5.12 GiB | 5.96 GiB |

Real-time factor here is measured synthesis seconds divided by output seconds; lower is faster. These are single-passage observations, not controlled quality rankings or a universal benchmark. Hardware was AMD EPYC 9V74, 9.7 GiB RAM, no GPU, two inference threads. Setup, downloads, review and transfers are excluded. Model loading was another 0.97 s for Kokoro, 43.80 s including initial downloads for Pocket, and 1.70 s for Qwen after downloading.

The practical default already used in the later films is Kokoro `af_heart`, native speed 1.0, separate measured phrases, with no time stretching. Pocket is a measured low-resource alternative. Qwen provides text-described voice design but was substantially slower and larger in this CPU test. Choosing a “better voice” still requires listening to a matched passage.

### 7.2 Code weights voices and data are separate

| System | Code | Weights and voice evidence | Exact audition pin |
|---|---|---|---|
| [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx) | MIT wrapper | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) weights Apache-2.0; stock `af_heart`/`af_bella`; retain model/voice documentation and attribution information | `model-files-v1.1`, `kokoro-v1.0.onnx`, `voices-v1.0.bin` |
| [Pocket TTS](https://github.com/kyutai-labs/pocket-tts) | MIT | [Stock-only model](https://huggingface.co/kyutai/pocket-tts-without-voice-cloning) CC BY 4.0; [Alba MacKenna material](https://huggingface.co/kyutai/tts-voices/blob/main/README.md) CC BY 4.0 | Weights `e7205b6ee50e654a5ea19f0e9df2b0813b05e921`; tokenizer `00eac05ed3d16bdc3f6b5d598874019c34a89214`; Alba embedding `4e1e0a3e611c51c0b4ed8174fc10f32a54644303` |
| [Qwen3 TTS](https://github.com/QwenLM/Qwen3-TTS) | Apache-2.0 | [Qwen3-TTS-12Hz-1.7B-VoiceDesign](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign) model Apache-2.0; generic adult female narrator designed from text, no reference voice | `5ecdb67327fd37bb2e042aab12ff7391903235d3`; BF16 CPU; SDPA; seed 20261009 |

Kokoro local model SHA256 is `beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a`; voice bank SHA256 is `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`. These are the ONNX deployment files, not the separate upstream PyTorch model hash.

The Kokoro model card describes training sources and CC BY material. A model license or developer's data statement is not an independent audit of every training item. Pocket's voice repository contains other voice collections with different terms, including noncommercial material; Alba's terms cannot be generalized to the whole repository. No personal voice recording or voice cloning was used in these auditions.

### 7.3 Audition artifacts

| Artifact | Library identity | Version | SHA256 |
|---|---|---:|---|
| Comparison report | `libfile_6d7785260e848191ae3ee34d3c283fff` | 0 | `220704442110149053ce87437e51a2b2c9b8cbc8c47ba42afb9adae948231c22` |
| Kokoro Heart | `libfile_2fcbfc2374f881919e6b5578a6ae97a5` | 0 | `061251f8a07ee71b58d503b8822f0261f44da58d64dc30d652dbd68c4637ea5d` |
| Kokoro Bella | `libfile_42506451228c8191ac5801347dcffb63` | 0 | `24fe80f141993297f9648afcec6d0a1d1879aaf6181bb5240495a3b958eb0a54` |
| Pocket Alba | `libfile_ce2b8f632dfc81918938d60213db9895` | 0 | `95d66cead8c375d459c50d49d7062ff7872aaa905ca24b3da1509bb8a964693c` |
| Qwen VoiceDesign | `libfile_eff760626714819193956b9a4c4b63ec` | 0 | `a6179bb7731323e0db57e348031f3cff935b44322fc492c3779321f2bf218f70` |

### 7.4 Failures that were actually resolved

Pocket's initial HTTP dependency lacked `socksio`; installing the missing dependency in the isolated environment allowed the next generation to complete. Qwen's first config HEAD request failed with a transport error before weights were retained. The same pinned official files later downloaded through a working Hub client in 76.30 seconds, then inference used local files. Missing SoX and flash-attn did not prevent this VoiceDesign generation; that is not a general statement that every Qwen mode works without them.

Qwen had a 7 GiB resident-memory guard, 1 GiB free-memory margin, 20-minute attempt bound and 500-codec-frame bound. It produced 241 codec frames and did not hit those guards. Preserve failed logs and working pins rather than repeating an already completed audition.

### 7.5 Narration-first timing recipe

1. Freeze the approved words. Separate exact narration, editorial hook, source notes and captions.
2. Split at sensible phrase/sentence boundaries, preserving context and punctuation.
3. Synthesize at natural speed; retain each PCM file, input text/hash, voice/model/settings and actual sample count.
4. Measure signal boundaries and phrase durations. Allocate pauses around changes in meaning, examples and questions.
5. Build one integer-frame timeline for pictures and captions from those measurements.
6. Keep captions faithful to all spoken phrases. A short hook can be editorial, but it cannot replace missing spoken subtitles.
7. Export SRT plus burned-in captions when desired. Distinguish phrase alignment, word alignment and chapter cards.
8. Listen on an appropriate device before approving pronunciation, tone, artifacts and music balance. Numerical checks cannot complete that step.

Earlier Girl Facts checks used a three-frame caption-onset tolerance and at most half a second of trailing hold. Those are project-specific engineering limits, not an accessibility standard or guarantee that every speech sound was understood.

### 7.6 Music and sound

The current cleared recording is [With These Hands by Scott Buckley](https://www.scottbuckley.com.au/library/with-these-hands/), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The exact source recording is 305.737143 seconds, 44.1 kHz stereo MP3, SHA256 `e450028d152becd5c68dec24899f05a71ac1c13d6934dfebf71dbbae5472db9b`.

Retain the actual cue in/out times per film, fades, gain, ducking and full credit. A cue proposed for one 64-second film is not automatically the cue used in every later 66- or 68-second film. Follow the creator's [usage guidance](https://www.scottbuckley.com.au/library/using-this-music/), including required description attribution for YouTube and restrictions on isolated music redistribution or Content ID submission. The film's credits should identify the track, creator, license/source and edits.

Other completed films used original code-authored scores. “Original score generated by code” is distinct from a licensed recording, neural music synthesis and commercial library music. Flite `slt` also appears in earlier format-template receipts; those historical voices should not be conflated with later Kokoro production.

## 8 Practical production recipes

These are procedures for an authorized working copy. They are not an instruction to start new jobs or install tools during reference preparation.

### Recipe A A 66 second photo narrative

Inputs: approved text, exact original photos, chosen existing background treatment, current layer contract, measured phrase audio, cleared music and an unused output destination.

1. Write a hook, concrete situation, meaningful turn and closing payoff/question. Keep factual claims source-qualified.
2. Preserve original images and record the selected crop/coverage contract before animation.
3. Reuse the 972×1728 viewport, moving 5% border and upper y320 title hierarchy.
4. Bind photo holds and caption states to measured narration. Avoid restarting a numbered/fact badge during a continuation phrase.
5. Composite the five background layers and four independent panels, then photo, story graphics, sampled glass and crisp text.
6. Preflight opening, every caption transition, brightest background, largest glyph line, face/prop overlap, ending and all geometry states.
7. Render resumable video-only chunks, verify them, then perform one final audio mux/encode.
8. Retain a high-quality master and create a compact delivery copy only after checking encoded text and protected regions.
9. Preserve the final source, source hashes, timing/rights records, failure history and exact delivery receipt.

Stop if the source, audio or approved geometry changes without a new bound recipe. Do not repair text overflow by shrinking the main photo.

### Recipe B A distinct illustrated story when that style is explicitly selected

This is a reusable historical technique. The latest News/Job request requires realistic dominant imagery instead, so do not use this recipe as its default.

Use a written character/style reference, then generate separate original vignettes for setup, decision and payoff. Keep identity, wardrobe, props and lighting coherent. Save original outputs and prompt/reference provenance. Check alpha-threshold bounds, hands, eyes and purposeful whitespace.

Use camera motion and symbolic graphics that match the story, not arbitrary particle fireworks. If actual body action is essential, rig or animate it explicitly; otherwise acknowledge still illustrations. A title-space correction should change placement only as necessary and protect visible content. Freeze the final narration and art hashes before rendering.

### Recipe C A complete stick figure short

Recover the existing source first. Build a minimal rig with fixed proportions, hand/foot targets and prop state. Define a small pose dictionary and action timeline. Stage one readable problem with escalation and a resolution over 60–75 seconds. Use camera cuts and pacing to emphasize the joke; motion blur or fast effects should not hide failed contact.

Start with a short technical contact proof, then verify a full story before calling it a release. Keep audio cues on the same clock. Compare the direct authored-pose approach against IK/physics only when the story requires repeated contact or dynamic props. License-check any kit separately from the character artwork.

### Recipe D A 2.5D environment with a walking character

Start from After the Rain's exact source. Replace only one qualified art/rig input in an isolated copy. Inspect neutral pose, maximum joint bends and planted stance endpoints. Check silhouette, umbrella/tool grip, occlusion and lower-limb motion with the camera moving. Use separate background planes, but fill every region revealed by parallax. Preserve the baseline and compare the same frame indices.

### Recipe E A native 3D film

Reuse a known scene, freeze camera and source hashes, choose representative wide/hero/detail frames, and benchmark at intended resolution/settings. Verify that the selected detail camera is actually active; an earlier Aetherfall benchmark mislabeled a hero view as water detail because animation overrode the intended camera.

Only launch a long render after visible improvement, capacity and disk/recovery checks. Use immutable shots/chunks and explicit frame ranges. Verify all frames, concatenation boundaries and audio conformity. Treat denoising, samples, geometry and resolution as separate experimental factors.

### Recipe F A reusable Godot room interaction

Choose the actual consumer scene and one concrete behavior. Document units, anchors, collision and reset contracts. Integrate a copy of the exact asset/module into a bounded fixture. Test valid, invalid, repeated and reset operations. Run native headless lifecycle checks, then separately qualify graphical controls and visible fit on a supported route. A placement validator with a static-world contract must not be advertised as moving-obstacle-safe.

### Recipe G A genuine software walkthrough

Capture actual UI navigation through a supported screen-recording route, preserve the continuous raw recording, and edit native-speed excerpts. Record source URL/revision, actions shown and source/output time mapping. Use readable highlights and captions without inventing an interface or claiming tests were run merely because test files appeared on screen.

The Requests example used Kdenlive Screen Grab, a 294.666667-second raw capture at 15 fps, and an 88-second final edit. Later FastMCP history includes owner rejections of held-view treatments and a completed 66-second native-capture repair. That history supports authentic visual motion and task-specific pacing, not a general ban on useful still diagrams.

## 9 Research and editorial methods

### 9.1 Research before visual claims

Maintain a claim ledger with exact wording, source URL/document revision, source type, date checked, relevant passage and what the source does not establish. Prefer original papers, institutions, technical documentation and primary historical records. Community threads can discover a method; they do not establish benchmark quality or rights.

Separate:

- Empirical fact from practical advice
- Original fiction from psychological generalization
- NASA simulation from live camera footage
- Generated portrait from a historical subject's actual likeness
- Conceptual data from measured data
- Source code inspection from code execution
- A public product page from authenticated product behavior
- A music-only review cut from a narrated final

For educational films, preserve the governing assumptions and the exact numbers used in the visual model. A sourced number can still be misleading if its denominator, timeframe or experimental context is omitted.

### 9.2 Story structure

Use a complete arc: hook → context → tension/question → evidence/action → change/reveal → resolution. Visual variety should follow the change in meaning. Add a second scene or perspective when it advances that arc; do not extend a short clip to 60 seconds with repeated filler.

For relationship stories, concrete observable actions are safer and more compelling than universal claims about genders or diagnoses. Who Gets to Tell It? turns on permission and who announces personal news. Take the Whole Job turns on a mutually defined task and observable completion. Neither needs invented statistics.

For history, move from an exact event to what changed and why it matters. Generic atmospheric illustration should not be mistaken for period reconstruction or archival evidence. For code, show the real path through a named revision, not a generic animated “AI” graph.

### 9.3 Visual comparison method

Freeze the source, camera, text and timing; change one meaningful variable. Compare matched frames and a short temporal sample. Record what improved, what regressed and how much the change cost. Use negative controls: freeze the foreground to prove background motion, disable a panel to prove it contributes, or render a known-wrong caption placement to prove the checker detects it.

A comparison that changes layout, caching, worker count, resolution and timer boundaries simultaneously cannot isolate a parallelization speedup. A source test that always passes cannot establish a useful acceptance gate without known-failure cases.

### 9.4 Historical editorial lessons

- Layer-by-layer polish was requested after visually weak procedural backgrounds.
- Heavy decorative edits were rejected when they displaced the image-led intent.
- Large photos, upper yellow hooks and faithful captions became cumulative requirements.
- A real blurred backing was requested beyond a plain translucent panel.
- The 10 October illustrated News/Job direction was rejected in favor of realistic imagery occupying most of the frame; a technically passing illustrated export remains a rejected style candidate.
- Bounded technical success did not rescue the flat Baltor motion-graphics style from owner rejection.
- Positive feedback on an earlier photoreal direction did not automatically approve a later pair or its missing narration.
- Short technical examples remained useful but were repeatedly separated from complete ≥60-second deliverables.

## 10 Rendering costs and capacity

### 10.1 Current tool observations

A read-only version check during this reference found FFmpeg 7.1.5-0+deb13u1, Blender 4.3.2, Godot 4.6.3 stable official (`7d41c59c4`), Python 3.12.14, Pillow 12.3.0 and NumPy 2.3.5. Godot's version command emitted font-cache warnings; it was not a graphical runtime test. Recorded Kdenlive 24.12.3 capture belongs to its documented execution environment and is not inferred from these version checks.

These are installed/observed versions, not recommendations to upgrade or claims about the latest upstream releases. Package pins and native font/codec dependencies matter to reproducibility.

### 10.2 Measured work units

| Work unit | Recorded measurement | Interpretation |
|---|---:|---|
| A Passing Breeze 64-second mesh film | 136.252 s render, 11.273 output fps | CPU mesh route observation; excludes full authoring/review |
| Small Things v4 60-second film | 270.808 s render; sampled concurrent RSS about 400.25 MiB | Existing decoder/compositor/encoder path; no new Blender job |
| Story Composer Window Maker 64 seconds | 70.772 s for preflight + complete encode + encoded verification | One existing-media composition; not a native 3D render |
| Native 3D Moonlit Range 66 seconds, 540×960 | 13,734.177 s accepted chunk render/validation | About 3 h 48 m 54 s; 1,584 final frames |
| Same native 3D run, bounded elapsed window | 15,491.569 s | About 4 h 18 m 12 s including recovery/persistence waits; no CPU core-seconds measured |
| Fifteen Girl Facts visual masters | 2,453.545 s | About 40.89 min for successful master generation only; one story in 15 edits |
| Three later factual films | 2,670.28 s distinct measured stages + at least 170.6 s interrupted render | Not all overhead measured |
| Building Trust / Feeling Heard pair | 1,579.47 s distinct stages + 12.61 s logged interrupted synthesis | Corrected ledger; packaging/unknown overhead separately recorded |

A previous Relationship source ledger counted the same 24.2549-second synthesis stage twice, yielding 1,603.73 seconds. The corrected figure is 1,579.47 seconds. Preserve the correction rather than adding both totals.

For the fifteen-edit batch, one earlier serial Gallery master took 464.143 s, while later parallel Cinema/Editorial/History masters took approximately 105–108 s, and Orbit took 160.382 s. Those runs had different layouts, shadow caching and timer scopes. The 4.30× historical ratio is descriptive, not a controlled parallel-only speedup or an end-to-end savings claim.

### 10.3 Capacity planning

The October 1 Aetherfall plan retained measured 1080p figures around 29–31 s/frame at 12 samples and about 54 s/frame for a 24-sample hero. Its planned mix of 150 seconds at 12 samples and 30 seconds at 24 samples projected roughly 42 render-hours. An earlier 126 s/frame measurement implied about 151 hours for three minutes at 24 fps. These are historical scene-dependent forecasts, not current guarantees.

Use:

`frames = duration_seconds × output_fps`

`estimated_render_wall = sum(frames_for_shot × measured_seconds_per_frame_for_that_shot)`

Then add explicit allowances for failed attempts, encode, checks, subjective review and transfer. Do not multiply wall time by a configured thread count and call it measured CPU time. Do not call included compute free in a business-economics claim: monetary platform cost and human labor were not exposed or measured here.

At 1080×1920, one RGB frame is 6,220,800 bytes before overhead. Four nominal queued frames are about 24.9 MB, but actual memory also includes input images, masks, decoded planes, copies, process communication, caches and encoder buffers. A four-job queue is not a total-memory guarantee.

### 10.4 Sensible optimization order

1. Stop rerendering unchanged imagery when only metadata, packaging or a compact encode changed.
2. Reuse verified audio and background assets.
3. Cache invariant masks, text/shadows and static geometry.
4. Stream frames instead of retaining unnecessary PNG sequences.
5. Checkpoint expensive work at explicit frame boundaries.
6. Compare serial/parallel paths with the same renderer and timer scope.
7. Reduce resolution/samples only after a matched visible-quality comparison.
8. Measure total correction/review effort before extracting a new generic component.

## 11 Quality and acceptance

### 11.1 Content checks

Verify the exact approved script, factual sources, fictional framing, title/caption distinction, complete arc and ≥60-second duration. Review any cut that removes context. Do not promote a successful technical sampler to a finished story.

### 11.2 Geometry and alpha checks

Check every deterministic state, not only a contact sheet: photo bounds; crop extremes; text width/height; protected regions; face/eye/prop clearance; panel seams; safe margins; layer alpha caps; fully transparent source behavior; and final frame. Keep source alpha multiplied by mask and opacity. Replacing alpha can turn transparent PNG backgrounds into visible rectangles.

A final H.264 RGB/YUV serialization can be opaque while individual authored layers stay translucent. The opacity requirement applies to those composited layers; flattening at final serialization should be explicit.

### 11.3 Motion checks

- Decode the actual encoded video, not only source-preview arrays.
- Inspect first/last, cuts, effect state changes and time-separated samples.
- Use frozen-foreground controls to prove independent background activity.
- Inspect each 2×2 panel separately and the combined view.
- Check duplicate frames, timestamps, contact stability, loop seams and sudden discontinuities.
- Distinguish moving camera, mesh deformation, native 3D animation and a screen recording.
- Review uninterrupted playback separately when possible; a pixel-difference statistic is not a motion-quality opinion.

All frames having different hashes can result from tiny noise. That alone does not establish meaningful movement. Conversely, deliberate held text or a pause is not automatically a defect.

### 11.4 Text and compression checks

Render type at the final composition resolution after background processing. Inspect actual glyph bounds, line breaks, outlines and backing against busy frames. Preserve exact font files, license, hash, font engine and shaping environment. A matching font filename is insufficient.

Earlier compact-film gates used caption-ink MAE <5.5; protected-region MAE <4.5 and p99 <22; lower-caption-region MAE <6. These are retained project thresholds, not universal perceptual standards. A known failure involved small amber glyphs damaged by chroma subsampling. Neutral small caption text preserved readability while warm panels/accents and a large colored title retained the look. A current yellow-title/caption treatment needs its own actual encoded checks; do not silently substitute an old white-text checker that fails to locate yellow glyphs.

Native 1080 output describes the composition dimensions. It does not create detail absent from a smaller original photograph or background plate. Likewise, enlarging a 540×960 render does not make it a native 1080p 3D render.

### 11.5 Audio checks

Measure expected duration/sample count, finite values, clipping, peak/headroom, channel layout, decode errors, narration-to-caption clock and output/source correlation. Preserve the actual normalization, ducking and fade settings. A low clipping count does not establish pleasant tone, correct names or balanced music. Mark listening explicitly as performed or not performed.

### 11.6 Game and asset checks

Separate source import, resource closure, mesh/material appearance, collision geometry, controller logic, engine-scheduled callbacks, graphical operation and capture. Include reset/re-entry, invalid calls, missing assets, out-of-range states, occlusion and coordinate transforms. Static geometry evidence cannot qualify moving blockers. A clean headless run cannot prove visible playability.

### 11.7 Final release checklist

- Correct source/configuration/audio versions and rights scope
- Full file exists, decodes and has expected duration/frame rate/frame count
- Complete arc, first frame and clean ending
- Current visual contract and caption checks pass
- Encoded motion/alpha/coverage evidence matches the actual final revision
- Subjective viewing/listening status stated accurately
- Master preserved; compact version separately checked
- Editable source includes dependencies or exact restoration instructions
- Library identity/version/bytes/SHA256 and readback evidence retained
- Owner acceptance and publication status recorded separately

## 12 Recovery and reproducibility

### 12.1 Keep jobs identifiable

Record a unique job/run ID, exact source/config/input hashes, frame range, output destination, process/session ownership when available, lease/lock state, progress, completion/termination evidence and receipts. Preserve partial files and logs. Elapsed time, a quiet log or an empty process list from a different namespace does not prove an old job ended.

### 12.2 Checkpoint video before final audio

Use small video-only chunks with explicit half-open frame ranges. Decode and hash each completed chunk, then concatenate only compatible verified segments. Encode/mux the final audio once to avoid repeated AAC priming, gaps or timing drift. Use an atomic final promotion when implemented and qualified; do not infer it from a filename ending in “final.”

The native lake recovered from an unavailable executor after the log stalled near frame 582. The first four verified checkpoints were reused, a partial attempt was preserved, and later chunks used a second attempt with the same frozen project. The original deadline was retained. Five completed but abandoned frames were excluded from the final 1,584-frame count.

### 12.3 Source package closure

A useful package contains:

- README with exact reproduction path and limitations
- Script/scene/renderer and configuration version
- Asset manifest with hashes, dimensions, timing/color/alpha metadata and rights
- Exact fonts or approved dependency restoration
- Phrase PCM/final mix when permitted, plus narration/caption source
- Seed, clock, camera, model/engine and encoder settings
- Tests and failure fixtures needed for the claimed gate
- Render/decode/review receipts and excluded-large-file inventory
- A known reference frame or output hash for same-environment replay

A compact package that omits movies or model weights is acceptable when it declares omissions and a verified restoration route. It must not be called self-contained. Existing audio can reproduce pictures without loading a neural voice model.

### 12.4 Reopen and meaningful revision

Reopen in a clean extraction, verify payload hashes, run the relevant checks and reproduce a specified frame or small authorized output. Then perform a meaningful change, such as one camera move, caption, color or geometry adjustment, without undocumented author intervention. Compare the effort with an ordinary clear README/manual route.

Same-host byte equality does not establish cross-machine portability. Font libraries, rendering backend, codec builds, color interpretation and GPU paths can change pixels. Keep semantic equivalence and bit-exact equivalence as separate claims.

### 12.5 Failure handling

Classify before retrying: missing dependency, rights hold, source mismatch, malformed input, resource limit, unsupported capability, transport failure, uncertain job state, failed visual criterion or failed compact encoding. Repair the smallest relevant cause. Do not remove a guard just to get a passing receipt. A package test error is not a caught behavioral defect; a refused unsupported feature is not a completed render.

## 13 Rights and source admission

This is a practical evidence checklist, not a legal opinion.

| Layer of rights | Questions to resolve |
|---|---|
| Tool code | Exact repository/release/commit? License and notices? Modification/distribution obligations? |
| Dependencies | Different licenses, optional GPL components, commercial SDKs or hosted services? |
| Model weights | Exact checkpoint/revision? Model license, acceptable-use terms, gating and redistribution conditions? |
| Voice | Stock licensed voice, designed voice, recording permission or impersonation concern? Attribution? |
| Training data | What is documented, and what remains unverified? Do not imply an exhaustive audit |
| Visual source | Original, generated, licensed, public-domain claim or supplied by owner? Exact permitted purpose? |
| Human likeness | Consent/rights context and intended use, separate from owning the file |
| Music/sound | Composition, recording and synchronization rights; credit and editing restrictions |
| Fonts | Exact file and license; redistribution/embedding conditions |
| Output/publication | Intended audience, platform, credits, commercial use, endorsement and sharing authority |

The owner previously declared full rights to supplied photos up to a dated statement on 6 October. Preserve that assertion's scope; it is not independent legal verification, proof that every image was 3D-generated, or permission to publish every later asset. Later image-specific contracts can remain private-only until clarified. Generated art is not evidence of exclusivity or a blanket copyright guarantee.

[Godot's MIT license](https://godotengine.org/license/) governs engine distribution; its own page separates that from game content. [FFmpeg's licensing page](https://ffmpeg.org/legal.html) distinguishes LGPL and optional GPL components. The observed FFmpeg build enables GPL and libx264, so an application-distribution analysis must use that actual build rather than assuming a minimal LGPL configuration. Exporting a movie and redistributing a bundled executable are different questions.

Do not assume an MIT repository licenses its screenshots, example films, logos, model weights or soundtracks. One reviewed product-launch-motion candidate explicitly excluded its reference film/still from reusable assets. A README-only license assertion with no license file can remain a code-adoption hold. Public availability is not clearance.

For every admitted source, retain creator, source URL/Library identity, retrieval date, version/hash, license evidence, required credits, modifications and intended use. An unknown field should remain unknown, not become “cleared” because a renderer accepted it.

## 14 Baltor interfaces and reusable capability design

### 14.1 Reuse useful outcomes before adding wrappers

The project has actual shared-helper reuse and bounded exact-content/data operations. It does not establish that all creative pipelines are live Baltor components. Existing Atomic/Text, catalog-admission, namespace/version/source and snapshot helpers solve specific metadata/evidence jobs; they are not automatically frame renderers or schedulers.

The measured renderer reuse guide is Library `libfile_f34742bcf0c88191aac4e4d2c68965c9`, v0. It supports keeping the project-local ordered CPU frame writer and serial alternative. It explicitly defers a new generic map component without a named second consumer and demonstrated advantage.

### 14.2 A proposed media capability envelope

A useful future contract should describe the following fields without forcing every engine into one identical implementation:

```json
{
  "capability": "render_checked_media",
  "contract_version": "proposal-1",
  "engine": {"name": "selected-existing-renderer", "version": "pinned"},
  "inputs": [{"asset_id": "hero", "sha256": "exact-hash", "rights_scope": "declared"}],
  "recipe_hash": "exact-recipe-hash",
  "clock": {"fps_num": 24, "fps_den": 1, "frame_start": 0, "frame_end": 1584},
  "effects": {"network": "none-declared", "writes": ["new-output-directory"]},
  "limits": {"wall_seconds": "explicit", "memory_bytes": "measured-or-unqualified"},
  "acceptance": {"checker_version": "pinned", "required_checks": ["decode", "geometry", "rights"]},
  "output": {"artifact_id": "assigned-after-save", "sha256": "assigned-after-completion"},
  "status": "proposed-not-an-existing-API"
}
```

This is illustrative. It deliberately does not pretend to be accepted input to Story Composer, Godot, Blender or a live Baltor service.

### 14.3 Reusable boundaries worth preserving

- Source/asset identity and verification
- Explicit clock and deterministic frame selection
- Caption/text geometry preflight
- Font/runtime dependency identity
- Rights/source admission and abstention
- Audio cue and script bindings
- Resource-bounded execution with clear ownership
- Output decode, hashes and delivery receipts
- Evidence-stage labeling and comparison records

Keep mutable caches, credentials, live service access, publication authority and project-specific art separate. A capability catalog entry is not an authorization grant. A typed schema is not implementation, and an implemented component is not proof of usefulness for a real second consumer.

### 14.4 Lessons from reviewed repositories

The historical repository review (POR-0017) extracted design ideas without installing the candidates:

- `gal-a/qikly`, commit `29aae365c22e6c8468e6d4c818a816d527b8b72c`: independently defined tests, known-wrong variants and separating collection errors from caught faults; code integration deferred.
- `tolimcn7786/skills`, commit `55399821192505e9a6585624ab3685e6ed2d1f13`: replaceable-engine idea retained; exact source rejected for installation due to source/flow mismatch and unresolved hosted/model terms.
- `Clairvoyant-fenestration570/product-launch-motion`, commit `970e09cf21b61383453b37bcff134db02db4d880`: measured narration timing, render invariants and output QA retained; wholesale installation/code transplantation not performed; reference film/still excluded from MIT reuse.
- `erishen/resolve-tui`, commit `87bc28bd52fc928665bd3c0499e96ea65c304d09`: deterministic fastpath/cache before model calls and match-or-abstain behavior; code adoption held for rights and independent tests.
- `linny006/awesome-agent-skills`, commit `221ea7bc6af940fcedd15fe63c9e862e7bb5d4f5`: discovery feed, not evidence of a vetting/scoring pipeline.

These are dated research conclusions from the saved log. They are not current security endorsements. README mismatches or low star counts do not prove malware; source availability or a popularity list does not prove a safe useful installation.

## 15 Open source video production and new model candidates

### 15.1 What open source video means here

Three different categories matter:

1. Editing/compositing/encoding: open-source tools such as FFmpeg, Blender, Godot and Kdenlive, alongside separately tracked private project renderers and Python dependencies. Original project code is not automatically publicly licensed.
2. Animation libraries: timelines, geometry, IK, physics, vector drawing and procedural motion, detailed below.
3. Learned video generators: model code plus separately licensed checkpoints, encoders and dependencies.

The first two categories already account for extensive actual project output. A workflow can produce a fully original animated video without a diffusion-video model.

[MoviePy](https://github.com/Zulko/moviepy) is an MIT Python editing alternative with cutting, composition, titles and effects. The upstream README warns of v1-to-v2 breaking changes. It was freshly reviewed for this handbook as an alternative; no current-project installation or execution is claimed. Replacing the tested direct FFmpeg/Pillow route merely to add another library has no demonstrated benefit.

### 15.2 Newly considered learned video options

The recovered historical animation references and the reviewed project logs did not establish Wan, LTX, Hunyuan, AnimateDiff or ComfyUI use. The following are new desk-researched options for this handbook, not retroactive claims of earlier work.

| Candidate | Primary-source finding checked 10 October | Potential role | Qualification and rights gate |
|---|---|---|---|
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI) | GPL-3.0 node-graph/backend project; supports both local model workflows and partner nodes | Reproducible graph-oriented model experimentation | Each node/model/service has separate terms and effects; local UI does not guarantee all processing stays local |
| [Wan2.2](https://github.com/Wan-Video/Wan2.2) | Repository states Apache-2.0 models; text-to-video, image-to-video, text/image-to-video and specialized animation routes | A bounded original motion shot from authorized artwork | No local install/weights/run here; exact checkpoint and dependencies must be pinned; official TI2V-5B example calls for at least 24 GB VRAM |
| [LTX-Video](https://github.com/Lightricks/LTX-Video) | Legacy repository has Apache-2.0 code and points to the newer LTX-2 line | Reference for controllable video workflows | Do not transfer legacy repository license assumptions to new checkpoints |
| [LTX-2](https://github.com/Lightricks/LTX-2) | Current official successor has multiple license files and version-specific model terms | Potential combined audio/video generation, keyframes and control workflows | Exact license/model selection unresolved for this project; not labeled unconditionally open source or commercially cleared |

The Wan hardware figure is an upstream example requirement, not our measurement or a purchase recommendation. The current measured speech environment has no GPU; successful CPU TTS provides no evidence that these video models are practical there.

The smallest sensible future test is one original, rights-cleared 3–5-second shot with a pinned model/config/seed and fixed acceptance criteria, compared with the existing deterministic route. Check character identity, hands, object permanence, camera consistency, usable frame count, editability, memory/runtime and rights. A successful shot remains production material until assembled into a complete ≥60-second story. Model marketing claims do not replace project measurements.

## 16 Cheap experiments and next questions

These are proposed tests, not newly started jobs.

| Question | Smallest useful experiment | Evidence to keep | Stop condition |
|---|---|---|---|
| Which TTS voice should be the default? | Listen to the existing four matched auditions; no new synthesis needed | Pronunciation, tone, artifacts, preferred voice and context | One documented decision, or a specific defect requiring one new passage |
| Does the new glass improve readability? | Compare identical frames before/after at bright, busy and dark backgrounds | Glyph contrast, face clearance, encoded text errors and visual preference | Accept/reject one fixed glass recipe; do not move photo to force a pass |
| Are all four panels useful? | Existing fixed-foreground control plus panel-ablation views | Each panel's actual motion/contribution and composite clutter | Keep only effects with a visible purpose |
| Can the old stick-figure style be reused? | Recover exact Final Boss/Kinetic source and one archived output | Source hash, rig/timeline/dependencies/license and reference frame | Recovery result or explicit missing-file blocker before rebuilding |
| Is a generalized renderer component justified? | One named second consumer with the current direct route as baseline | Same-workload end-to-end time, memory, repair/review effort | Accept only a decision-changing advantage; otherwise retain local code |
| Is a new Godot asset genuinely portable? | Clean import plus one meaningful integration and reset in a second exact scene | Source/export hashes, native tests, graphical fit and unresolved limits | One bounded qualification, rejection or blocker |
| Would native 3D improve this shot? | Three matched representative frames and one short motion proof | Visible gain, seconds/frame, noise/flicker, storage forecast | No long render if quality/capacity does not justify it |
| Would learned video add value? | One authorized original shot, after hardware/terms admission | Exact model/seed, all usable frames, cost, failures and editability | No broad rollout from a single attractive sample |
| Can another person reopen the source? | Independent clean extraction and one specific edit | Missing dependencies, time-to-result and questions needed | One completed handoff or concrete failure; no repeated unchanged test |

The most valuable next decisions are artistic and operational: which completed style/voice should become the reusable default; which one concrete next story needs a new animation capability; and which existing source can satisfy it with the least new complexity.

## 17 Historical animation repositories and game assets

### 17.1 The actual 22 tool research slate

These tools were named in the supplied animation conversation, `Pasted text(2).txt`, Library `libfile_07d2bc025dd48191bbcb26b1f8af870c`. Their official repositories/license pages were checked on 10 October. No exact candidate commit was recorded for this slate, so these are discovery links rather than reproducible install pins. Unless noted, the slate status is considered, with no recovered individual installation or execution receipt. Older history already describes some Motion Canvas and Blender integration; “considered for the new slate” does not mean “never used anywhere.”

| Tool | Concrete role in this project | License and admission note |
|---|---|---|
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | TypeScript timelines, vector scenes, camera/type choreography and narration-led explainers | MIT; older handoff reports diagram/explainer integration, not freshly replayed here |
| [Fullik or FIK](https://github.com/lo-th/fullik) | FABRIK limb IK, planted hands/feet, angle constraints | MIT; upstream naming/API changed to FIK, so pin the actual adapter |
| [Manim Community](https://github.com/ManimCommunity/manim) | Exact mathematical/explanatory vector animation | MIT; distinguish Community from the separate 3b1b implementation |
| [DragonBonesJS](https://github.com/DragonBones/DragonBonesJS) | Skeletal skins, layered actions and Pixi-connected puppets | MIT runtime; artwork and authoring tools have separate rights |
| [Blockbench](https://github.com/JannisX11/blockbench) | Cuboid characters, rigs, action clips, glTF and editable `.bbmodel` | GPL-3.0 application; upstream explicitly separates created assets from application code |
| [Blender](https://github.com/blender/blender) | Native procedural worlds, geometry, rigging, lights and cameras | GPLv3 application; substantial actual project execution exists; new block-chain film was only reported at test-frame stage |
| [Planck.js](https://github.com/piqnt/planck.js) | Door hinges, motors, pulleys and 2D rigid-body comedy | MIT; export physics states to the renderer rather than entangling simulation and drawing |
| [Rapier](https://github.com/dimforge/rapier) | 2D/3D collision/joints and trace-driven scenes | Apache-2.0; determinism must be qualified for the specific build and inputs |
| [Zdog](https://github.com/metafizzy/zdog) | Rounded pseudo-3D Canvas/SVG objects | MIT; stylized pseudo-3D, not a full physical renderer |
| [Paper.js](https://github.com/paperjs/paper.js) | Vector paths and alternate stroke styles for shared geometry | MIT |
| [Rough.js](https://github.com/rough-stuff/rough) | Hand-drawn-looking shapes | MIT |
| [Rough Notation](https://github.com/rough-stuff/rough-notation) | Drawn circles, underlines and emphasis marks | MIT; annotation effect, not a complete character rig |
| [vsketch](https://github.com/abey79/vsketch) | Seeded line art and SVG/plotter-style patterns | MIT code; documentation CC BY-NC-SA 4.0 |
| [SolveSpace](https://github.com/solvespace/solvespace) | Equal-length/angle constraints and mechanisms | GPLv3 or later; inspect solver-distribution obligations |
| [CadQuery](https://github.com/CadQuery/cadquery) | Parameterized doors, desks, brackets and mechanical props | Apache-2.0; exported meshes do not preserve the whole parametric design history |
| [rive-mcp](https://github.com/ODU33104/rive-mcp) | JSON-to-animation, bones/IK and preview automation | [Custom freeware terms](https://github.com/ODU33104/rive-mcp/blob/main/LICENSE), not open source; generated output rights differ from restrictions on modifying/redistributing the software |
| [Flubber](https://github.com/veltman/flubber) | Silhouette/SVG path morphs | MIT; holes and changing topology need dedicated checks |
| [Vivus](https://github.com/maxwellito/vivus) | Stroke reveal and draw-on diagrams | MIT |
| [Ruckig](https://github.com/pantor/ruckig) | Velocity, acceleration and jerk-bounded camera/prop motion | MIT Community code; intermediate waypoints in Community use a cloud API, unlike local Pro waypoint mode |
| [librosa](https://github.com/librosa/librosa) | Beat and onset analysis to align motion with music | ISC; analysis does not grant soundtrack rights |
| [Kiwi](https://github.com/nucleic/kiwi) | Cassowary constraints for label/caption spacing | Modified BSD terms; historical variant unpinned, linked source is C++/Python |
| [Maker.js](https://github.com/microsoft/maker.js) | Parameterized drawing and mechanical SVG/DXF paths | Apache-2.0 |

The first named evaluation priorities were Motion Canvas, Fullik and Planck. The proposed shared story interface was story/lesson → actions, props, shots, captions and sound cues, with reusable walk, reach, recoil, fall, celebrate and react behaviors. Constant-speed path drawing, bounded camera acceleration and frame-exact sound cues were specific desired custom capabilities. These are more actionable than collecting tool names without a consumer.

### 17.2 Broader historical engine routes

The October 1 master handoff, Library `libfile_341bd2ed6bf881919b6f56252efc03ca`, describes routes on the earlier production computer:

- Three.js: room/product studies, orbital and neon scenes, paper/insect/voxel/probe/route films
- Blender: native room/product backends and seeded worlds
- Godot: authored marble runs, separate actual rigid-body drops and domino paths
- PixiJS: layered puppets and hidden-object rooms
- Remotion: story, data and chart compositions
- Motion Canvas: diagrams and explainers
- Anime.js/SVG: kinetic typography and drawable paths
- Python/NumPy/Pillow/OpenCV: simulations, diagrams, cutouts, scores and inspection
- FFmpeg: assembly, encoding, decode and mastering
- Babylon and other engines: candidate or source-only routes in the specific records

These are reported historical integrations, not a claim that every engine is currently installed or every adapter has been replayed. A historical RTX 3060 did not make SwiftShader runs hardware-GPU benchmarks; browser context-loss failures were recorded.

### 17.3 External visual kits actually referenced or used

[Kenney Marble Kit](https://kenney.nl/assets/marble-kit) is CC0 according to the official asset page. The historical handoff records a download with license and tests of three selected objects in GLB/OBJ/FBX formats. That is nine selected encoding checks, not full-package qualification or a delivered physical-music film.

[Poly Haven Mossy Stone Wall](https://polyhaven.com/a/mossy_stone_wall), by Amal Kumar, is covered by Poly Haven's [CC0 asset policy](https://polyhaven.com/license). Earlier Aetherfall look development used three 1K texture maps. Later exact four-GLB diagnostic scenes explicitly omitted those maps and used constant material values. Preserve that dependency distinction.

The original project kits below retain their individual rights notices. No blanket public open-source license is established.

### 17.4 Orbit Courier

Cloud 3D Starter: `libfile_b54b4bd15ed08191a2adf7241a9de025`, v1, SHA256 `cdf0d5fae81d8c3b2ce3a836cfdca3bc0d970dd72aa6d20220301ae63f12eadb`.

A real nondefault-parameter test changed four parcels to six in Godot. The original collected all six but failed to win and displayed `6/4`, exposing hardcoded win/HUD/footer values. An isolated correction derived them from `PACKAGE_POSITIONS.size()`. Six-parcel and restored four-parcel headless tests passed. Repair archive: `libfile_8f6118ba93648191bb9ef1dcfd4c1f95`, v0.

The test repositioned the player directly. It proves a bounded state/configuration repair, not navigation, graphics, control feel or browser-engine parity. The original archive remained unchanged. Software-rendered Three.js video `libfile_bfc3dde3679481919bad87556945bc2c` and scripted gameplay visualization `libfile_a29ce424185c8191a0035bec4f1a5d83` are separate evidence types.

### 17.5 Aetherfall

Aetherfall combines original native landscape work, a bounded walking/sailing/flying game slice and substantial contact/recovery research. Keep those tracks distinct.

| Artifact or result | Identity / recorded evidence | Boundary |
|---|---|---|
| Original Blender source | `libfile_0917755c620c819187f1577b33c7deb8` | Source, not complete trailer |
| 180-second editable scene | `libfile_4e12d03f28ac81918570b8483d505951` | Planned full timeline, not proof all frames rendered |
| 180-second storyboard animatic | `libfile_326a6e56b1288191bf2a6c569c6525d1` | 4,320 encoded frames from 44 unique held 3D images |
| Eight-second native cinematic | `libfile_6e0e87e7d6ec8191a63814556a583d90` | 192 actual 1280×720 Cycles CPU frames; initial water/background quality required revision |
| Game slice source | `libfile_8331524819288191b64322e3fca7f5ab`, v0 | Native source/mechanics; visual acceptance separate |
| Contact-fixed RC1 Linux build | `libfile_bf665868a2808191b4387fe5ed4faf46` | Export/headless startup qualified; graphical controls and continuous boarding/landing open |
| RC1 known issues | `libfile_0c55ad97c8108191ad442ad5a44c7ed9` | Precise launch and limitation record |

The slice includes walking, sailing, flying, beacons and a compass objective. Six mode transitions relocate the keeper approximately 2.06–4.53 m in one tick. Sampled endpoint clearance therefore does not prove continuous articulated movement.

The experimental first-boarding chain progressed from geometry fixture 0.1.0 through conditional capsule repair 0.2.0, source adapter 0.3.0, scheduled headless scene 0.3.1, a rejected solver attempt 0.3.2 and an unqualified proposed solver contract. The solver rejection concerned a 5-micrometre authored-pose identity guard; physical-clearance checks at those rejected endpoints passed. Do not rewrite that history as proven collision penetration or merge an isolated experiment into the released game.

A historical Aetherfall Site projection claims a finished three-minute 4K film and six portrait cuts, but the more explicit RC1/validation records describe unfinished 180-second/full-social scope. The completed media behind the Site claim were not recovered here. The discrepancy remains unresolved; it is not used as a completion count.

### 17.6 Studio Six

Original props: walnut riser, ceramic mug, task lamp, linen notebook, pen tray and compact speaker. Kit `libfile_7ec958154ca08191afa1669eebcb1e97`, v0, SHA256 `5d41da15b9531147bec78950b39cd840ebaff4034dc0c76fa040d0f39e30175d`.

The kit includes a procedural Blender builder, native source, GLBs, collision description, Godot demo and engine contract. Units are meters; Blender uses Z-up/−Y front and glTF Y-up/+Z front. Materials use embedded core metallic-roughness PBR with explicit UVs/normals. Pivots are design-base anchors, not universally exact bounding-box centers.

Actual Blender evidence and Godot 4.6.3 headless import/instantiation of nine GLBs, manual LOD switching and conservative-box settling exist. Three.js 0.186.1 and Babylon.js 9.29.0 examples received source/syntax checks, use CDN imports and are not offline-qualified. The six props are static; no skeletal rig, hinge system or animation clips should be inferred.

### 17.7 Glasshouse Nine

Nine original modules: floor, glazed wall, solid wall, gable, roof, hinged door, fan, raised planter and potting bench; 2 m grid and nominal 4×6 m floor. Kit `libfile_51d9f86009708191ade0534cf4a530a4`, v0, SHA256 `cb56c2b30c965e66f8a11c370d3584bdc73471a71548a36af40f5d790e5f650a`.

`Door_OpenClose` is a four-second transform animation with 121 samples and 95° outward opening. `Fan_Spin` is a two-second full turn with 61 samples. These are actual glTF transform channels, not a skeletal rig. Native headless imported AnimationPlayer progression, simultaneous playback, independent pause/resume/restart and loop wrap passed. Browser examples remain source/syntax-only. Alpha-blended glass is not physical refraction, and renderer-specific transparent sorting remains a separate check.

### 17.8 Cedar Vale and the interaction kit family

House kit: `libfile_9bf6405627e08191b53e8a2569620ecf`, v0, SHA256 `f3e97a304c2a5b73402b47f5fd7e8633c1469b8bcff7eff627ac7fe332dbd1b6`.

The furnished environment uses original geometry, seeded material maps, three door pivots, 83 static box proxies and three dynamic door-leaf boxes. Godot collision behavior is not encoded by a portable GLB alone. Recorded headless imports, CharacterBody routes, grounded motion, open/closed door blocking, synthetic input events and cutaway toggles are real engine tests. Overlapping packaged/independent test counts must not be summed as unique behavior counts.

| Reusable module | Concrete contract | Explicit limitation |
|---|---|---|
| Willow Gate | Garden assets, gate/light state; later birch/LOD improvement | Same pack revision, not a new kit; obstruction add-on is bounded |
| Tidehaven Eight | Waterfront assets and native runtime behavior | ZIP v1 corrected audit/checksum; it did not add geometry |
| Brasswick Six | Interaction props and interlock; PBR/batching revision | Batching is not a measured FPS gain |
| Lavender LOD | Three geometry tiers; two bounded house integrations | Geometry count is not target-device performance |
| Irrigation | Finite tokens; reservations/FIFO; explicit ticks, rain, pause, reset, cancel, snapshot/restore | State conservation, not fluid simulation or irrigation science |
| Pump Station | `bind_controller`, `unbind_controller`, read-only gauge ratio | Reuses one authoritative irrigation ledger; no second tank balance |
| Utility Rack | Three snap modules; queued whole-layout changes at physics callback; snapshots | Caller must clear content/actors; conservative contact proof only |
| Registered Rack Guard | Explicit content registration and clearing acknowledgement | A freed/lost reference is unresolved, not proof physical contents were cleared |
| Wall Clock | Named hand pivots; seek/advance/rate/running/reset/restore with explicit simulation time | No OS/network/timezone clock or civil-time accuracy claim |
| Roller Blind | Extension/target/speed/running; seek/advance/stop/reset/restore | Fixed hardware collision; fabric is not dynamic physics |
| Five Geometry Styles | Faceted, hexagonal, triangular, cube and voxel room geometry | Actual geometry differences; conservative proxies omit hollow detail |
| Room Survey | Finite focus/dwell objectives, restart and native occlusion | Small headless-qualified mechanic; human controls remain separate |
| Surface Arranger 1.0.0 | Preview/place/cancel/reset/restore; exact Studio Six reuse | Stable synchronized world only; same-tick moved-obstacle test retained a failure |
| Surface Arranger 1.0.1 guard | Registered static bodies, sync barrier, validation and invalid-state latch | Does not cover unregistered/new bodies, hidden between-check changes or general moving-body safety |

Graphical evidence remains precise: Godot Project Manager launched on the supported cloud desktop, but the exact project was not visible in that separate filesystem, and the Library transfer hit `ERR_BLOCKED_BY_CLIENT`. Native app launch is proven; exact-project graphical play is not. This is a scoped transfer blocker rather than a universal statement that graphics cannot work.

### 17.9 Other worlds and control replays

Twin Realms is an offline two-world engineering build, initially Library `libfile_1e5f1d6e16588191951bddae3ab58af0`, v0. Later shader-precision repair and original-music work have separate records. Bounded model/source tests do not establish real browser play or successful capture. Keep a scripted replay, the game file and actual user play as distinct outputs.

Hexhaven progressed from bounded hex-column scenes to a million-cell procedural horizon and a later 10,246,401-position bounded-state/seed-persistence design. Those counts describe addressable positions, not simultaneous rendered cells. Offline source/model/handler checks and scripted software cinematics exist; real browser/mobile play and device performance were unverified in those records. V4 source is `libfile_91d502cb519c81918d109ca037ab2ff3`; offline HTML `libfile_bb2e74ee41748191a43c0cc0fb1e0f21`.

Glasswater Survey and Stonewake Signal are distinct 64-second scripted films: `libfile_eb0ec879ba648191adb2a679d9d84c6d` and `libfile_5a6d6e2978c08191b635b633b4b69c00`; source `libfile_8dd44e994ae0819191cca013906a89b6`.

Street Dispatch has a 74-second first-person/shoulder control replay (`libfile_6f4ce3213c3481918318c263aa4d1c98`), source `libfile_8dcf98600e5c8191ab5ea8d770ccf128`, and offline HTML `libfile_9708d25936e48191bbbad5adabd9bb1b`. Model/camera/UI-harness/replay tests do not close actual browser-play acceptance.

The Rain Courier is a separate original 68-second CPU-rendered 2D story with captions and original sound, 720×1280 at 24 fps and 1,632 unique decoded frames. It should not be credited as the newer Final Boss film or Aetherfall recovery.

### 17.10 Actual Baltor reuse in creative work

Three useful bounded interfaces have concrete consumers:

1. Portable Project Workspace 0.1.0, `libfile_511f41a73f088191b20a364f79957175`, v0: unchanged `strict_json`, `relative_file` and `verify` checked the real Cedar irrigation controller/config payload. Refusal cases cover changed bytes, missing files, bad hashes, traversal, symlinks and duplicates. It verifies declared file bytes, not rights, authenticity, transitive dependencies or engine compatibility.
2. Baltor Evidence Maintenance Kit 0.1.0, `libfile_f3bf85f30ccc8191a8b32b7dcdca8fc4`, v0: unchanged modules reviewed an actual kitchen-clock revision with one changed script and fifteen unchanged input pins. Historical PASS text remained intact while dependent review/citation records were marked for reconsideration. That preserves historical truth without pretending old evidence automatically applies to new code.
3. Receipt Cost Reconcile 0.1.0, `libfile_af4b07542b5c8191a4b1d8b5b46a84e6`: `invoke`, `invoke_json` and CLI reconcile explicit namespace/run/stage/attempt identities. Two edited receipts for one 24.2549-second TTS invocation count once; matching audio hashes alone cannot establish identical execution. Unknown/conflicting measurement identities remain unresolved rather than inventing totals.

These are real scoped reuse examples. They do not establish a deployed unified Baltor animation platform or financial savings.

### 17.11 Historical production family map

The following map consolidates the earlier master handoff's 32 families. “Rendered” is a historical report for examples in that family, not current execution proof, uniform artistic acceptance or a blanket right to reuse every source. Each future consumer still needs its exact artifact/recipe and current contract.

| Family | Historical footing | Listed concrete mechanics | Meaningful parameters |
|---|---|---|---|
| Dance / performer effects | Rendered; source-based, not full 3D motion capture | Pose-triggered spores, lightning, water, ribbons, silhouettes, echoes, balloons, form-angle overlays | Pose confidence; mask stability; emission rate; face keep-out; effect coverage; beat phase |
| Dance comparison / anthologies | Rendered | Matched A/B, source versus effect, four-world sequences, effect build-ups, storm relays | Source interval; cell geometry; crop; transition beat; shared soundtrack |
| Satisfying rule-based simulations | Rendered; individual mechanics need their own tests | Ring escapes, multiplying balls, triangle tripling, paddle merges, packing circles, gapped boxes | Seed; gravity; radius; restitution; gap angle; rotation; spawn rule; population cap; timestep |
| Marbles, dominoes and physical music | Native starter scenes exist; Peg Sonata is a model/plan, not a delivered film | Authored marble paths; real Godot rigid-body drop; domino chain; impact-to-note composition | Peg positions; ball radius; gravity; restitution; friction; note threshold; score mapping |
| Spinning ambiguous objects | Rendered | Point-cloud cat/dancer/butterfly, shell, knot, tree, whisk, sphere, ribbons | Object; mirror transform; spin period; integer turns; point density; normal-based shading |
| Geometric and color illusions | Rendered examples plus proposed families | Cafe Wall, equal-size/color context, impossible forms, forced perspective, shadows, moire, visual anagrams | Projection; view angle; contrast; line spacing; masks; reveal camera; exact geometry invariants |
| Particles / vortices / math art | Rendered core looks; many extensions are concepts | Vortices, hyperspace ribbons, galaxy orbits, helix coils, attractors, spirographs, Lissajous figures | Particle count; field equations; seed; integration; camera; size; tone map; bloom cap |
| Algorithm and code explainers | Rendered, with executable model tests | Sort comparisons, linear/binary search, Hanoi, Big-O, BFS/DFS, vertical-only wave lattices | Input distribution; target; algorithm; event definitions; compares versus swaps; teaching time scale |
| Technical / chaptered core explainers | Short comparisons rendered; broader lessons are recipes | Wi-Fi versus Internet, RAM versus storage, file formats, network packets, sensor types | Concept pair; evidence; worked example; causal state; chapter length; label anchors |
| This versus that / choices | Rendered | Two-term education, A/B preference rounds, cats/dogs, coast/forest, product categories | Matched camera/light/scale; round count; question; payoff; truthful comparison conditions |
| Sourced facts / geography / weather | Rendered examples; each new factual script needs verification | Planetary facts, weather mechanisms, nature facts, relationship/psychology claims with real evidence | Source date; units; caveats; diagram scale; narrator timing; factual claim ledger |
| Charts and data stories | Native data-driven renderers and named masters exist | Line charts, bar races, scatter/distribution, networks, flow accounting, small multiples | Dataset; units; domain; interpolation policy; missing values; survey breaks; tie/rank rules |
| Research / evaluation explainers | Rendered DueCare example | One result versus a whole result set; aligned comparison cards and scoped evidence | Task definition; reference design; denominators; held-out definition; source release; scope labels |
| History / micro-documentaries | Rendered coffee-camera and historical motion examples | Object-led history, dates, sourced archival accounts, original illustrations, headline over B-roll | Dates; archive versus reconstruction label; camera path; source; reveal timing |
| Photo motion / 2.5D | Existing compositor/code and rendered examples; not all proposed modes finished | Ken Burns, panoramic scrolling, subject/background planes, detail magnifiers, album turns | Depth layers; crop anchor; camera baseline; edge masks; parallax amount; artifact checks |
| Panels / grids / picture-in-picture | Rendered comparisons and recipes | Top/bottom, 2x2, hero with supporting cards, comic panels, reaction corners, mosaic backgrounds | Cell count; reading order; panel phase; hero scale; text area; source-time synchronization |
| Recurring photo-cutout animal comedy | Many historical renders / source-specific review states | Raccoon Crew, Capybara Calm, Office Penguins, Owl Teacher, singing frog, countdown casts | Cast identity; role; pose; gesture; mouth cue; bubble anchor; scene blocking; punchline timing |
| Original character stories / motion comics | Rendered | Miso, cat duo skits, missing-prop stories, six-panel courier story, anthology chapters | Rig; expressions; visemes; prop constraints; cameras; shot timing; source art identity |
| Moving / speaking avatars | Partial 3D source plus functioning simpler puppet paths; full promised batch not established | Cute animal dance, idle, reaction, wave, presenter, jaw/mouth animation | Rig hierarchy; clip retiming; foot contact; jaw/viseme channels; blinks; gaze; speech timing |
| Hidden-object / memory / motion puzzles | Rendered Pixi implementation and original rooms | Find-all, frozen character, odd dance, missing prop, memory recall | Target count 1–15; answer IDs; slots; sizes; clutter; search time; reveal sequence |
| Breathing / attention / perception tasks | Rendered recipes; historical copy corrections matter | Breath rings, box/4-7-8 pacing, figure-eight target, Stroop, follow-four-shapes, afterimages | Exact phase durations; target path; velocity; acceleration; cycles; luminance; instruction timing |
| Reddit-style / paraphrased social stories | Rendered template family | Hook, concise paraphrase, opposing comments, viewer poll, original background action | Story beats; privacy-safe paraphrase; comment roles; reveal timing; background cognitive load |
| Product / material / holographic studies | Native product starters; holo lab is partial and references are not finished films | Turntables, foil, chrome, glass, thin-film color, card shine, configurator, material comparison | Roughness; metallic; transmission; clearcoat; light size; lens; material swaps; finish timing |
| Mechanisms / exploded assemblies | Rendered original flutterer and folding probe | Named hinges, gears, exploded construction, rigid part motion, reassembly | Bind transforms; pivot locations; limits; gear ratio; explosion amount; camera; reset |
| Spacecraft / sci-fi cinematics | Folding probe rendered; longer hull/launch sequence remains a brief | Hangar, scale reveal, hull detail, panel deployment, ignition, launch, orbital hero | Part hierarchy; deployment; thruster timing; shot lens; scale references; atmospheric depth |
| Voxel / hex / tile / tiny-planet worlds | Voxel garden rendered; native world builders are unfinished starters | Seeded biomes, falling blocks, rising hex islands, square worlds, tiny planets, day/night | Grid/topology; seed; biome; block size; vegetation; build order; sun cycle; water |
| Real geography / terrain / train / globe routes | Station and projection films rendered; other routes are recipes | DEM + mapped transport/buildings, location guessing, globe routes, map layers, area-to-bars | CRS; coordinate order; units; source dates; elevation; route connectivity; label occlusion |
| Parkour / runner / game B-roll | Authored 3D camera film; not itself a playable game | Floating rooftops, voxel jumps, obstacle courses, low-poly driving, satisfying routes | Jump model; speed; obstacle gaps; checkpoint state; controller; camera clearance AND sightline |
| Playable arcade / game trailers | Two-course offline original prototype tested; movie tracked separately | One-button lane switching, loss/retry, slower replay, harder course, final reward | 120Hz model; player radius; wall/gap geometry; course pattern; input trace; scoring; pause/reset |
| Typography / SVG / line motion | Native Anime.js starter scenes rendered | Kinetic type, drawable paths, lettering into objects, one-line worlds, branded stingers | Glyph geometry; path arc length; easing; stroke reveal; hold time; font license |
| CAD / 2D-to-3D / reconstructed assets | Research and reusable geometry directions; not all integrations working | SVG extrusion, lathed vase, bracket, enclosure, lattice, sketch-to-solid, photogrammetry, splats | Dimensions; tolerances; wall thickness; topology; UVs; uncertainty; licensed input views |
| Audio / visual music / stem remixing | Original synthesis and stems working; external models are research candidates | Impact-led notes, sorting pitches, narration ducking, continuous anthology score, audio-reactive environments | BPM; key; seed; gain; event-to-note rule; envelope; ducking; loudness; loop tail |

### 17.12 Proposed upgrades and concepts preserved as proposals

Twelve detailed upgrade briefs remain distinct from finished films:

- Marble instrument/terrarium with actual impact-to-note score
- Folding paper city or voxel garden driven by real instance tables
- Mechanical creature with named hinges and explode/reassemble states
- Miniature 3D one-button arcade retaining a tested two-lane model
- Physical algorithm machine driven by an actual trace
- Museum object or procedural vase with explicit source/geometry rights
- Original paper/foil greeting card with a real hinge reveal
- Geographic train/landmark mystery using terrain and connected routes
- Impossible object explained through a camera reveal
- Full character short with contact, eyelines and a complete payoff
- Recognizable object transforming through a bounded particle portal
- Spacecraft deployment preserving rigid named panels

The later 24-concept research set was grouped by route:

| Route | Six proposed concepts |
|---|---|
| Blender | Marble terrarium bloom; camera-revealed impossible staircase; paper city folding into a planet; animal room changed by dominoes; chrome ribbon through ceramic gates; canyon unfolding from a tile |
| Game engine | One-button three-jump platformer; marble course with explicit between-attempt changes; miniature train routing; bridge-building rescue robot; four-lane gravity race; checkpoint-driven rotating-wall maze |
| Three.js/Babylon | Particle portal room; moving-contour shoreline; sculpture swarm opening a passage; audio-reactive ribbon garden; toy city under day/rain/neon light; vortex-to-object morph |
| 2D/2.5D | Articulated paper-cut cat escape; algorithm-bar platformer; parallax illusion explanation; sorting conveyors; domino recursion proof; storm diagram becoming a miniature world |

Other named series ideas were Material Switch, Scale Atlas, Cutaway Rooms, Tiny Logistics, Type in Motion, One Line Worlds, Map Layers, Sound Shapes, Stop-Motion Objects and Shadow Proofs. Preserve them as a queue of questions and briefs. A series name or concept count is not another implementation, active experiment or completed release.

## 18 Selected artifact and source register

### 18.1 How to use the register

A Library identity is stable; its version selects the particular historical bytes discussed here. A source package version such as 1.0.0 is not the same as a Library version such as 0. The hashes below come from the cited saved validation records unless explicitly identified as newly read-back. They are not a claim that every archived package was downloaded and rerun to write this handbook. Obtain the matching authorized file, verify its hash, then read its own README and current limits before reuse.

This register concentrates on reusable source, game builds and guides; media examples and current film receipts appear in the relevant sections above. It is not a finished-film count. Some packages preserve failed, proposed or blocked work deliberately.

### 18.2 Snapshot source documents

- **Thirty Day Portfolio Delivery Plan.md** — `libfile_dbb8a8ab319481918cf6ba6ae6b7f3d6`, Library v4. 69 lines; duration and evidence requirements. SHA256 `7c4c323fa9a0bc543848fba9e1659bb5699aba4d9099babb335a2c650025ff02`.
- **Reusable Asset Validation Log.json** — `libfile_8b70ba61e5208191a652c99a8a4325b4`, Library v169. 171 retained entries; exact historical technical/artifact records. SHA256 `a035364f9f075bb6917d72854220376b7db18b17d788a8d27d8f8d69d215cea4`.
- **Portfolio Opportunity Research Log.json** — `libfile_1d28b097f4808191836338a9bc4e59f7`, Library v72. Research, comparisons, rights and adoption limits. SHA256 `4d8c7de7a8117f3423cb6028af62f02bda9809f29ad645581808d9784143f055`.
- **Business Data Initiative Index.xlsx** — `libfile_eef8e02043888191b13449714fc4dda0`, Library v11. Portfolio identities and evidence-stage context. SHA256 `d6a532097656a881b63aced822954f8a9e0eacdb9e78b4462ad1a8e7643cfa75`.

Additional historical sources: `Pasted text(1).txt` (`libfile_3f7f878b130481918fe7227d6fc05f6f`), `Pasted text(2).txt` (`libfile_07d2bc025dd48191bbcb26b1f8af870c`), and `OPENAI_DOT_MASTER_HANDOFF_2026-10-01.md` (`libfile_341bd2ed6bf881919b6f56252efc03ca`). Their supplied-history role and missing directly exposed Library version are preserved. The first guide's old defaults do not override current visual instructions. The larger `Baltor_Master_Component_and_Creative_Handoff_2026-10-06.md` is `libfile_617ff6b27a088191b64bebb7f00a961d`, v1; only relevant named references were consulted.

### 18.3 Current visual reference deliverables

| Reference | Library identity | Recorded version |
|---|---|---:|
| Background_Layer_Reference_Book.pdf | `libfile_faf334985ee08191914392c50d7f0a12` | 1 |
| 01_Background_Atlas_36_Directions.png | `libfile_98236c2be3748191b941c9a01b6a2c91` | 0 |
| 02_Photo_Geometry_and_Hierarchy.png | `libfile_1da5f4a8e5f8819180376cbf5de90dc0` | 1 |
| 03_Thirty_Layer_Exploded_Stack.png | `libfile_eeca1b76d09c8191a305f905549ccbf7` | 0 |
| 04_Four_Panel_Independent_Compositor.png | `libfile_3af87ebe8f40819195dc75ff5a406cf0` | 0 |
| 05_Four_Finished_Recipe_Directions.png | `libfile_74d37f0078bc8191b4215b5447da6ef5` | 1 |
| 06_Motion_Parameters_and_Validation.png | `libfile_e17d979c526881918c5e176db47138a7` | 0 |

All six sheets are static references. The PDF v1 SHA256 is `e7da1f1ddd31c95d98ad52e1177cf922b2600b68fa4b17a0fffa68462d5ce39f`. The atlas has 36 visual directions; the exploded stack proposes 30 slots. Current implemented motion evidence comes from film receipts and source, not these static pages.

### 18.4 Film snapshot after the realism correction

At the 10 October 09:28 UTC snapshot:

- The v7 photographic pair remains the exact verified baseline in section 4.2. The genuine-glass update to those two films is still pending terminal delivery evidence.
- The v7 editable package is `libfile_f8633d207dc88191b3cce86966102539`, v1, SHA256 `0f0a746e32d6509043a53c76f2e7b2b635030f9c6d6a775a27ce3158e7f25100`. It is a complete saved baseline, explicitly superseded creatively by the requested glass revision.
- Who Gets to Tell It? completed a 68-second illustrated glass export: compact `libfile_a037682f39808191ad6f6b8bf8cd3087`, v0, SHA256 `f4d2cc00b5663c4c64820a48743e4db874f2066b0ce148cfa18b5037e8cd3c23`; master `libfile_ab58be063de88191b442705eb6ee725c`, v0, SHA256 `c21708a1ede0f6dd5820c04b0e408b79fdf9a2b9ca3549fcec157ff8385c897a`. Full compact/master decode, timing, 47 native caption comparisons, eight decoded temporal chapter contacts, layer/glass checks and exact readback passed. The owner then rejected its illustrated style at 09:26 UTC.
- The illustrated Take the Whole Job master is being preserved; compact encoding and delivery are held. Photorealistic replacement assets are in preparation. No replacement completion or final creative acceptance is implied.
- The completed News caption check measured yellow-core MAE 4.235 against a 5.5 limit; whole-glyph compact-to-master MAE 3.820 against 4.0; minimum yellow glyph recall 0.9779; additional recall loss 0.00909 against 0.01. It retained the older white-caption gate failure as diagnostic history. These are technical checks, not proof the owner likes the style.
- No full glass-source archive has yet been established by a terminal receipt, and no subjective listening pass is claimed.

### 18.5 Reusable source packages and offline builds

- **Baltor Creative Reuse Revision Test.zip**
  - Library `libfile_8f6118ba93648191bb9ef1dcfd4c1f95`; recorded Library version 0; evidence AV-20261001-014
  - SHA256 `not recorded in the selected artifact row`
- **Aetherfall First Boarding Geometry Fixture 0.1.0.zip**
  - Library `libfile_b9f189a7128c8191a458ae152f81fa09`; recorded Library version 0; evidence AV-20261003-053
  - SHA256 `27192d5f2e7a29904a7f73f572a025c494a96cc8a8ed703e06d93b1227f7ddb6`
- **Aetherfall First Boarding Repair 0.2.0.zip**
  - Library `libfile_fbb2c5f7a1fc819194c8d4d32d5bb88a`; recorded Library version 1; evidence AV-20261003-054
  - SHA256 `8a3301eb21c8e1aca85421b2db75719e03159a8b8c2dcb7b87835dcfe0f32dc3`
- **Aetherfall First Boarding Source Adapter 0.3.0.zip**
  - Library `libfile_e3c5ef88a8ac8191ad3d2f705315a247`; recorded Library version 0; evidence AV-20261003-055
  - SHA256 `99a33b7bef805228c5f867f8f8db0087a7db7d9176a7fcdb20d8b595e0c54ac5`
- **Aetherfall First Boarding Scheduled Scene 0.3.1.zip**
  - Library `libfile_fa1889a1b01c81918af9303511044dea`; recorded Library version 0; evidence AV-20261003-056
  - SHA256 `28767b7ed81815ddbeca69e2b526d71dcc3fbe72e2c82f3e58fbdbcd3442e272`
- **Aetherfall First Boarding Solver Rejection 0.3.2.zip**
  - Library `libfile_2cd113fe66c48191b4ab0bd119eebcee`; recorded Library version 0; evidence AV-20261003-057
  - SHA256 `e54a03b5ab7c232f3f39e2cfc7b34e7e6c5f4f2d8aca958f6e79c032531fc40b`
- **Aetherfall Solver Contract Proposal 1.0.0-proposed.1.zip**
  - Library `libfile_3a58db7d0a4c8191857c9fd1044cfc9f`; recorded Library version 0; evidence AV-20261003-058
  - SHA256 `3d0c1cf8046b41aeef69c77043cf6d34510965d9524111b83d60a176fe05042b`
- **Moon_Lesson_Compact_Editable_Source_Pack.zip**
  - Library `libfile_6e32fdd292008191ac513aecb5d8667f`; recorded Library version 0; evidence AV-20261004-070
  - SHA256 `d43bc1318d069000232a0bdc9a3637cdc13b01bceebdd00c5ef6f7b821921a77`
- **Moon_Lesson_Editable_Source_and_Social_Pack.zip**
  - Library `libfile_ea88ceeb41fc81919b6fdcda08ad3342`; recorded Library version 0; evidence AV-20261004-070
  - SHA256 `63d2e0db5675766e76c102052265d7cf3fb38b042d0f71ded4efa06cfdf24be0`
- **Twin Realms - Play.html**
  - Library `libfile_1e5f1d6e16588191951bddae3ab58af0`; recorded Library version 0; evidence AV-20261005-071
  - SHA256 `9589af1d12622bae12824bd7b9e697d46abd30603e66db6548f498619452147c`
- **Twin Realms - Source and Guide.zip**
  - Library `libfile_c2c4f845c45c819184e2fbdc0466935e`; recorded Library version 0; evidence AV-20261005-071
  - SHA256 `3c5df1a1479e8804f0f8a3606ff836f20b08573e5991622050e78451ae9ebdb9`
- **Twin Realms - Play v1.0.1.html**
  - Library `libfile_f685ee1d45648191b90d496199473e74`; recorded Library version 0; evidence AV-20261005-072
  - SHA256 `fc744338f5e3d10798be195b814f7a471a94f3cea7296e1cd1b8578e07b57526`
- **Twin Realms - Source and Guide v1.0.1.zip**
  - Library `libfile_93939b2588c8819181e5ca121e773b8b`; recorded Library version 0; evidence AV-20261005-072
  - SHA256 `e5db864a74f2bfbf29b4a7d00b54dc063642a6ea10fef8d04926703ef66015c1`
- **Twin Realms - Music Source and QA v1.0.zip**
  - Library `libfile_4cf39515ac248191827ea606edb78098`; recorded Library version 0; evidence AV-20261005-073
  - SHA256 `726390b0acebdff621f88ab86540102cc013d00081bd6303b42d00f8777c84fb`
- **Actual Video Frame Review Pack.zip**
  - Library `libfile_92308e4380288191a1a6052e537e5a1f`; recorded Library version 0; evidence AV-20261005-074
  - SHA256 `6e9d074fc495f3e1b20233e24a81b4197bfecb143ee53a059ae4df8dc2540329`
- **Adversarial Review Configurations and Questions v1.0.0.zip**
  - Library `libfile_3c1d6989163c8191afaa24ad0c868808`; recorded Library version 0; evidence AV-20261005-074
  - SHA256 `e42106fc67003cf15217ad857e2acbeeec438d1a2478223ad3914eb40a868314`
- **Twin Realms - Play v1.0.2 Source Fix Candidate.html**
  - Library `libfile_289f2fddaa40819197b20a4d0c88f896`; recorded Library version 0; evidence AV-20261005-074
  - SHA256 `4987b22b981a8856296001be778e5e5a5acbaed5a237f918e034fd57ff257d2a`
- **Twin Realms - Source Emulation Review v1.zip**
  - Library `libfile_59a6433b2fc481919c72ca0f08fdd657`; recorded Library version 0; evidence AV-20261005-074
  - SHA256 `504bec2268ac562a570fe9ed1bb9f55406b2c398250c64fd27c5bf65ea51c486`
- **Twin Realms - Source v1.0.2 Source Fix Candidate.zip**
  - Library `libfile_706a394b6b208191b69d799e6a10e3d2`; recorded Library version 0; evidence AV-20261005-074
  - SHA256 `19bcdd011e99d06ec77fdc13e71b8ce93e435824211749d1be9bc7a8b8fe8ba5`
- **Wind_vs_Gusts_Source_Captions_and_Social_Pack.zip**
  - Library `libfile_d04f591ed1648191ab9f4d7265054ee4`; recorded Library version 1; evidence AV-20261005-075
  - SHA256 `fee4c910b2e40526ea1b0c0f4db29afeab6bf208161853da50542f344905f09f`
- **Cinematic_Background_Factory_Source_and_Presets_v1.zip**
  - Library `libfile_c81461d095b48191adfca346c531557d`; recorded Library version 0; evidence AV-20261005-076
  - SHA256 `49655e8cdc4e4f3c83e286c8f3d888003c789708e153277e0ffa4b4b65ab98da`
- **History Reel Factory - Source and QA v1.0.zip**
  - Library `libfile_6a2123b7034881919bc88a83d3b8100f`; recorded Library version 0; evidence AV-20261005-076
  - SHA256 `d3d0edc25435d74a75cdcdbff0ac1fccdeddaf0e118cba60d1a548e7d7623b57`
- **Moonlit_Range_Layered_Polish_Source_v2.zip**
  - Library `libfile_19a7c43c509c8191b4abfcd408321603`; recorded Library version 0; evidence AV-20261005-077
  - SHA256 `9385c0ab2aa6645aa41bdaf1ae65ab9a8f9f480c8bdaece26d6e98a8f2f10870`
- **Moonlit_Range_True_3D_Source.zip**
  - Library `libfile_9c79c55446f08191a36647b19a2eea37`; recorded Library version 1; evidence AV-20261005-077
  - SHA256 `bee2422f9b0a545428cc226a94e20de4a4b03d857a2094cde00944e0e2c2ea4d`
- **atlas_editable_3d_source_and_layers.zip**
  - Library `libfile_d0bd7f68dff88191b991777e1322ff00`; recorded Library version 0; evidence AV-20261005-077
  - SHA256 `18254d0e8fd245d37e37201cc9eb510cf233fde1e9892546bcdfd6acf09294fd`
- **Moonlit_Range_Full_Film_Editable_Source.zip**
  - Library `libfile_e1c7fbd937508191a88cdd109595986d`; recorded Library version 0; evidence AV-20261005-078
  - SHA256 `76a654036c113ea20fc36af172576a5e90664060ee3b0dc1bf41310d2fd962de`
- **Five_Hidden_Symbols_Editable_Source.zip**
  - Library `libfile_2b009b5620f08191ac07553b6707457a`; recorded Library version 0; evidence AV-20261005-079
  - SHA256 `7cd449e67f20051e5ffc3beee4177acb6319d1544e084879e6483e46eb0c9908`
- **Layered_Lake_Factory_Three_Styles_Source_and_Plates_v1.zip**
  - Library `libfile_6d9442214304819196f55ecc2df2b257`; recorded Library version 0; evidence AV-20261005-079
  - SHA256 `0ee04c253c53d13ebba5670c7ed8769440671bd7a3e62333794bb4ac4de6c9db`
- **Relationship_Reflection_Editable_Source.zip**
  - Library `libfile_576f50fdf95c819188d386e44c503e4e`; recorded Library version 1; evidence AV-20261005-079
  - SHA256 `9d50f1a44ba34ebb9239c6568aa31954f462522ee790b1201c5e906bed539244`
- **Lake_Composition_Dependency_Snapshot_v0.1.0.zip**
  - Library `libfile_71c449aef1a08191ae9f1b2dd0256a44`; recorded Library version 0; evidence AV-20261005-080
  - SHA256 `1d296d94ea04a1bf499452556b409ad752f28964093b853d3c7e29dfd4b8d176`
- **Moonlit_Range_66s_Editable_Source_And_Recovery.zip**
  - Library `libfile_a31e5c2e0b1c819191141357cd2d11c5`; recorded Library version 0; evidence AV-20261005-081
  - SHA256 `95a032fd93f1983d3633ea6d76f36bb289c9d408c23a48a993e0d15491a8d2c3`
- **Moonlit_Range_Lighting_Test_Editable_Source.zip**
  - Library `libfile_9e969b0f78748191a5cc3c3b300b308e`; recorded Library version 0; evidence AV-20261005-082
  - SHA256 `ade700deaf5473f911490e8791e6446015d9a1e6b499520b1b98acc8ac130754`
- **Puzzle_Dependency_Consumer_Check_v1.zip**
  - Library `libfile_f07c84b6c79c819180f25a1d89850d4b`; recorded Library version 0; evidence AV-20261005-083
  - SHA256 `03c94459138a49ba5ebdef6f8361856cf07152f2065a91e37cb4169dbd0b0062`
- **Moving_Background_Videos_Editable_Source.zip**
  - Library `libfile_a056af9019dc8191b0ce20f9fee76b7e`; recorded Library version 0; evidence AV-20261006-086
  - SHA256 `b8e06f300c641778126031ac9652ddd31c0fc4e509c11597543e51a09f8cebd2`
- **The_Small_Things_V4_Motion_Editable_Source.zip**
  - Library `libfile_465c07a422e881919670aea247c194b1`; recorded Library version 0; evidence AV-20261006-087
  - SHA256 `f868d4f373736a6b57871b6dc7a45991a2eadc8626388317c9468d065d572fc9`
- **Video_Recipe_Factory_v2_1_Editable.zip**
  - Library `libfile_9d157cd0e12c8191b1dfefba33d73b7a`; recorded Library version 2; evidence AV-20261006-087
  - SHA256 `37fd8478ad314cad4b235154106311b3fff63e39eda0107d66443ca720d6b6f0`
- **Hexhaven - Play.html**
  - Library `libfile_fa70deb6f03481919610eb5a5951e880`; recorded Library version 0; evidence AV-20261006-089
  - SHA256 `a11c5a78ef1836ab56e76f5db0cdcf0f9b4e3be62cc5a57f84b3262a2285492e`
- **Hexhaven - Source and Verification.zip**
  - Library `libfile_1deca31f62cc8191bbe715b091fa7cae`; recorded Library version 0; evidence AV-20261006-089
  - SHA256 `572c678fef891dee1e4d2c31f3136f7d9ea406d85ebc650f4b641e8e0e54bc22`
- **Hexhaven - Second Shore - Play.html**
  - Library `libfile_94efec31172c8191a4836b27b93ef470`; recorded Library version 0; evidence AV-20261006-090
  - SHA256 `a8f9774cf20f4f9efc34c30ac726316efb99626f1fc94ba1ee01b4a142b1e813`
- **Hexhaven - Second Shore - Source and Verification.zip**
  - Library `libfile_7965d365dc0c8191a19670873e30bd15`; recorded Library version 0; evidence AV-20261006-090
  - SHA256 `459b44547fca2b233520e3d84801048a99c3f55c155c2df0741b0bfe7f208e00`
- **Font_Environment_Validation_v1_20261006.zip**
  - Library `libfile_d4a27222aa28819183c7fd46e8ce27bb`; recorded Library version 0; evidence AV-20261006-091
  - SHA256 `f1f8657f9cfeb7cbc304314db92eabe81249d16d607246583bfa21fa70b759e1`
- **Hexhaven - The Long Horizon - Play.html**
  - Library `libfile_17237f6ac5a08191a048f0f60af55c5b`; recorded Library version 0; evidence AV-20261006-094
  - SHA256 `7f15fec3d35b930a7d9ec25d84e5b8a986976b17bf122f986573653f3a4a59ab`
- **Hexhaven - The Long Horizon - Source and Verification.zip**
  - Library `libfile_f3793d091e6881918390a191f25d15d8`; recorded Library version 0; evidence AV-20261006-094
  - SHA256 `fbb7cb93317afc621bcd886338b843e436cb47264854c036225ff9ddc3cf08b0`
- **Hexhaven - Ten Million Horizon - Play.html**
  - Library `libfile_bb2e74ee41748191a43c0cc0fb1e0f21`; recorded Library version 0; evidence AV-20261006-095
  - SHA256 `1acf945b9a0a97a901b0aec2e52f90166ad93732c5dfdabab2ad511cc0ed3230`
- **Hexhaven - Ten Million Horizon - Source and Verification.zip**
  - Library `libfile_91d502cb519c81918d109ca037ab2ff3`; recorded Library version 0; evidence AV-20261006-095
  - SHA256 `4fb9f10521fcd221bda1aab89e192240fe83cb26cb9ec39ce6b4646e8cfc6217`
- **Baltor_Hexhaven_Source_Review_Reuse_2026-10-06.zip**
  - Library `libfile_62c625fc3f6c8191a761cf81ad207167`; recorded Library version 0; evidence AV-20261006-096
  - SHA256 `71562313596a09295ad41f74e860ff6ee43327bd68745bda906988dd0fb10d6f`
- **Hexhaven - Far World Journeys - Source and QA.zip**
  - Library `libfile_8dd44e994ae0819191cca013906a89b6`; recorded Library version 0; evidence AV-20261006-097
  - SHA256 `be0b136606409d69644d71e5448ef71435242fb2ce1a11d8261f40fe78f05af8`
- **Story Composer v1.0 - Compact Source and Templates.zip**
  - Library `libfile_e5a0a9d00f6481918cad9c5309bde061`; recorded Library version 0; evidence AV-20261006-098
  - SHA256 `ee3c428f5cf0d4e0125ccc2976ab206480cfa9feb16f9b13e8bd4084c3230276`
- **Story Composer v1.0 - Source Presets and Guide.zip**
  - Library `libfile_c9b24282c8908191ad242cca5ba330b8`; recorded Library version 0; evidence AV-20261006-098
  - SHA256 `2d74174efcd3d6ea94480f3de18146ffefbb6139ea49e996bfd72a8c6f5ff4e3`
- **Worlds - City and Landscape Posters - Six Images and Source.zip**
  - Library `libfile_9b81ddcd3f448191af049242783b4b43`; recorded Library version 0; evidence AV-20261006-100
  - SHA256 `1e86ab10d827dae40356c4da061aec3a4b2f8a6d59a40e3bf1ea42ec4ad4623a`
- **Worlds - Complete Ten Format Collection - Source and Verification - Final.zip**
  - Library `libfile_1a491fb45b848191ad55a191d79aed87`; recorded Library version 0; evidence AV-20261006-100
  - SHA256 `136324dd53d62e99aaa2ab9afc80f2ae4496554a2eac2b1f0827bc691804135a`
- **City at the Water - Street Dispatch - Play.html**
  - Library `libfile_9708d25936e48191bbbad5adabd9bb1b`; recorded Library version 0; evidence AV-20261006-101
  - SHA256 `aff624eb0c251b90f4eb469757e7012e12748a6af202fb247c2efddd18046403`
- **City at the Water - Street Dispatch - Source and Verification.zip**
  - Library `libfile_8dcf98600e5c8191ab5ea8d770ccf128`; recorded Library version 0; evidence AV-20261006-101
  - SHA256 `cbea8d062f7b5df2c43980edd5461d589f1fdeaa07afba15034cd32007703b2c`
- **AgentSignals_Offline_Ingestion_Pilot_0.1.0.zip**
  - Library `libfile_d28b8f03ca908191809227173cd993db`; recorded Library version 0; evidence AV-20261006-103
  - SHA256 `b249e4a4306e2b38b5e653cf354fee55c4c6614db7e1bab0ed477150c59e1409`
- **Mesh Avatar Studio - MP4 Production Handoff.md**
  - Library `libfile_fc831040c4708191b7f6f8e9fa32dda5`; recorded Library version 0; evidence AV-20261006-104
  - SHA256 `9b4e46139b7010620a32cc99ecd129bc73d16b81eaa2801b04c58a2a552e6cb0`
- **The Last Signal - Editable Avatar Project Draft.zip**
  - Library `libfile_17e678c9a2ac81918e0c333c9dc767d2`; recorded Library version 0; evidence AV-20261006-104
  - SHA256 `1c5d66d82396db7fca2c36711c724b220b7f325a6557e88072bb2ae31aecefee`
- **mesh_portrait_source_and_proof.zip**
  - Library `libfile_72db3c180a6c8191be3920dba7e501e8`; recorded Library version 0; evidence AV-20261006-105
  - SHA256 `37293daa66d8c570934b6658d94b68d4565f39e9e6d62b8365bfbc4285c54bca`
- **Fact Vault and Girl Facts - Reusable Source Captions and Sources.zip**
  - Library `libfile_efbc0133e2f881918d0cc8af62691112`; recorded Library version 0; evidence AV-20261007-108
  - SHA256 `5c486e279ecbce41d7ddcd18916bb292131b9691abf9310857d0d0d9826fcbc0`
- **Four Portrait Films - Source and Proof.zip**
  - Library `libfile_e3f1a9bfc2a481918e61eb62ed27fc31`; recorded Library version 0; evidence AV-20261007-108
  - SHA256 `caa0a18da6531c7dd9ffd794f46ae4945f3c1841425b5feac46c0afeed8994b0`
- **Motion_Fields_Source_64s.zip**
  - Library `libfile_fd6dd3d094c881919ff34ef438cf8a51`; recorded Library version 0; evidence AV-20261007-108
  - SHA256 `ae122c822bea3553004e98916636203ab38850f0256fb0b8225bbb81211ddf2f`
- **improved_photo_avatar_compact_source.zip**
  - Library `libfile_8e720ecd371881919528ce3c90a65ca4`; recorded Library version 0; evidence AV-20261007-108
  - SHA256 `92b8d93613910521a8d5627a3c61d5a7259d920a9715dd9ed971c7e305bdc3a5`
- **improved_photo_avatar_source_and_proof.zip**
  - Library `libfile_b3c9b9d537988191a3fb0f3cc4654104`; recorded Library version 0; evidence AV-20261007-108
  - SHA256 `c89fb848278fa0c2c16ad8383c690c6a81f99463d1c89a9281a7b5c47ace5e32`
- **portrait_three_models_source.zip**
  - Library `libfile_360e7e1f88708191acbddf875d681f68`; recorded Library version 0; evidence AV-20261007-108
  - SHA256 `ddd4dde86316a8281e7634e5838fd87c4ac472cc83ca3a9bd78d938bb343b1f2`
- **Frame Foundry Studio 0.2.0 - Local App Source and Verified Previews.zip**
  - Library `libfile_e83984f5d2ec81918a963a42b8d36a2b`; recorded Library version 0; evidence AV-20261007-109
  - SHA256 `15266ce07c150a96aea65e4a6dfbac51d042ff7a80f75fd46b1ae8187d58ca9b`
- **Local Video Factory 0.1.0 - Compact Source Specs Tests and Guide.zip**
  - Library `libfile_f15a107e9f588191b026430000bd4705`; recorded Library version 0; evidence AV-20261007-109
  - SHA256 `78ca17968db4499cfa34aab83600479e35eccab3f72268ff32225d45f7c5d5f7`
- **Local Video Factory 0.1.0 - Source Assets Examples and Guide.zip**
  - Library `libfile_3f73d2ee206881918cb5acc9717c1135`; recorded Library version 0; evidence AV-20261007-109
  - SHA256 `d4bf65bf10208367e51fb622540a114ff4a9ed4442d294afba38e666fd0ed45f`
- **The_Harbor_They_Brought_Source.zip**
  - Library `libfile_d21a63009fb081918913b13a6aa0490c`; recorded Library version 0; evidence AV-20261007-111
  - SHA256 `bb6371a7d9c66750ec8ba40d1e22ecd28f96f74c4410c77ad2ef067ae22e4e96`
- **Venus Cinematic - Source Captions and Provenance.zip**
  - Library `libfile_0b2175a69ee48191913b44231392ab2e`; recorded Library version 1; evidence AV-20261007-112
  - SHA256 `8a55e13d31015b266f5717e92113acaf80366d047212d02e25ce21721317290f`
- **Eight Original Formats - Compact Source and Assets.zip**
  - Library `libfile_8a2a93f854fc8191a3b0f54cbba7e308`; recorded Library version 0; evidence AV-20261007-113
  - SHA256 `8f2f640b5eb9f131e85945c3e2b627ceb4a76e7c0226123ac1a4fe2819a94448`
- **Eight Original Formats - Source and Templates.zip**
  - Library `libfile_6310e7fd28988191ba04a47293c903df`; recorded Library version 3; evidence AV-20261007-113
  - SHA256 `2d9b7a2ac850330bf8b37de4b7e7bded337eac9911176a9f6e1b7ac26a3579ac`
- **Centered Layout - Independent Reuse and Guard Proposal.zip**
  - Library `libfile_f077eac68aa88191bb41a285f745d466`; recorded Library version 0; evidence AV-20261007-114
  - SHA256 `3d102d289557b14fc520f6779fc3fbac410ef7dd948c0824abe1075df4eee883`
- **Centered Films - Initial 64s Batch Source.zip**
  - Library `libfile_7f93b5151400819183484308c1bb3576`; recorded Library version 0; evidence AV-20261007-115
  - SHA256 `452e8ef581f1367a19a458409efb1d9830e47a3f62b374035af8a487a2c3c05f`
- **After the Rain - Detailed Source.zip**
  - Library `libfile_8f3b611a913481918cfa3e2ac217d47e`; recorded Library version 0; evidence AV-20261007-117
  - SHA256 `6f43c2e4fe2524925174e8411ddd1c164831bcebb1464109f7e4ac94083fc50b`
- **When Waves Meet - Editable Source and QA - Final.zip**
  - Library `libfile_b1747a6cd57481918047e75cb81880e1`; recorded Library version 0; evidence AV-20261007-118
  - SHA256 `6cf7433ce0e3dbd0b8e6d35199952aa0ab29087f8551848efa8df56425581150`
- **The World Through a Pinhole - Editable Source.zip**
  - Library `libfile_57048ab210788191b50ea900e5a2211f`; recorded Library version 1; evidence AV-20261007-119
  - SHA256 `7c729ec30e19c2444f1997f6aef112d89e4e8663afe5724d704ec19a0505b830`
- **Fact Films - Reproducible Source and Evidence.zip**
  - Library `libfile_5c3b89d879148191b3c19dd5e7539376`; recorded Library version 0; evidence AV-20261007-121
  - SHA256 `349b96fa648b47d5bce419b37a2eee0ed5e942c680d6852b5403577929c95313`
- **Moving Border 1.0 - Source and Templates.zip**
  - Library `libfile_1a7b32101b1c8191a11dbaef207baffe`; recorded Library version 0; evidence AV-20261007-123
  - SHA256 `b0d531853a4f1e099026af2daa2f343a959a1e5198816571b8fe53c3247453ae`
- **expanded_optics_source_evidence.zip**
  - Library `libfile_5caa5ea3fbd88191bdb00cc86814075e`; recorded Library version 0; evidence AV-20261007-123
  - SHA256 `bf6aa5e08a3e2279d7a23566b6e239ca69401a3d021b580b6d06d6f2927337ac`
- **Three Small Wonders - Source and Evidence.zip**
  - Library `libfile_0db0d8029d7481919c3a82557ddb51c8`; recorded Library version 0; evidence AV-20261007-124
  - SHA256 `0b537c8fd2476a08d8d5ccc5320d60214bdc3ae6f7709c08c3ce45a739050d2c`
- **FastMCP_Review_Evidence_and_Edit_Package.zip**
  - Library `libfile_ae7d0a8431288191aaa94673feb142bb`; recorded Library version 3; evidence AV-20261008-125
  - SHA256 `c9d2f74bb288da31746748c9481954b63ba7061d5854e692351787e23f39ad8e`
- **01_Baltor_Campaign_Angles.md**
  - Library `libfile_3563460b55548191a19bdb5c3096e851`; recorded Library version 1; evidence AV-20261008-128
  - SHA256 `bc287d0a3e7d9789653d28cc47216815ebca4f4ba24820a9f6970ad544ad61c7`
- **02_Baltor_Social_Copy.md**
  - Library `libfile_542a81ac53c481918c9f30f34ab36485`; recorded Library version 1; evidence AV-20261008-128
  - SHA256 `e5ab18310568177239847f6062872a611f06946969df4c35e7a3449447fc6d1b`
- **03_Baltor_Landing_And_Onepager_Copy.md**
  - Library `libfile_23358bfe60f88191824d596bb597cb81`; recorded Library version 1; evidence AV-20261008-128
  - SHA256 `accc62dca80889093b5d29af23745d369d78f2e9823f74abbadafcaa8335841d`
- **04_Baltor_Showcase_And_Repurposing_Guide.md**
  - Library `libfile_906f194fdba48191b27767a7ffebd910`; recorded Library version 1; evidence AV-20261008-128
  - SHA256 `232135a0462e23cc1438647513d240b7b76b679a3f05cb32f7da4bfa678326ca`
- **05_Baltor_Claim_Evidence_And_Review_Notes.md**
  - Library `libfile_313af59076f08191aaea6885c3b76aa7`; recorded Library version 1; evidence AV-20261008-128
  - SHA256 `cfd37a36b413f357386bde38c444b123c462fdcf6a6305462443ef92a23e9665`
- **Baltor - Compact Lossless Film Source - 20261008.zip**
  - Library `libfile_c08a044a9bac81919c2662aba4eabb58`; recorded Library version 0; evidence AV-20261008-128
  - SHA256 `ffe793a2f0aeb07f185649b6655fce12bcb82eadb11d57514c5645e3deb00070`
- **Baltor - Evidence to Reuse Films - Source and Proofs - 20261008.zip**
  - Library `libfile_2827115f00408191b9f3ae233916990a`; recorded Library version 1; evidence AV-20261008-128
  - SHA256 `8c849e8a633681b2df694a12d640213d8e4c10572d328f6ed9566e1a996dac5d`
- **Baltor_Marketing_Showcase_Companion_20261008_Private.zip**
  - Library `libfile_f87d42a4d1c481919d256c73c723ff26`; recorded Library version 1; evidence AV-20261008-128
  - SHA256 `7aaf0fc89f11bb1474e28493758c87f2b4b2533f5c8618286b75be252a412fa0`
- **Baltor - Photorealistic Films - Editable Source and Narration Handoff.zip**
  - Library `libfile_1e7f8428f4248191a71d0e22b88ba5fe`; recorded Library version 0; evidence AV-20261009-129
  - SHA256 `f6e7cdc620e0d1117d884305873c779dd82d9acb863c720c73ec73c5c9da8e79`
- **Baltor - Two New Photographic Stories - Editable Source.zip**
  - Library `libfile_d6c5ae7eae0881919ea3674e3a1601cd`; recorded Library version 0; evidence AV-20261009-130
  - SHA256 `46ec98ca2898128e7669a1c80b00eb03d6b985546f2401bedd4011dd660c40d7`
- **Studio_Six_Cross_Engine_Asset_Kit_v1.0.0.zip**
  - Library `libfile_7ec958154ca08191afa1669eebcb1e97`; recorded Library version 0; evidence AV-20261009-131
  - SHA256 `5d41da15b9531147bec78950b39cd840ebaff4034dc0c76fa040d0f39e30175d`
- **Glasshouse_Nine_Cross_Engine_Asset_Kit_v1.0.0.zip**
  - Library `libfile_51d9f86009708191ade0534cf4a530a4`; recorded Library version 0; evidence AV-20261009-132
  - SHA256 `cb56c2b30c965e66f8a11c370d3584bdc73471a71548a36af40f5d790e5f650a`
- **Cedar_Vale_Complete_Game_House_Kit_v1.0.0.zip**
  - Library `libfile_9bf6405627e08191b53e8a2569620ecf`; recorded Library version 0; evidence AV-20261009-133
  - SHA256 `f3e97a304c2a5b73402b47f5fd7e8633c1469b8bcff7eff627ac7fe332dbd1b6`
- **Willow_Gate_Obstruction_Addon_v1.0.0.zip**
  - Library `libfile_b0a69723fce48191bf05058565077a8e`; recorded Library version 0; evidence AV-20261009-135
  - SHA256 `3eaaaabf814e7c0c92a6b4cbd5fe0c0e5bfae4de1e7c4b172f1b2ddb8cbc2da8`
- **Tidehaven_Eight_Godot_Waterfront_Kit_v1.0.0.zip**
  - Library `libfile_5a282ca01f88819193b8a221fc4e81a5`; recorded Library version 1; evidence AV-20261009-136
  - SHA256 `88ed229d57b342de34cfc6115270087d302c58dc007b79205e58e1294c2a5b47`
- **Willow_Gate_Godot_Garden_Kit_v1.1.0.zip**
  - Library `libfile_a17474978e488191a1e7c0736b465848`; recorded Library version 1; evidence AV-20261009-138
  - SHA256 `1e5ed7d2b267f59511fd0a3c62115dbbc54ae810b34de48dd1a93c0ae7288419`
- **Brasswick_Six_Godot_Interaction_Kit_v1.1.0.zip**
  - Library `libfile_7e1bc189b48081918adf007c75c2a003`; recorded Library version 1; evidence AV-20261009-139
  - SHA256 `83de520134cd6e97eb7995fbc193574b23d2b61ef9f719d3dbb65a7b78d19692`
- **Cedar_Vale_Estate_Detailed_Garden_and_Flooring_Kit_v1.0.0.zip**
  - Library `libfile_1d3d2c0d93e08191aa6b2f3698a71824`; recorded Library version 0; evidence AV-20261009-143
  - SHA256 `b551ea376d2288b2ce2d6e1c703fecb56ae5f3d636fadef9dc947d34bf275be4`
- **Cedar_Vale_Estate_Detailed_Kit_Compact_v1.0.0.zip**
  - Library `libfile_97c5164c51848191bdc42bdcab6978e7`; recorded Library version 0; evidence AV-20261009-143
  - SHA256 `8c8220d6eb230f99aeec846df309cbb885aedb20405b314130ebdd2d0f626416`
- **Cedar_Vale_Garden_and_Flooring_Compact_v1.0.1.zip**
  - Library `libfile_95d2198324708191a16a155f9a1a63a3`; recorded Library version 0; evidence AV-20261009-143
  - SHA256 `d9b04caae2b879271105b55ae36e7ecbd7b23d3f43d4e44435b615dc55b1d0e5`
- **Cedar_Vale_Garden_and_Flooring_Concept_v1.0.0.zip**
  - Library `libfile_65061fb00a4c81919e8582f2b81ffc88`; recorded Library version 1; evidence AV-20261009-143
  - SHA256 `c96ba017ccc44b5fcd9a908ed7352f6d664eded9a0326eaf6252e60e49f16720`
- **Cedar_Lavender_LOD_Addon_v1.0.0.zip**
  - Library `libfile_7c853861e388819199bb5d55b24c4cec`; recorded Library version 0; evidence AV-20261009-145
  - SHA256 `a0ab2554f94c6c5d875ed9f3b4927d482199f54fda469fbd97ca512f18812685`
- **Top_5_Girl_Facts_Editable_Source.zip**
  - Library `libfile_c9795118f65c8191a78271d030d11843`; recorded Library version 3; evidence AV-20261009-146
  - SHA256 `b0cac493facb34837f83acdb61008d0832ef41468e3e3ede06524008b3a61ea5`
- **Cedar Vale - Tour Editable Source.zip**
  - Library `libfile_0c5516284dec8191a77c6b2d7b82c60a`; recorded Library version 0; evidence AV-20261009-147
  - SHA256 `5a684bf36e63b97fd987f0a595a096aa6140f5e7f59955759cc48f8aba7448bb`
- **Cedar_Lavender_Care_Editable_Source.zip**
  - Library `libfile_adb607de12f881919a2ab4db6c3a6278`; recorded Library version 0; evidence AV-20261009-147
  - SHA256 `390c91ab5edd1c6cf1056d72f7486d7a476ab75caa605b0ae574233a58decb9d`
- **Cedar Vale - Five Tour Edits Source.zip**
  - Library `libfile_a1dbd6f0e3908191b18b80110eff77a6`; recorded Library version 0; evidence AV-20261009-148
  - SHA256 `d27d5d9348cc12abd7e9a73807ef64859ccf903208e07adcab250095da9f25ed`
- **Cedar_Lavender_Five_Care_Editions_Editable_Source.zip**
  - Library `libfile_46a8858a2bc081919f69c95bea84557c`; recorded Library version 0; evidence AV-20261009-148
  - SHA256 `6f4fa2d3f1662466605412fe9038b9a6f6d14e2a99897639e57d24a7e7fb030c`
- **Cedar Vale - 2.5D Depth Tour Source.zip**
  - Library `libfile_3b3de527c790819188b623dd8a627929`; recorded Library version 0; evidence AV-20261009-149
  - SHA256 `f4ac7db98c13d7b4089992b1382431b7517013d54522cf6d9a815b9706524919`
- **Cedar Vale - 3D Scene Source.zip**
  - Library `libfile_f224b72f6b50819190244ead7434fe7b`; recorded Library version 0; evidence AV-20261009-149
  - SHA256 `f43453e4013223217a0b2b3e5a6a56050bad85bf81b89d644d85b2068b65ddba`
- **Cedar Vale - Depth Film Editing Source.zip**
  - Library `libfile_ee46c678f0908191aad1cdc13b34f61a`; recorded Library version 0; evidence AV-20261009-149
  - SHA256 `2234e8c5e32c703284c3ddb897e6ce88a903b00556d5083de0b66f08524fb211`
- **Cedar_Lavender_Actual_3D_Pilot_Editable_Source.zip**
  - Library `libfile_77a23e7cd7b88191b6a208640d03b9b8`; recorded Library version 0; evidence AV-20261009-149
  - SHA256 `daaf280d22fbd03684cd8d89f46e37d2c81b685f9ab602e98a644ec33d83a5c9`
- **Girl_Facts_15_Creative_Versions_Editable_Source.zip**
  - Library `libfile_42eabdeb9878819181e12217ff6b0096`; recorded Library version 0; evidence AV-20261009-149
  - SHA256 `a14a34689a82888c1f7441ce427e4579072f34ede15012e81d2626952df13382`
- **Cedar_Irrigation_Addon_v1.0.0.zip**
  - Library `libfile_ebf2e028d934819190442fabc2ab6a65`; recorded Library version 0; evidence AV-20261009-150
  - SHA256 `67605be69e69ea64c40cd4d3dabe2bce6dcc10baad4c89ab7877f304c11e9c17`
- **Cedar_Irrigation_Quickstart_v1.0.0.md**
  - Library `libfile_db256b864bbc81918f279119362e4abd`; recorded Library version 0; evidence AV-20261009-150
  - SHA256 `d26eb42e1f77b8e647848a35664b0b4f9652caaa7c6ad03c91375ebcb45ee3da`
- **Cedar_Pump_Station_Quickstart.md**
  - Library `libfile_a1800e690638819198a86c30d8a4fe4c`; recorded Library version 0; evidence AV-20261009-151
  - SHA256 `24d9631ef0800f53675d36e1e88eff634bf0f6b143fc3fc2174e9fdf2b7a1ab0`
- **Cedar_Pump_Station_v1.0.0.zip**
  - Library `libfile_fe45374afc808191b702c244ca3e667f`; recorded Library version 0; evidence AV-20261009-151
  - SHA256 `1d67cbacbf2ac1f5bd6100377ebde8e25166dad5f3cd307fd49a71bde2e074d4`
- **Baltor_Cedar_Dependency_Reuse_Review_1.0.0.zip**
  - Library `libfile_85e2a53cba3481919dacc9cbccd53622`; recorded Library version 0; evidence AV-20261009-152
  - SHA256 `acfbfe1b18b2ff3a29e3bba4e545fe72bbce42c56dcfc2770bf939797f2e2bd9`
- **Cedar_Utility_Rack_Quickstart.md**
  - Library `libfile_b19b15dfd1c48191ae561bd2b4b7ae2e`; recorded Library version 0; evidence AV-20261009-153
  - SHA256 `d1c2c71a8c618a2dbbb1152607443ab10e88cb32921b5f59cecef0c9aca19837`
- **Cedar_Utility_Rack_v1.0.0.zip**
  - Library `libfile_63729c76591c819181c75a249990ef31`; recorded Library version 0; evidence AV-20261009-153
  - SHA256 `424a317b54805e1f4137cdcd6f5aa41c7d8bef2f0598d0a7a18dda306d757136`
- **Cedar_Registered_Rack_Guard_Quickstart.md**
  - Library `libfile_e9db60a3630881918a46f7f285c9760c`; recorded Library version 0; evidence AV-20261009-154
  - SHA256 `855284201db930d56c50950f8f30a86cfa74fab867a5c2a5a6cc4916715cf9de`
- **Cedar_Registered_Rack_Guard_v1.0.0.zip**
  - Library `libfile_3ea4d0ec60808191a2b8116b733b6d20`; recorded Library version 0; evidence AV-20261009-154
  - SHA256 `41989b0149db1b10fb9b10cc39f5eb130b1f9d77ce6e47dc56920ad14fb572e5`
- **Cedar_Wall_Clock_Quickstart.md**
  - Library `libfile_5a4d92e79138819181e3b4973a9e3571`; recorded Library version 0; evidence AV-20261009-155
  - SHA256 `a3e44af14d1de11773fea44816dd35f9777cb9a340a1b93166e643754074fe26`
- **Cedar_Wall_Clock_v1.0.0.zip**
  - Library `libfile_25f918fac2ec819199fbcbba71046668`; recorded Library version 0; evidence AV-20261009-155
  - SHA256 `c3b4e0403351b0e72380a026b63f90eba15721b057e6596ac6a928abedfa310a`
- **Cedar_Kitchen_Clock_Integration_Quickstart.md**
  - Library `libfile_7d189b6847f48191b126c076a25af9ba`; recorded Library version 1; evidence AV-20261009-156
  - SHA256 `fb1a1a9bf93beff0d2680dfc4661627ecc44f07914771873dba8672862bc656c`
- **Cedar_Kitchen_Clock_Integration_v1.0.0.zip**
  - Library `libfile_2ed41424400881918f2077d654263a09`; recorded Library version 1; evidence AV-20261009-156
  - SHA256 `3181b7cd8386fc60ad85bce719cba2e5a617a2f319a971971356438e3d081a6f`
- **Cedar_Review_Applicability_Reuse_20261009.zip**
  - Library `libfile_958c9f53a92c8191bc6bc13f01fa5d78`; recorded Library version 0; evidence AV-20261009-157
  - SHA256 `fbea3c4c1feb4e28f1cd911bf68b42c34e687902f8eff8b7d7240d40106f7922`
- **Cedar_Roller_Blind_Quickstart.md**
  - Library `libfile_ab336eded8048191bdbcb18aec81ca09`; recorded Library version 0; evidence AV-20261009-158
  - SHA256 `9c308a29bd29de09146110e59ff1b9474b15cc74067f2122c82b8cb027ce5418`
- **Cedar_Roller_Blind_v1.0.0.zip**
  - Library `libfile_e80b95b9c34c8191b43c9c1feaeb0301`; recorded Library version 0; evidence AV-20261009-158
  - SHA256 `d295354879f140e708c479ff09ab548a9926e7cda457aa685b052c8dc4d8fe3a`
- **Cedar_Five_Geometry_Styles_Quickstart.md**
  - Library `libfile_2f3ad66d1458819183515a9a4280d162`; recorded Library version 0; evidence AV-20261009-160
  - SHA256 `a6f6a6be2777b3d1b0247b3573f6a6473840caa23249623825939b6ea5ea9a17`
- **Cedar_Five_Geometry_Styles_v1.0.0.zip**
  - Library `libfile_e0ec703ab2788191bb11f00f681f3a0f`; recorded Library version 0; evidence AV-20261009-160
  - SHA256 `803f718162f0b0745595279852f04b5881c2c86ee9909a1619c0b0c4ecfed23c`
- **Girl_Facts_Image_Led_Production_Source.zip**
  - Library `libfile_bcbf9bc56928819189d6df040ee0b5d6`; recorded Library version 1; evidence AV-20261009-161
  - SHA256 `972f63b55e128e3d94fe3008b22ef113433a086add1ad7042c784bbf11311dc8`
- **Cedar_Vale_Window_Blind_Integration_Quickstart.md**
  - Library `libfile_2dc0c5a975f08191a4cf81357f2462a4`; recorded Library version 0; evidence AV-20261009-162
  - SHA256 `fffc3471acd000daa17a15e5afcf7d2ad7f7b4bd342fb21e1c9f568009408eeb`
- **Cedar_Vale_Window_Blind_Integration_v1.0.0.zip**
  - Library `libfile_6656e9c8539c81918af686f50d03e5f2`; recorded Library version 0; evidence AV-20261009-162
  - SHA256 `5b25a7453e9ac53b1bb0c1ddd0ba98ceb3112422b086012fdcab683e799bb670`
- **Cedar_Room_Survey_Guide_v1.0.0.md**
  - Library `libfile_f61968a391dc819185c2239910bac39b`; recorded Library version 0; evidence AV-20261009-165
  - SHA256 `2b5501d488926ad5a119bfab825c3093b5681009d8d9651919bdd047dd243b2f`
- **Cedar_Room_Survey_v1.0.0.zip**
  - Library `libfile_345a7d3e45b8819185f903261001bdb0`; recorded Library version 0; evidence AV-20261009-165
  - SHA256 `737c53aabf77ca7bf4cc44095bd954cd1e44c3c59db39d925d2b38afda764fc9`
- **Cedar_Surface_Arranger_Use_Guide_v1.0.0.md**
  - Library `libfile_a68c3dd08814819190424bb851a02bae`; recorded Library version 0; evidence AV-20261009-168
  - SHA256 `2b446d3b45936619df5aa81c3f69a22792e8d72754e7b74650fd8b921803e8d5`
- **Cedar_Surface_Arranger_v1.0.0.zip**
  - Library `libfile_b56824812470819189c9e6af814a0247`; recorded Library version 0; evidence AV-20261009-168
  - SHA256 `f349dfcd05f64b9f191684d4edbefc10e79c8c0cf85051a680c8d4a47d99344d`
- **Girl_Facts_Editable_Source.zip**
  - Library `libfile_0bee2caf5ba8819190a65ad8940a42e1`; recorded Library version 4; evidence AV-20261009-169
  - SHA256 `a6cd3c6e9034db4e893de48e0349089c3710e4cef0650a14995c573aea3e5e7f`
- **Relationship_Cost_Correction.zip**
  - Library `libfile_94472942c1088191a8a5b0d52774443b`; recorded Library version 0; evidence AV-20261009-169
  - SHA256 `9933a7f15366a3cbf0f5b8ad68e3ab7406d39f30a5c72a08ec73399656b4e8d7`
- **Cedar_Surface_Arranger_Graphical_Route_Check_20261009.zip**
  - Library `libfile_626fe71f03748191b326feaf2a8b3179`; recorded Library version 0; evidence AV-20261009-170
  - SHA256 `7eb4e8a1cd99643e113abc08d2417fd3231ca4d83209ff5576d32854e69339b2`
- **Cedar_Surface_Arranger_Guard_Use_Guide_v1.0.1.md**
  - Library `libfile_3361c0819e6081918e25ef81fdc1fc5c`; recorded Library version 0; evidence AV-20261010-171
  - SHA256 `86cd89437504ff9d693b1c29a64f3fbb9b9baf7232cf5b0f3cb668532cddc121`
- **Cedar_Surface_Arranger_v1.0.1.zip**
  - Library `libfile_37a2b4d55644819185b8d066bbc1136f`; recorded Library version 0; evidence AV-20261010-171
  - SHA256 `0af1b2bde1b62dc4408be8d88cf11f490620da3fd26750868bec140a3402058f`

### 18.6 Versioning the next revision

Update the same handbook identity when a material result changes: an exact old source is recovered, a new model/tool is actually admitted and run, an interactive route passes graphical review, a new final source is sealed, or owner feedback changes the default. Preserve older evidence and explicitly replace only the conclusions it supersedes. Re-check current upstream license/model claims before adoption; this reference is dated, not perpetual clearance.
