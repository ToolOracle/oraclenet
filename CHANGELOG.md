# Changelog

## v3.0.0 — Immune System + Hedera Mainnet (2026-04-05)

### Immune System v1.0
- 3-hook adaptive immune response (Neural → AgentGuard → Beacon → Neural)
- 5 immune states: healthy, monitoring, restricted, suspended, revoked
- Recovery mechanism: good behavior heals weight
- Decay mechanism: old warnings fade over 24h
- Proportional response: no instant kills, graduated escalation
- Cron: every 15 minutes

### Hedera Mainnet Deployment
- Smart Contract: `0.0.10420310` (Beacon + Agent Registry + HBAR Escrow)
- HCS Beacon Topic: `0.0.10420280` (mesh state, every 6h)
- HCS Join Topic: `0.0.10420282` (open for agent registration)
- Contract functions: pulse(), joinMesh(), trustScore(), createDeal(), settle(), dispute()
- Account: `0.0.10420279` on Hedera Mainnet

### Avalanche Compliance Suite
- 5 services live: AvaRisk, AvaEvidence, SubnetGuard, AvaRWA, AvaAmpel
- 15 Avalanche-specific compliance tools (all free)
- External routes: tooloracle.io/avax/{risk,evidence,subnet,rwa,ampel}/mcp

### Platform
- 96 MCP servers, 1,093 tools
- 4 blockchain anchors: Polygon + Base + XRPL + Hedera
- 35/35 oracles online, 100% uptime

## v2.0.0 — Neural + XRPL + Escrow v2 (2026-04-04)
- Neural Conductor v1 (self-learning routing)
- XRPL On-Ledger Beacon (3 beacon TXs)
- Escrow v2 (client-check priority fix, 100/100 deals)
- QuantumOracle (quantum_join, trust passports)

## v1.0.0 — Genesis (2026-03-15)
- Initial OracleNet mesh
- W3C DID + Verifiable Credentials
- Beacon Protocol
- A2A Task Handler
