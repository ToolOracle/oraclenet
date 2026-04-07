# OracleNet

> 90 MCP oracles · 1,014 capabilities · Execute pipeline · Neural learning · On-chain settlement · 24/7 soak-tested

OracleNet is an autonomous coordination layer for AI agents. One call to understand, route, execute, prove, settle, and learn — across 90 specialized oracles.

## What changed: Execute Pipeline (v4.0)

Before v4.0, OracleNet was a recommendation engine — it told agents where to go. Now it **executes**.

```
Agent: "Is USDT compliant in the EU?"

OracleNet:
  1. Understands    → compliance category, tool: compliance_preflight
  2. Routes         → FeedOracle Compliance (best weight: 2.55)
  3. Executes       → MCP call to oracle, 160ms
  4. Proves         → SHA-256 content hash + ES256K signature
  5. Settles        → Base escrow, Deal #103 on-chain
  6. Learns         → Synapse logged, neural weight updated
  7. Returns        → { status: "BLOCK", confidence: 1.0, jurisdiction: "EU" }
```

One call. Full loop. The mesh gets smarter with every interaction.

## Core Tools

### quantum_ask — The Front Door

Natural language in, structured result out. Supports English and German.

```bash
curl -X POST https://tooloracle.io/quantum/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"quantum_ask","arguments":{"need":"Is EURC MiCA compliant?"}}}'
```

### quantum_execute — Direct Tool Execution

Call any tool on any oracle. Neural synapse logged automatically.

```bash
quantum_execute → tool: "fed_rate", oracle: "macro"
quantum_execute → tool: "btc_overview", oracle: "btc"
quantum_execute → tool: "threat_landscape", oracle: "cybershield"
```

### QuantumOracle Gateway (20 Tools)

| Tool | Purpose |
|------|---------|
| `quantum_ask` | Natural language → intent → execute → deliver → learn |
| `quantum_execute` | Direct tool execution with neural learning |
| `quantum_join` | Join OracleNet — instant Trust Passport |
| `quantum_trust_passport` | W3C Verifiable Credential |
| `quantum_intent` | Intent parsing (keyword + LLM) |
| `quantum_route` | Find best oracle for a task |
| `quantum_offer` | Pricing catalog |
| `quantum_deal` | Deal handshake protocol |
| `quantum_rate` | Rate interaction → adjust weights |
| `quantum_reputation` | Query agent reputation (A+ to F) |
| `quantum_settle` | Record deal settlement |
| `quantum_scan` | Scan any domain for signals |
| `quantum_subscribe` | Webhook registration |
| `quantum_feed` | Poll event feed |
| `quantum_preflight` | Pre-flight trust check |
| `quantum_refer` | Referral to best oracle |
| `quantum_history` | Past interactions |
| `quantum_status` | Mesh status |
| `quantum_nodes` | Registered nodes |
| `neural_status` | Learned weights |

## 90 Oracles · 7 Categories

| Category | Oracles | Tools | Examples |
|----------|---------|-------|----------|
| **Compliance & Regulation** | 40 | 521 | MiCA, DORA, AML, ESMA, EU Law, RegWatch |
| **Trust & Agent Infrastructure** | 10 | 107 | AgentGuard, QuantumOracle, TrustOracle |
| **Finance & Markets** | 10 | 116 | MacroOracle, CFOCoPilot, ISO20022 |
| **Business Intelligence** | 10 | 97 | SEO, Lead, Review, Ecommerce |
| **Travel & Lifestyle** | 8 | 79 | Weather, Sport, Movie, Map |
| **Blockchain & DeFi** | 14 | 150 | BTC, ETH, XRPL, SOL, ARB, TON, SUI, Hedera, Base, BNB, XLM, Aptos, Flare |
| **Payment & Settlement** | 4 | 48 | CBDC, PSD2, Settlement, Merchant |

## Neural Layer

The mesh learns from every execution. Routing gets smarter automatically.

- **96 synapses** logged (growing with every call)
- **69 weights** across 38 oracles
- Faster + more reliable oracles get higher scores
- Failed oracles get downweighted
- Circuit breaker: 3 failures → 2 min cooldown

```
MacroOracle:     weight 5.00 (perfect — 8ms avg, 100% success)
AmpelOracle:     weight 4.81 (6 fires, 385ms avg)
ComplianceOracle: weight 2.55 (9 fires, learning)
```

## On-Chain Anchors

| Chain | Type | Reference |
|-------|------|-----------|
| Base | Escrow contract (104 deals, 103 settled) | [0x330F...051F](https://basescan.org/address/0x330F99f34246EA375333b9C01Ed6BB49190B051F) |
| Polygon | Evidence hash | Block 84,921,488 |
| XRPL | Beacon pulse (6h) | [rJffix...pzD](https://xrpscan.com/account/rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD) |
| Hedera | Smart contract + HCS | [0.0.10420310](https://hashscan.io/mainnet/contract/0.0.10420310) |

## Hardening

| Protection | Detail |
|-----------|--------|
| Idempotency | Request-hash dedup, 5 min TTL |
| Rate Limit | 30 calls/min per caller |
| Circuit Breaker | 3 failures → open → 120s cooldown → half-open probe |
| Replay Protection | Timestamp-based, 5 min window |
| Malformed Response Guard | 1MB size limit, type validation |
| Escrow Protection | Service-key required, 1 USDC max per settlement |
| Webhook Limits | 50 global, 5 per agent |
| Nginx | HSTS, X-Frame-Options, XSS-Protection |

## Defense Layers

| Layer | System | Status |
|-------|--------|--------|
| L12 | HoneypotOracle — canary tokens, trap endpoints | Active (5 tokens, 16 hits) |
| L13 | Behavioral Baseline — anomaly detection | Active (cron every 5 min) |
| L14 | Predictive Threat Intel — CVE/KEV tracking | Active |
| L15 | Counter-Intelligence — attacker profiling + auto-escalation | Active (observe → slow → block) |
| L16 | Self-Evolution — auto-generates policy proposals | Active (Telegram approval) |
| Immune | Neural → AgentGuard → Beacon feedback loop | Active (cron every 15 min) |

## Observability

| Endpoint | Purpose | Update |
|----------|---------|--------|
| `tooloracle.io/oraclenet/pulse.json` | Live mesh signal | Every 5 min |
| `tooloracle.io/oraclenet/soak.json` | Soak test results (12 queries, 6 categories) | Every 5 min |
| `tooloracle.io/oraclenet/cockpit.json` | Oracle health, neural weights, security, threats | Every 5 min |
| `feedoracle.io/beacon/index.json` | 98 oracle beacon with trust VCs | Every 5 min |

## Connect

```bash
# Claude Desktop / Cursor / Windsurf
claude mcp add --transport http oraclenet https://tooloracle.io/quantum/mcp/
```

```json
{
  "mcpServers": {
    "oraclenet": {
      "url": "https://tooloracle.io/quantum/mcp/"
    }
  }
}
```

Free tier: 100 calls/day, no registration.
Paid: x402 USDC on Base ($0.01/call).

## Links

- [OracleNet Manifest](https://tooloracle.io/.well-known/oraclenet.json)
- [Agent Card](https://tooloracle.io/.well-known/agent.json)
- [DID Document](https://tooloracle.io/.well-known/did.json)
- [JWKS](https://feedoracle.io/.well-known/jwks.json)
- [tooloracle.io](https://tooloracle.io) · [feedoracle.io](https://feedoracle.io)

---

Built in Germany · ES256K signed · 4-chain anchored · MIT License
