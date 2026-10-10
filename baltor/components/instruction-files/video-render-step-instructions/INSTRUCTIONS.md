
## Video render step

- Read the house rules (`short-video-house-style` skill) before writing any render code.
- Keep a rule ledger: every rule the user states goes in `RULES.md` in this step and is checked before each render.
  A new request never silently drops an older rule; ask only when two rules conflict.
- Deliver full-length exports. Do not send short previews unless the user asks for one.
- Save the editable source and the export to durable storage before reporting success.
- Report measured results only. Write "not checked" for anything you did not measure.
- Do not suggest paid services when an open-source tool does the job. Do not ask for approvals already given.
