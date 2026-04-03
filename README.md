<div align="center">

# OracleNet

**The compliance-first AI agent mesh network.**

90 MCP servers · 1,065 tools · W3C DIDs · Verifiable Credentials · On-chain escrow

[![Servers](https://img.shields.io/badge/MCP_Servers-90-10B898?style=flat-square)](https://tooloracle.io/assets/catalog.json)
[![Tools](https://img.shields.io/badge/Tools-1,065-10B898?style=flat-square)](https://tooloracle.io)
[![Base](https://img.shields.io/badge/Escrow-Base_Mainnet-0052FF?style=flat-square)](https://basescan.org/address/0x12Fd0Bd06AcB442fb375835eD191016e5355f5aD)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Beacon](https://img.shields.io/badge/Beacon-Live-10B898?style=flat-square)](https://feedoracle.io/beacon/index.json)

</div>

---

## Connect in 30 seconds

```bash
# Claude CLI
claude mcp add --transport http tooloracle https://tooloracle.io/mcp/

# Or in any MCP config
{
  "mcpServers": {
    "tooloracle": {
      "url": "https://tooloracle.io/mcp/"
    }
  }
}
```

That's it. You now have access to compliance, blockchain, finance, and 1,062 more tools.

---

## What is OracleNet?

OracleNet is the infrastructure layer for autonomous AI agents that need to:

- **Find** each other (W3C DIDs + ANP Agent Discovery)
- **Trust** each other (Verifiable Credentials + ES256K signatures)
- **Work** together (MCP tools + A2A protocol)
- **Pay** each other (x402 USDC micropayments + Base escrow)
- **Prove** what they did (PROV-O intelligence transfer + blockchain anchoring)

Built for regulated industries. Every response signed. Every evidence trail auditable.

### The stack

```
┌─────────────────────────────────────────────────┐
│  External AI Agent                              │
├─────────────────────────────────────────────────┤
│  1. DISCOVER    did:web:feedoracle.io            │ W3C DID
│  2. INSPECT     /.well-known/agent-descriptions  │ ANP Discovery
│  3. VERIFY      /beacon/vcs/bundle.json          │ W3C Verifiable Credentials
│  4. CONNECT     tooloracle.io/mcp/               │ MCP (90 servers)
│  5. NEGOTIATE   escrow_create (Base USDC)        │ On-chain escrow
│  6. EXECUTE     compliance_preflight, etc.       │ 1,065 tools
│  7. RECEIVE     Intelligence Transfer Package    │ PROV-O provenance
│  8. SETTLE      escrow auto-settle               │ Hash match → payment
└─────────────────────────────────────────────────┘
```

---

## Quick examples

### Check if a stablecoin is MiCA compliant

```python
import httpx

r = httpx.post("https://mcp.feedoracle.io/mcp/", json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
        "name": "compliance_preflight",
        "arguments": {"symbol": "USDT"}
    }
})
# → BLOCK: Not authorized under MiCA. Missing in ESMA register.
```

### Run a full DORA audit

```python
r = httpx.post("https://tooloracle.io/conductor/mcp", json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
        "name": "full_assessment",
        "arguments": {"entity_id": "ent_09e73b0d"}
    }
})
# → 10 oracles consulted, score 86.5%, 22G/1Y/2R, 3 findings
```

### Screen a person for sanctions

```python
r = httpx.post("https://tooloracle.io/aml/mcp", json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
        "name": "sanctions_screen",
        "arguments": {"name": "Vladimir Putin"}
    }
})
# → BLOCKED: EXACT match OFAC SDN, Score 1.0
```

### Check escrow contract stats on Base

```python
r = httpx.post("https://tooloracle.io/deal/mcp/", json={
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
        "name": "escrow_stats",
        "arguments": {}
    }
})
# → Live from Base: contract 0x12Fd...f5aD, fee 2%, deals on-chain
```

---

## Architecture

### 90 MCP Servers across 7 categories

| Category | Servers | Tools | Highlights |
|---|---|---|---|
| Compliance & Regulation | 35 | 506 | DORA OS (21 oracles), MiCA, AMLR, BaFin reporting |
| Blockchain & DeFi | 14 | 127 | 13 chain oracles (BTC, ETH, SOL, TON, SUI...) |
| Finance & Markets | 10 | 116 | ECB, FRED, OECD, World Bank, Carbon |
| Business Intelligence | 10 | 97 | SEO, E-Commerce, Leads, Invoices |
| Travel & Lifestyle | 8 | 79 | Flights, Hotels, Weather, Sports, Jobs |
| Trust & Agent Infrastructure | 9 | 86 | AgentGuard, DealOracle, Memory, Scheduler |
| Payment & Settlement | 4 | 48 | CBDC, PSD2, Settlement, Merchant |

### DORA OS — 21 oracles, 317 tools, 9 workflows

The most comprehensive DORA automation system. Covers all 49 articles.

```
Conductor → AmpelOracle (50 tools, central state)
         → DORAOracle (threat intel, CVE, KEV)
         → AMLOracle (87K sanctions names)
         → ContractOracle (Art. 30 clause check)
         → ResilienceOracle (BIA, BCM, DR)
         → IncidentOracle (4h/72h/30d BaFin)
         → TestOracle (TLPT, TIBER-EU)
         → ReportingOracle (ITS export, NCA)
         → CloudOracle (AWS/GCP/Azure live)
         → ... 12 more specialized oracles
```

### OracleNet Protocol Stack

| Layer | Protocol | Endpoint |
|---|---|---|
| Identity | W3C DID (`did:web`) | `/.well-known/did.json` |
| Discovery | ANP Agent Description | `/.well-known/agent-descriptions` |
| Communication | A2A v0.3 | `/.well-known/agent.json` |
| Tool Access | MCP | `/.well-known/mcp/server-card.json` |
| Trust | W3C Verifiable Credentials | `/beacon/vcs/bundle.json` |
| Status | OracleNet Beacon (5min) | `/beacon/index.json` |
| Provenance | PROV-O Intelligence Transfer | `/beacon/itp-example.json` |
| Payment | x402 USDC on Base | `tooloracle.io/x402/` |
| Escrow | Smart Contract (Base) | [`0x12Fd...f5aD`](https://basescan.org/address/0x12Fd0Bd06AcB442fb375835eD191016e5355f5aD) |
| Security | AgentGuard (258 policies) | `tooloracle.io/agentguard/mcp/` |

### On-chain trust

- **Escrow**: `0x12Fd0Bd06AcB442fb375835eD191016e5355f5aD` on Base
- **Trust Anchor #1**: Polygon Block 81,721,330 (Jan 16, 2026 — day before DORA)
- **Trust Anchor #2**: Polygon Block 84,921,488 (Mar 31, 2026 — full DORA OS)
- **Signing**: ES256K (secp256k1), verifiable via [JWKS](https://feedoracle.io/.well-known/jwks.json)

---

## Escrow: Autonomous agent commerce

AI agents can lock USDC in escrow, receive deliverables with provenance proof, and settle automatically.

```
Agent A (client)                  OracleNetEscrow (Base)              Agent B (oracle)
     │                                    │                                │
     │── createDeal(50 USDC) ───────────→ │ USDC locked                   │
     │                                    │                                │
     │                                    │ ←── deliver(proofHash, itp) ──│
     │                                    │                                │
     │── settle() ──────────────────────→ │ → 49 USDC → oracle            │
     │                                    │ → 1 USDC  → platform (2%)     │
```

Contract: [`OracleNetEscrow.sol`](contracts/OracleNetEscrow.sol) — Solidity 0.8.24, OpenZeppelin v5

---

## Discovery endpoints

| URL | What |
|---|---|
| `feedoracle.io/.well-known/did.json` | W3C DID Document |
| `tooloracle.io/.well-known/did.json` | W3C DID Document |
| `feedoracle.io/.well-known/agent.json` | A2A v0.3 Agent Card |
| `tooloracle.io/.well-known/agent.json` | A2A v0.3 Agent Card |
| `feedoracle.io/.well-known/agent-descriptions` | ANP Discovery (JSON-LD) |
| `tooloracle.io/.well-known/agent-descriptions` | ANP Discovery (JSON-LD) |
| `feedoracle.io/beacon/index.json` | Live beacon (updated every 5 min) |
| `feedoracle.io/beacon/vcs/bundle.json` | 27 Verifiable Credentials |
| `tooloracle.io/assets/catalog.json` | Full catalog (90 servers) |
| `tooloracle.io/registry/api/` | Trusted Agent Registry |

---

## Built by

**One founder. Four AI models. Zero pretense.**

[Murat Keskin](https://linkedin.com/in/muratkeskin/) — Founder & CEO, FeedOracle Technologies. Bad Salzuflen, Germany.

Architecture, code, and execution across Claude, ChatGPT, Grok, and Gemini. No phantom team. No fake org chart. This is how 90 servers and 1,065 tools actually get built.

---

## License

MIT — use it, fork it, build on it.

---

<div align="center">

**[tooloracle.io](https://tooloracle.io)** · **[feedoracle.io](https://feedoracle.io)** · **[Beacon](https://feedoracle.io/beacon/index.json)** · **[Registry](https://tooloracle.io/registry.html)**

</div>
