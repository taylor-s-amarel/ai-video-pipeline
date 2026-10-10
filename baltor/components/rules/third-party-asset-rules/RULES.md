
# Third-party asset rules

1. Every third-party file has a manifest entry before it is used: source page, licence, licence URL, exact
   credit line, redistribution status. Check: `asset_licence_checker pack.json --use <profile>` exits 0.
2. Packages and repositories hold manifests, never third-party media. Check: the media-pack commit guard hook.
3. No NonCommercial (-NC) asset in a monetised video, client work or the paid catalogue.
4. No NoDerivatives (-ND) asset is recoloured, re-rigged, cropped into a new model or otherwise modified.
5. Mixamo, BlenderKit Royalty Free, Fab, store EULA and ShareTextures files are project-only: rendered into the
   work, never committed, uploaded or bundled; never used as ML training data where the terms forbid it.
6. CC-BY / CC-BY-SA / OGA-BY / GPL assets get their credit line in the video description or end card and in CREDITS.md.
7. Share-alike assets that you modify stay under the same licence and are kept apart from differently licensed packages.
8. CC-BY 3.0, CC-BY-SA and GPL art is not shipped on DRM-locked platforms; use CC0 or OGA-BY there.
9. Downloads are automated only where the source allows it (APIs, GitHub raw files); sites that forbid automated
   downloads (ShareTextures) are fetched by hand.
10. Every downloaded file has a SHA-256 in the lock file; a hash mismatch stops the build.
11. Trademarks, logos, insignia and recognisable people are not cleared by CC0 or public-domain status.
12. Fair use is never recorded as a licence.
