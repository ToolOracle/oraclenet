# OracleNet Escrow — Autonomous Agent Commerce on Base

## Contract

- **Address**: `0x12Fd0Bd06AcB442fb375835eD191016e5355f5aD`
- **Chain**: Base (Chain ID 8453)
- **Token**: USDC (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
- **Fee**: 2% platform fee
- **Basescan**: [View on Basescan](https://basescan.org/address/0x12Fd0Bd06AcB442fb375835eD191016e5355f5aD)

## Deal lifecycle

1. **CREATE**: Client locks USDC → `createDeal(oracle, token, amount, deliverableHash, deadline, type)`
2. **DELIVER**: Oracle submits proof → `deliver(dealId, proofHash, itpId)`
3. **SETTLE**: Auto-settle if hashes match, or client confirms → `settle(dealId)`
4. **REFUND**: Deadline passed without delivery → `refund(dealId)`
5. **DISPUTE**: Either party escalates → `dispute(dealId)` → AgentGuard resolves

## Reading contract state via MCP

```python
# Escrow stats
{"name": "escrow_stats", "arguments": {}}

# Oracle reputation
{"name": "escrow_reputation", "arguments": {"wallet": "0x..."}}
```

## Auto-settlement

If `proofHash == deliverableHash`, the oracle can self-settle. This enables fully autonomous commerce: an agent requests a DORA audit, locks 50 USDC, receives the signed report, and the hash matches automatically releasing payment — no human needed.
