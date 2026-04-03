# Getting Started with OracleNet

## 1. Connect (30 seconds)

```bash
claude mcp add --transport http tooloracle https://tooloracle.io/mcp/
```

You now have 1,065 tools. Try: "Check if USDC is MiCA compliant"

## 2. Discover (what's available)

```bash
# See all 90 servers
curl https://tooloracle.io/assets/catalog.json

# See live status (updated every 5 min)
curl https://feedoracle.io/beacon/index.json

# See trust credentials
curl https://feedoracle.io/beacon/vcs/bundle.json
```

## 3. Use free tools (no API key needed)

These tools are always free:
- `compliance_preflight` — MiCA compliance check
- `mica_status` — Authorization status
- `peg_deviation` — Stablecoin peg check  
- `macro_risk` — US macro composite from 86 FRED series
- `sanctions_screen` — EU + OFAC + UN (87K names)
- All `support_*` tools — diagnostics, health, onboarding

## 4. Pay for premium tools (x402)

```bash
# x402 USDC micropayments on Base — $0.01 per call
curl https://tooloracle.io/x402/
```

Or use the Escrow for complex workflows (see [escrow docs](escrow.md)).

## 5. Verify trust

```bash
# Resolve our DID
curl https://feedoracle.io/.well-known/did.json

# Check our Verifiable Credential
curl https://feedoracle.io/beacon/vcs/feedoracle-io.json

# Verify our signing key
curl https://feedoracle.io/.well-known/jwks.json
```
