
## Asset sourcing step

- Use assets only through a media pack manifest (`agent_media_pack_manifest`): source page, licence, licence URL,
  exact credit line, redistribution status, SHA-256 once downloaded. No manifest entry, no use.
- Prefer CC0 sources (Kenney, Quaternius, KayKit free tiers, Poly Haven, ambientCG, NASA 3D Resources); CC-BY is fine
  for videos when the credit line is in the description. Never NC/ND assets in monetised work.
- Mixamo, Royalty Free marketplace and Fab files are project-only: keep them in a git-ignored folder.
- Download automatically only from APIs and GitHub raw URLs (the fetcher's allow-list); fetch other sites by hand.
- Inspect every model with `gltf_glb_inspector` (Draco, scale, triangles) and set Godot import presets with
  `godot_texture_import_presets` before opening the editor.
- Report what you verified and how; write "not checked" for anything you did not check.
