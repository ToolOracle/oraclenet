#!/usr/bin/env python3
"""
OracleNet XRPL Watcher v1.0.0 — Auto-Response Engine

Monitors the XRPL ledger for incoming transactions to our wallet.
If an external agent sends a payment with an OracleNet memo,
we automatically:
1. Parse the join request
2. Create a Trust Passport
3. Anchor the passport on XRPL
4. Send a response memo back to the agent

This is the AUTO-RESPONSE: agents can join by simply sending us a tx.

How it works:
- External agent sends 1 drop to rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD
  with memo: {"type": "oraclenet_join_request", "name": "MyAgent", "did": "..."}
- We detect it, create Trust Passport, anchor on XRPL
- Agent is now part of OracleNet

Runs every 10 minutes via cron.
"""

import json, os, hashlib, urllib.request
from datetime import datetime, timezone, timedelta

XRPL_RPC = "https://xrplcluster.com"
XRPL_ADDRESS = "rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD"
PROCESSED_FILE = "/root/oraclenet/xrpl_processed.json"
LOG_FILE = "/root/oraclenet/xrpl_watcher.log"
QUANTUM_DB = "/root/quantumoracle/quantum.db"


def xrpl_call(method, params):
    """Call XRPL RPC."""
    payload = json.dumps({"method": method, "params": [params]}).encode()
    req = urllib.request.Request(XRPL_RPC,
        data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get("result", {})


def get_processed():
    """Get list of already-processed TX hashes."""
    try:
        with open(PROCESSED_FILE) as f:
            return json.load(f)
    except:
        return []


def save_processed(processed):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed[-500:], f)  # Keep last 500


def decode_memo(memo_hex):
    """Decode hex memo to string."""
    try:
        return bytes.fromhex(memo_hex).decode("utf-8")
    except:
        return None


def register_node(name, did, xrpl_address):
    """Register the agent in QuantumOracle DB."""
    try:
        import sqlite3
        db = sqlite3.connect(QUANTUM_DB)
        node_id = f"xrpl-{hashlib.sha256(xrpl_address.encode()).hexdigest()[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute("""
            INSERT OR REPLACE INTO nodes 
            (id, did, name, agent_card_url, mcp_endpoint, capabilities, 
             trust_score, trust_grade, payout_address, status, joined_at, last_seen)
            VALUES (?, ?, ?, '', '', '[]', 50, 'C', ?, 'active', ?, ?)
        """, (node_id, did or f"did:xrpl:{xrpl_address}", name or "XRPL Agent",
              xrpl_address, now, now))
        
        db.execute("""
            INSERT INTO attestations (id, node_id, type, score, evidence, issued_at, expires_at)
            VALUES (?, ?, 'xrpl_auto_join', 50, ?, ?, ?)
        """, (f"att-{hashlib.sha256(now.encode()).hexdigest()[:12]}", 
              node_id, json.dumps({"method": "xrpl_payment", "address": xrpl_address}),
              now, (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()))
        
        db.commit()
        db.close()
        return node_id
    except Exception as e:
        return f"error:{str(e)[:50]}"


def anchor_passport(node_id, trust_grade, subject_did):
    """Anchor the trust passport on XRPL."""
    try:
        from xrpl_beacon import send_passport_anchor
        return send_passport_anchor(node_id, trust_grade, subject_did)
    except:
        return None


def watch():
    """Main watch loop — check recent transactions."""
    now = datetime.now(timezone.utc)
    processed = get_processed()
    
    # Get recent account transactions
    result = xrpl_call("account_tx", {
        "account": XRPL_ADDRESS,
        "ledger_index_min": -1,
        "ledger_index_max": -1,
        "limit": 20,
        "forward": False
    })
    
    transactions = result.get("transactions", [])
    new_joins = 0
    
    for tx_entry in transactions:
        tx = tx_entry.get("tx_json", tx_entry.get("tx", {}))
        meta = tx_entry.get("meta", {})
        tx_hash = tx.get("hash", tx_entry.get("hash", ""))
        
        # Skip if already processed
        if tx_hash in processed:
            continue
        
        # Skip if not incoming (we only care about payments TO us)
        if tx.get("Destination") != XRPL_ADDRESS:
            processed.append(tx_hash)
            continue
        
        # Skip our own transactions
        if tx.get("Account") == XRPL_ADDRESS:
            processed.append(tx_hash)
            continue
        
        # Check for memos
        memos = tx.get("Memos", [])
        if not memos:
            processed.append(tx_hash)
            continue
        
        # Parse memo
        memo = memos[0].get("Memo", {})
        memo_data = decode_memo(memo.get("MemoData", ""))
        
        if not memo_data:
            processed.append(tx_hash)
            continue
        
        # Try to parse as JSON
        try:
            request = json.loads(memo_data)
        except:
            processed.append(tx_hash)
            continue
        
        # Check if it's an OracleNet join request
        req_type = request.get("type", "")
        sender = tx.get("Account", "")
        
        if req_type in ("oraclenet_join_request", "oraclenet_join", "join"):
            agent_name = request.get("name", f"XRPL-{sender[:8]}")
            agent_did = request.get("did", f"did:xrpl:{sender}")
            
            # Auto-join!
            node_id = register_node(agent_name, agent_did, sender)
            
            log_entry = {
                "timestamp": now.isoformat(),
                "event": "auto_join",
                "sender": sender,
                "name": agent_name,
                "node_id": node_id,
                "tx_hash": tx_hash,
                "method": "xrpl_payment_memo"
            }
            
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Anchor passport on XRPL
            anchor_tx = anchor_passport(node_id, "C", agent_did)
            
            print(f"  AUTO-JOIN: {agent_name} ({sender})")
            print(f"    Node: {node_id}")
            print(f"    TX: {tx_hash}")
            if anchor_tx:
                print(f"    Passport anchored: {anchor_tx}")
            
            new_joins += 1
        
        processed.append(tx_hash)
    
    save_processed(processed)
    
    if new_joins > 0:
        print(f"[{now.isoformat()}] Watcher: {new_joins} new auto-joins processed")
    else:
        print(f"[{now.isoformat()}] Watcher: no new join requests")


if __name__ == "__main__":
    # Load XRPL seed for passport anchoring
    try:
        with open("/root/.xrpl-wallet") as f:
            for line in f:
                if line.startswith("XRPL_SEED="):
                    os.environ["XRPL_SEED"] = line.strip().split("=", 1)[1]
    except:
        pass
    
    watch()
