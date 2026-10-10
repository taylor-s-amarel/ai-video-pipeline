# Proposed agent interface (MCP tools), shared by all awareness builders

feeds.changes(scope, cursor, token_budget) -> awareness_packet
feeds.explain(event_id, project_scope)     -> awareness_project_implication + awareness_next_step[]
feeds.evidence(evidence_ref)                -> evidence excerpt + provenance (short quotes only)
feeds.revisit(decision_id)                  -> events matching the decision's revisit_when conditions
feeds.coverage(scope)                       -> awareness_source_health[] for the sources behind the scope
feeds.respond(event_id, action, note)       -> records not-relevant | already-handled | hold | no-action | accepted

MCP tool names use underscores: feeds_changes, feeds_explain, feeds_evidence, feeds_revisit, feeds_coverage, feeds_respond.
Delivery moments: task-start, task-resume, provider-choice, periodic-review. Notifications carry event references;
agents expand within their budget. Status: proposed interface implemented locally; not a live baltor.ai endpoint.
