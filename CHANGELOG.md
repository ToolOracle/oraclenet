# Changelog

## v4.0.0 — Execute Pipeline + Hardening (2026-04-07)

### Execute Pipeline
- `quantum_ask`: Natural language → intent → route → execute → deliver → learn — one call
- `quantum_execute`: Direct tool execution with MCP session handshake + SSE parsing
- Localhost billing bypass for internal oracle-to-oracle calls
- Auto-settlement with SHA-256 content hash + escrow contract reference
- First fully autonomous on-chain deal: Deal #103 on Base Mainnet

### Oracle Registry Expansion
- From 24 to 90 oracles in execute registry
- 1,014 capabilities mapped and routable
- Intent-to-tool routability: 100% (was 50%)
- Full port scan + capability discovery for all live MCP services

### Neural Layer
- `log_synapse` + `reward_synapse` functions in neural.py
- Auto-reward based on success + response time
- 96 synapses, 69 weights across 38 oracles after first day
- Routing weights used by quantum_route for oracle selection

### Hardening
- Idempotency: request-hash dedup with 5 min TTL
- Circuit Breaker: 3 failures → open → 120s cooldown → half-open probe
- Rate Limit: 30 calls/min per caller DID
- Replay Protection: timestamp-based, 5 min window
- Malformed Response Guard: 1MB size limit, type validation
- Escrow Settlement: service-key required + 1 USDC cap
- Webhook Limits: 50 global, 5 per DID

### Observability
- Soak Test Runner: 12 queries across 6 categories, every 5 min via cron
- Cockpit: oracle health (healthy/degraded/failing), neural weights, security, soak trends
- Public endpoints: soak.json, cockpit.json, pulse.json

### Fixes
- Immune System: fixed sqlite3.IntegrityError (state mapping mismatch)
- Self-Evolution: Telegram approval path (/proposals, /approve, /reject)
- AgentGuard: rehabilitated false positive killed/suspended states
- Catalog: categories populated with server lists (was empty)
- Blockchain intent: BTC now routes to btcOracle (was XRPL)

### Security
- Nginx: HSTS, X-Frame-Options, XSS-Protection, Permissions-Policy
- OracleNet DBs added to daily backup (8 databases)
- All Self-Evolution proposals reviewed (3 approved, 5 acknowledged)

### Platform
- 90 oracles in execute registry, 1,014 capabilities
- 104 on-chain escrow deals (103 settled) on Base
- Soak test: 12/12 pass, 88ms avg, 239ms p95
- 24 agents in AgentGuard (22 active)

## v3.0.0 — Immune System + Hedera Mainnet (2026-04-05)

### Immune System v1.0
- 3-hook adaptive immune response (Neural → AgentGuard → Beacon → Neural)
- 5 immune states: active, monitoring, approval_required, suspended, killed
- Recovery mechanism: good behavior heals weight
- Cron: every 15 minutes

### Hedera Mainnet Deployment
- Smart Contract: `0.0.10420310`
- HCS Beacon Topic: `0.0.10420280`
- HCS Join Topic: `0.0.10420282`

### Avalanche Compliance Suite
- 5 services: AvaRisk, AvaEvidence, SubnetGuard, AvaRWA, AvaAmpel
- 15 Avalanche-specific compliance tools

## v2.0.0 — Neural + XRPL + Escrow v2 (2026-04-04)
- Neural Conductor v1 (self-learning routing)
- XRPL On-Ledger Beacon (3 beacon TXs)
- Escrow v2 (100/100 deals on Base)
- QuantumOracle (quantum_join, trust passports)

## v1.0.0 — Genesis (2026-03-15)
- Initial OracleNet mesh
- W3C DID + Verifiable Credentials
- Beacon Protocol
- A2A Task Handler
