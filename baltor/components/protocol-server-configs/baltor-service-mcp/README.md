
# Baltor service MCP connection

Tools served: `intelligence_search(query)` and `provisioning_read(identity, expected_digest)`.
Create one client token per device or tool and keep it in `BALTOR_SERVICE_TOKEN`; the files hold
only the variable name. Check the service first: `curl https://baltor.ai/api/v1/capabilities`.

Until the hosted endpoint is live, the `baltor_local_catalog_mcp` configuration serves the same two
tools from this repository's catalogue over stdio.
