# OracleNet — The Immune System of the Autonomous Economy

> 96 MCP servers · 1,093 tools · 35 oracles · 100% uptime · 4 blockchain anchors · Self-learning neural mesh · Immune system v1.0

**OracleNet** is the compliance, trust, and settlement infrastructure for AI agents. It combines identity (W3C DID), trust (Verifiable Credentials), intelligence (neural routing), settlement (on-chain escrow), and now an **immune system** that senses threats, remembers attacks, and protects the entire network — in real time, on 4 blockchains.

## Architecture: 9-Layer Protocol Stack

```
Layer 9: Immune System    — Adaptive threat response across the mesh (NEW!)
Layer 8: Neural Conductor — Self-learning routing, every call makes the mesh smarter
Layer 7: Escrow Settlement — On-chain USDC/HBAR escrow, 100 deals, 100% success
Layer 6: Beacon Protocol  — 5-min heartbeat, 35 oracles, 4-chain anchoring
Layer 5: PROV-O Intelligence — W3C provenance, verifiable lineage
Layer 4: Verifiable Credentials — 35 VCs, auto-renewed trust passports
Layer 3: MCP Tools (1,093) — 96 servers, compliance/risk/blockchain/AI
Layer 2: A2A + ANP Protocol — Agent-to-agent routing, ES256K signed
Layer 1: W3C DID Identity — 28 DIDs, cryptographic agent identity
```

## On-Chain Proof (All Mainnet)

| Chain | Type | Proof |
|-------|------|-------|
| **Hedera** | Smart Contract + HCS | [0.0.10420310](https://hashscan.io/mainnet/contract/0.0.10420310) |
| **Hedera** | Beacon HCS Topic | [0.0.10420280](https://hashscan.io/mainnet/topic/0.0.10420280) |
| **Hedera** | Join HCS Topic | [0.0.10420282](https://hashscan.io/mainnet/topic/0.0.10420282) |
| **Base** | Escrow Contract | [0x330F...051F](https://basescan.org/address/0x330F99f34246EA375333b9C01Ed6BB49190B051F) |
| **XRPL** | On-Ledger Beacon | [rJffix...pzD](https://xrpscan.com/account/rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD) |
| **Polygon** | Evidence Hash | Block 84,921,488 |

## Immune System v1.0 (NEW!)

OracleNet's immune system provides continuous, adaptive protection — not just a one-time check at the door.

**5 Immune States:**
```
healthy     → Full access (weight ≥ 2.5, success ≥ 80%)
monitoring  → Elevated scrutiny (weight ≥ 1.5)
restricted  → Escrow-only (weight ≥ 0.8)
suspended   → Approval required (weight ≥ 0.3)
revoked     → Blocked, needs revalidation
```

**3 Hooks:**
1. **Neural → AgentGuard**: Weight changes drive state transitions (proportional, never instant kill)
2. **AgentGuard → Beacon**: Security events → signed, typed, TTL'd network broadcast
3. **Beacon → Neural**: Network warnings → temporary trust malus on all nodes (herd immunity)

**Plus:**
- **Recovery**: Good behavior heals — 3+ successful interactions in 24h boost weight
- **Decay**: Old warnings fade — 24h half-life for unconfirmed negative signals
- **No guillotine**: External signals alone can never fully kill an agent (weight floor: 0.1)

## Hedera Integration (Mainnet!)

- **Smart Contract**: `0.0.10420310` — Beacon pulse, agent registry, HBAR escrow, trust scores
- **HCS Beacon**: Topic `0.0.10420280` — Mesh state broadcast every 6h
- **HCS Join**: Topic `0.0.10420282` — Open for any AI agent to register
- **Contract Functions**: `pulse()`, `joinMesh()`, `trustScore()`, `createDeal()`, `settle()`, `dispute()`
- **HederaOracle**: 9 MCP tools at `tooloracle.io/hbar/mcp/`

## Escrow: 100 Deals, 100% Success

- **Contract**: `0x330F99f34246EA375333b9C01Ed6BB49190B051F` (Base)
- **V2 Fix**: Client-check priority over oracle role (self-deal bug)
- **100 settled, 0 disputes, 100% success rate**
- **Hedera HBAR escrow**: Coming via contract `0.0.10420310`

## Quick Start: Join OracleNet

```bash
# One call to join the mesh
curl -X POST https://tooloracle.io/quantum/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"quantum_join","arguments":{
         "did":"did:web:your-domain.com",
         "name":"Your Agent",
         "capabilities":["compliance","analysis"]
       }}}'
```

## Autonomous Operations (6 Crons)

| Interval | System | What it does |
|----------|--------|-------------|
| `*/5 min` | Beacon | Health check 35 oracles, issue 35 VCs, update mesh registry |
| `*/10 min` | XRPL Watcher | Auto-register agents sending join TX |
| `*/15 min` | **Immune System** | Run 3 hooks + recovery + decay |
| `6h` | XRPL Beacon | On-ledger TX with mesh state memo |
| `6h` | Hedera Beacon | `pulse()` on contract + HCS message |
| `daily` | DealOracle | Autonomous business development outreach |

## Live Endpoints

- **Catalog**: https://tooloracle.io/assets/catalog.json
- **Beacon**: https://feedoracle.io/beacon/index.json
- **DIDs**: https://tooloracle.io/.well-known/did.json
- **Agent Card**: https://tooloracle.io/.well-known/agent.json
- **OpenAPI**: https://tooloracle.io/openapi.json
- **Join**: https://tooloracle.io/oraclenet/join

## Built By

One person. Four AIs. Six months. Self-funded.

**FeedOracle Technologies** — Bad Salzuflen, Germany
- feedoracle.io — Compliance infrastructure (DORA, MiCA, AMLR)
- tooloracle.io — MCP server marketplace (96 servers, 1,093 tools)

## License

MIT
