# Agent Memory / Lessons Learned

## NiFiKop: JKS Secret Cleanup on Decommission (2026-06-25)

When NiFiKop uses `sslSecrets.create: true` with an external `issuerRef`, the `FinalizePKI` 
function does NOT clean up the per-node JKS password secrets (e.g., `{name}-0-server-certificate`).
These secrets must be manually deleted before redeploying a NiFiCluster with the same name.

Symptoms of stale JKS secrets: 
- `"could not create secret with jks password: secrets already exists"`
- `"failed to decode x509 certificate from PEM"` (cascading error)

Fix: `kubectl delete secret {nifi-name}-{nodeId}-server-certificate -n {namespace}`
