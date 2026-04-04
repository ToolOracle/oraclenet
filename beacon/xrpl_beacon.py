#!/usr/bin/env python3
"""
OracleNet XRPL Beacon v1.0.0 — On-Ledger Signal

Writes a compact, machine-readable OracleNet beacon signal directly
into the XRPL as a Memo on a micro-payment transaction.

Any agent that reads the XRPL ledger can find and parse this signal.
It proves OracleNet is active, exposes the join path, and optionally
anchors a SHA-256 hash of the current mesh state.

Design principles (from ChatGPT protocol architecture prompt):
- XRPL = public beacon layer, NOT full state database
- On-ledger: compact signal (type, version, did, join, verify, ref, hash)
- Off-ledger: full mesh state, VCs, ITP logs, node data
- No coercion, no malware logic — pure usefulness and trust

Tx cost: 0.000012 XRP (~$0.00003) per beacon
Schedule: Every 6 hours via cron (4x/day = 0.000048 XRP/day)
At 21 XRP balance: ~437,500 days of beacons (1,198 years)
"""

import json, os, hashlib, time
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════

XRPL_RPC = "https://xrplcluster.com"
XRPL_SEED = os.environ.get("XRPL_SEED", "")
XRPL_ADDRESS = "rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD"
BEACON_FILE = "/var/www/feedoracle/beacon/index.json"
LOG_FILE = "/root/oraclenet/xrpl_beacon.log"

# Self-payment (send to ourselves — the memo is the payload)
DESTINATION = XRPL_ADDRESS  
AMOUNT_DROPS = "1"  # 0.000001 XRP (minimum)


def get_beacon_hash():
    """SHA-256 hash of current off-chain beacon state."""
    try:
        with open(BEACON_FILE) as f:
            data = f.read()
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    except:
        return None


def build_beacon_memo(event_type="oraclenet_beacon", extra=None):
    """Build the compact on-ledger beacon payload."""
    now = datetime.now(timezone.utc)
    
    payload = {
        "type": event_type,
        "v": "1.0",
        "did": "did:web:feedoracle.io",
        "join": "https://tooloracle.io/quantum/mcp",
        "verify": "https://feedoracle.io/.well-known/jwks.json",
        "ref": "https://feedoracle.io/beacon/index.json",
        "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    # Add mesh state hash for integrity proof
    beacon_hash = get_beacon_hash()
    if beacon_hash:
        payload["hash"] = beacon_hash
    
    # Add extra fields for special events
    if extra:
        payload.update(extra)
    
    return payload


def send_xrpl_beacon(event_type="oraclenet_beacon", extra=None):
    """Send a beacon transaction to XRPL with memo payload."""
    from xrpl.clients import JsonRpcClient
    from xrpl.wallet import Wallet
    from xrpl.models.transactions import AccountSet, Memo
    from xrpl.transaction import submit_and_wait
    from xrpl.utils import str_to_hex
    
    if not XRPL_SEED:
        print("ERROR: XRPL_SEED not set")
        return None
    
    client = JsonRpcClient(XRPL_RPC)
    wallet = Wallet.from_seed(XRPL_SEED)
    
    # Build beacon payload
    payload = build_beacon_memo(event_type, extra)
    payload_json = json.dumps(payload, separators=(',', ':'))  # Compact JSON
    
    # Create memo (XRPL memos are hex-encoded)
    memo = Memo(
        memo_type=str_to_hex("application/json"),
        memo_data=str_to_hex(payload_json)
    )
    
    # AccountSet with memo — no XRP moves, just anchors data on-chain
    # Cost: only the transaction fee (~12 drops = 0.000012 XRP)
    tx = AccountSet(
        account=wallet.address,
        memos=[memo]
    )
    
    try:
        result = submit_and_wait(tx, client, wallet)
        tx_hash = result.result.get("hash", "?")
        ledger = result.result.get("ledger_index", "?")
        fee = result.result.get("Fee", "?")
        
        log_entry = {
            "timestamp": payload["ts"],
            "event": event_type,
            "tx_hash": tx_hash,
            "ledger": ledger,
            "fee_drops": fee,
            "payload_size": len(payload_json),
            "beacon_hash": payload.get("hash", "?")
        }
        
        # Log
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        print(f"[{payload['ts']}] XRPL Beacon: {event_type}")
        print(f"  TX: {tx_hash}")
        print(f"  Ledger: {ledger}")
        print(f"  Fee: {fee} drops")
        print(f"  Payload: {len(payload_json)} bytes")
        print(f"  Hash: {payload.get('hash', 'none')}")
        print(f"  Explorer: https://xrpscan.com/tx/{tx_hash}")
        
        return tx_hash
    except Exception as e:
        print(f"ERROR: {str(e)[:200]}")
        return None


def send_genesis_deal_anchor(deal_tx_hash, deal_count, volume_usdc):
    """Anchor the genesis deal proof on XRPL."""
    return send_xrpl_beacon("oraclenet_genesis_deal", {
        "base_tx": deal_tx_hash,
        "deals": deal_count,
        "vol": f"{volume_usdc} USDC",
        "chain": "base:8453",
        "escrow": "0x330F99f34246EA375333b9C01Ed6BB49190B051F"
    })


def send_mesh_epoch(epoch_number, oracles_online, tools_count):
    """Anchor a mesh epoch snapshot on XRPL."""
    return send_xrpl_beacon("oraclenet_mesh_epoch", {
        "epoch": epoch_number,
        "oracles": oracles_online,
        "tools": tools_count
    })


def send_passport_anchor(node_id, trust_grade, did):
    """Anchor a trust passport issuance on XRPL."""
    return send_xrpl_beacon("oraclenet_passport_anchor", {
        "node": node_id,
        "grade": trust_grade,
        "subject": did
    })


if __name__ == "__main__":
    import sys
    
    # Load seed from file
    if not XRPL_SEED:
        try:
            with open("/root/.xrpl-wallet") as f:
                for line in f:
                    if line.startswith("XRPL_SEED="):
                        os.environ["XRPL_SEED"] = line.strip().split("=", 1)[1]
                        XRPL_SEED = os.environ["XRPL_SEED"]
        except:
            pass
    
    if not XRPL_SEED:
        # Try from .env
        os.environ["XRPL_SEED"] = "sEdSVJRtsGAjJw99y843DKxipXbUcVV"
        XRPL_SEED = os.environ["XRPL_SEED"]
    
    event = sys.argv[1] if len(sys.argv) > 1 else "oraclenet_beacon"
    
    if event == "genesis":
        send_genesis_deal_anchor(
            "0x19a455d0818f49702ea81da37630c90b8df476b982cf36e0afe9752543e988b4",
            100, 1.99
        )
    elif event == "epoch":
        send_mesh_epoch(1, 27, 1072)
    else:
        send_xrpl_beacon()
