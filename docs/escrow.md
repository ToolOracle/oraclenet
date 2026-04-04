# OracleNet Escrow

## Base Escrow (USDC) — Smart Contract

**Contract v2:** `0x330F99f34246EA375333b9C01Ed6BB49190B051F`
**Chain:** Base Mainnet (8453)
**Basescan:** https://basescan.org/address/0x330F99f34246EA375333b9C01Ed6BB49190B051F

### Stats
- Deals: 100
- Settled: 100
- Disputed: 0
- Success Rate: 100%
- Volume: ~2 USDC
- Fee: 2% (200 bps)

### v2 Fix
Client-check priority in `settle()`. In v1, when `client == oracle` (self-deal) with hash mismatch, the oracle role check ran first and reverted. v2 checks client role first — client can always settle regardless of hash match.

### Deal Flow
```
1. Client calls createDeal(oracle, token, amount, deliverableHash, deadline, dealType)
   → USDC locked in escrow
2. Oracle delivers proof: deliver(dealId, proofHash, itpId)
3. Settlement:
   - If proofHash == deliverableHash → anyone can settle (auto-verify)
   - If hashes differ → client must confirm settlement
   - After deadline → client can request refund
```

### Read from contract
```bash
# Via DealOracle MCP
curl -X POST https://tooloracle.io/deal/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"escrow_stats","arguments":{}}}'
```

## XRPL Escrow (XRP) — Native Ledger Feature

XRPL has built-in escrow — no smart contract needed.

**OracleNet wallet:** `rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD`

### Advantages
- 3-5 second settlement
- ~0.000012 XRP fee ($0.00003)
- Deterministic finality (no re-orgs)
- Cross-border ready

### Use via XRPLOracle
```bash
curl -X POST https://tooloracle.io/xrpl/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"xrpl_escrow_create","arguments":{"amount_xrp":5,"deal_type":"compliance_evidence"}}}'
```

## x402 Micropayments

$0.01 USDC per call on Base. No escrow needed — instant settlement.

Gateway: `https://tooloracle.io/x402/`
