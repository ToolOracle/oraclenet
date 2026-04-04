#!/usr/bin/env python3
"""
OracleNet Neural Layer v1.0.0

Adds learning, reward scoring, and dynamic routing weights to OracleNet.
This is NOT a neural network in the ML sense. It's a simple but effective
feedback loop that makes the mesh smarter over time.

How it works:
1. Every Oracle interaction is logged as a "synapse firing"
2. Each firing gets a reward score (success, failure, speed, trust)
3. Rewards accumulate into connection weights
4. quantum_route uses weights to prefer better-performing oracles
5. The mesh gets smarter with every interaction

Analogy:
- Oracle = neuron (specialist processor)
- ITP call = synapse firing (data flows with provenance)
- Reward = reinforcement signal (this worked / didn't work)
- Weight = connection strength (prefer this oracle for this task)
- Conductor = prefrontal cortex (orchestrates, learns, decides)
"""

import json, os, sqlite3, hashlib, math
from datetime import datetime, timezone, timedelta

DB_PATH = "/root/oraclenet/neural.db"

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS synapses (
            id TEXT PRIMARY KEY,
            source_did TEXT,
            target_did TEXT,
            tool TEXT,
            task_type TEXT,
            fired_at TEXT,
            response_ms INTEGER,
            success INTEGER DEFAULT 1,
            reward REAL DEFAULT 0,
            confidence REAL DEFAULT 0.5,
            context TEXT
        );
        
        CREATE TABLE IF NOT EXISTS weights (
            oracle_did TEXT,
            capability TEXT,
            weight REAL DEFAULT 1.0,
            total_fires INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            avg_response_ms REAL DEFAULT 0,
            last_updated TEXT,
            PRIMARY KEY (oracle_did, capability)
        );
        
        CREATE TABLE IF NOT EXISTS rewards (
            id TEXT PRIMARY KEY,
            event_type TEXT,
            oracle_did TEXT,
            reward REAL,
            reason TEXT,
            timestamp TEXT
        );
        
        CREATE TABLE IF NOT EXISTS mesh_intelligence (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_synapses_target ON synapses(target_did);
        CREATE INDEX IF NOT EXISTS idx_synapses_tool ON synapses(tool);
        CREATE INDEX IF NOT EXISTS idx_weights_cap ON weights(capability);
    """)
    db.close()

init_db()


# ══════════════════════════════════════════════════════════
# 1. SYNAPSE FIRING — Log every Oracle interaction
# ══════════════════════════════════════════════════════════

def fire_synapse(source_did, target_did, tool, task_type="general",
                 response_ms=0, success=True, confidence=0.5, context=None):
    """Record a synapse firing (Oracle-to-Oracle interaction)."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    syn_id = f"syn-{hashlib.sha256(f'{now}{tool}{target_did}'.encode()).hexdigest()[:12]}"
    
    # Calculate reward
    reward = _calculate_reward(success, response_ms, confidence)
    
    db.execute("""
        INSERT INTO synapses (id, source_did, target_did, tool, task_type,
                             fired_at, response_ms, success, reward, confidence, context)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (syn_id, source_did, target_did, tool, task_type,
          now, response_ms, 1 if success else 0, reward, confidence,
          json.dumps(context) if context else None))
    
    # Update connection weight
    _update_weight(db, target_did, tool, success, response_ms, reward)
    
    db.commit()
    db.close()
    return {"synapse_id": syn_id, "reward": reward}


def _calculate_reward(success, response_ms, confidence):
    """Calculate reward for a synapse firing.
    
    Reward factors:
    - Success: +1.0 for success, -0.5 for failure
    - Speed: +0.3 for <500ms, +0.1 for <2000ms, 0 for slower
    - Confidence: multiplier (0.0 to 1.0)
    """
    reward = 0.0
    
    # Success/failure
    if success:
        reward += 1.0
    else:
        reward -= 0.5
    
    # Speed bonus
    if response_ms > 0:
        if response_ms < 500:
            reward += 0.3
        elif response_ms < 2000:
            reward += 0.1
    
    # Confidence multiplier
    reward *= max(0.1, confidence)
    
    return round(reward, 3)


def _update_weight(db, oracle_did, tool, success, response_ms, reward):
    """Update the connection weight for an oracle+capability pair."""
    now = datetime.now(timezone.utc).isoformat()
    
    # Get or create weight entry
    existing = db.execute(
        "SELECT * FROM weights WHERE oracle_did=? AND capability=?",
        (oracle_did, tool)
    ).fetchone()
    
    if existing:
        fires = existing["total_fires"] + 1
        successes = existing["success_count"] + (1 if success else 0)
        fails = existing["fail_count"] + (0 if success else 1)
        
        # Exponential moving average for response time
        alpha = 0.1  # Learning rate
        avg_ms = existing["avg_response_ms"] * (1 - alpha) + response_ms * alpha
        
        # Weight = base + success_rate_bonus + speed_bonus + volume_bonus
        success_rate = successes / fires if fires > 0 else 0
        speed_factor = max(0, 1.0 - (avg_ms / 5000))  # Normalize to 0-1
        volume_factor = min(1.0, math.log10(fires + 1) / 2)  # Log scale, caps at 100
        
        weight = 1.0 + (success_rate * 2.0) + (speed_factor * 0.5) + (volume_factor * 0.5)
        
        db.execute("""
            UPDATE weights SET weight=?, total_fires=?, success_count=?,
                              fail_count=?, avg_response_ms=?, last_updated=?
            WHERE oracle_did=? AND capability=?
        """, (round(weight, 3), fires, successes, fails, round(avg_ms), now,
              oracle_did, tool))
    else:
        weight = 1.0 + (1.0 if success else -0.5)
        db.execute("""
            INSERT INTO weights (oracle_did, capability, weight, total_fires,
                               success_count, fail_count, avg_response_ms, last_updated)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?)
        """, (oracle_did, tool, round(weight, 3),
              1 if success else 0, 0 if success else 1,
              response_ms, now))


# ══════════════════════════════════════════════════════════
# 2. REWARD MODEL — Score mesh events
# ══════════════════════════════════════════════════════════

REWARD_TABLE = {
    "join_success": 5.0,           # New agent joined
    "join_high_trust": 10.0,       # High-trust agent joined (Grade A/B)
    "deal_settled": 3.0,           # Escrow deal settled
    "deal_disputed": -5.0,         # Dispute
    "compliance_pass": 1.0,        # Compliance check passed
    "compliance_block": 0.5,       # Block is also useful (prevented bad action)
    "drift_detected": -1.0,        # Something drifted
    "drift_remediated": 2.0,       # Self-healed
    "revenue_generated": 2.0,      # Revenue from external call
    "beacon_acknowledged": 0.5,    # Someone read our beacon
    "passport_issued": 1.0,        # Trust passport created
    "oracle_offline": -3.0,        # Oracle went down
    "oracle_recovered": 1.5,       # Oracle came back
}

def record_reward(event_type, oracle_did, reason=None):
    """Record a mesh reward event."""
    reward_value = REWARD_TABLE.get(event_type, 0)
    if reward_value == 0:
        return None
    
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    reward_id = f"rwd-{hashlib.sha256(f'{now}{event_type}{oracle_did}'.encode()).hexdigest()[:12]}"
    
    db.execute("""
        INSERT INTO rewards (id, event_type, oracle_did, reward, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (reward_id, event_type, oracle_did, reward_value, reason, now))
    db.commit()
    db.close()
    
    return {"reward_id": reward_id, "event": event_type, "reward": reward_value}


# ══════════════════════════════════════════════════════════
# 3. DYNAMIC ROUTING — Use weights for smart routing
# ══════════════════════════════════════════════════════════

def get_weighted_route(capability, min_weight=0.5):
    """Get oracles for a capability, sorted by learned weight."""
    db = get_db()
    results = db.execute("""
        SELECT oracle_did, capability, weight, total_fires, success_count, 
               fail_count, avg_response_ms
        FROM weights 
        WHERE capability=? AND weight>=?
        ORDER BY weight DESC
    """, (capability, min_weight)).fetchall()
    db.close()
    
    return [{
        "oracle_did": r["oracle_did"],
        "capability": r["capability"],
        "weight": r["weight"],
        "fires": r["total_fires"],
        "success_rate": round(r["success_count"] / r["total_fires"] * 100, 1) if r["total_fires"] > 0 else 0,
        "avg_ms": round(r["avg_response_ms"])
    } for r in results]


# ══════════════════════════════════════════════════════════
# 4. MESH INTELLIGENCE — Aggregate insights
# ══════════════════════════════════════════════════════════

def get_mesh_intelligence():
    """Generate mesh-wide intelligence report."""
    db = get_db()
    
    total_synapses = db.execute("SELECT COUNT(*) FROM synapses").fetchone()[0]
    total_rewards = db.execute("SELECT COALESCE(SUM(reward), 0) FROM rewards").fetchone()[0]
    recent_success = db.execute(
        "SELECT COUNT(*) FROM synapses WHERE success=1 AND fired_at > datetime('now', '-24 hours')"
    ).fetchone()[0]
    recent_fail = db.execute(
        "SELECT COUNT(*) FROM synapses WHERE success=0 AND fired_at > datetime('now', '-24 hours')"
    ).fetchone()[0]
    
    # Top performing oracles
    top_oracles = db.execute("""
        SELECT oracle_did, SUM(weight * total_fires) as score,
               SUM(total_fires) as fires, 
               ROUND(AVG(weight), 2) as avg_weight
        FROM weights
        GROUP BY oracle_did
        ORDER BY score DESC
        LIMIT 10
    """).fetchall()
    
    # Most active capabilities
    top_caps = db.execute("""
        SELECT capability, SUM(total_fires) as fires, ROUND(AVG(weight), 2) as avg_weight
        FROM weights
        GROUP BY capability
        ORDER BY fires DESC
        LIMIT 10
    """).fetchall()
    
    db.close()
    
    return {
        "mesh_health": {
            "total_synapses_fired": total_synapses,
            "cumulative_reward": round(total_rewards, 2),
            "last_24h_success": recent_success,
            "last_24h_fail": recent_fail,
            "success_rate_24h": round(recent_success / max(1, recent_success + recent_fail) * 100, 1)
        },
        "top_oracles": [{
            "did": o["oracle_did"],
            "neural_score": round(o["score"], 2),
            "fires": o["fires"],
            "avg_weight": o["avg_weight"]
        } for o in top_oracles],
        "top_capabilities": [{
            "capability": c["capability"],
            "fires": c["fires"],
            "avg_weight": c["avg_weight"]
        } for c in top_caps],
        "learning_status": "active" if total_synapses > 0 else "cold_start"
    }


# ══════════════════════════════════════════════════════════
# 5. INTEGRATION — Hook into Conductor
# ══════════════════════════════════════════════════════════

def on_conductor_call(oracle_key, tool_name, success, response_ms, confidence):
    """Called by Conductor after every oracle call.
    This is the hook that makes the mesh learn."""
    
    # Map oracle key to DID
    did_map = {
        "ampel": "did:web:feedoracle.io:ampel",
        "dora": "did:web:tooloracle.io:dora",
        "aml": "did:web:tooloracle.io:aml",
        "test": "did:web:tooloracle.io:test",
        "reporting": "did:web:tooloracle.io:reporting",
        "cloud": "did:web:tooloracle.io:cloud",
        "law": "did:web:tooloracle.io:law",
        "contract": "did:web:tooloracle.io:contract",
        "drift": "did:web:tooloracle.io:drift",
        "predict": "did:web:tooloracle.io:predict",
        "eventfabric": "did:web:tooloracle.io:eventfabric",
        "resilience": "did:web:tooloracle.io:resilience",
        "governance": "did:web:tooloracle.io:governance",
        "dependency": "did:web:tooloracle.io:dependency",
    }
    
    target_did = did_map.get(oracle_key, f"did:web:tooloracle.io:{oracle_key}")
    
    return fire_synapse(
        source_did="did:web:tooloracle.io:conductor",
        target_did=target_did,
        tool=tool_name,
        task_type="conductor_workflow",
        response_ms=response_ms,
        success=success,
        confidence=confidence
    )


if __name__ == "__main__":
    # Demo: simulate some synapses
    print("=== OracleNet Neural Layer v1.0.0 ===\n")
    
    # Simulate conductor calls
    demos = [
        ("ampel", "readiness_check", True, 450, 0.95),
        ("aml", "sanctions_screen", True, 320, 0.98),
        ("dora", "cve_latest", True, 890, 0.85),
        ("cloud", "cloud_status", True, 1200, 0.70),
        ("ampel", "readiness_check", True, 380, 0.95),
        ("aml", "sanctions_screen", True, 290, 0.98),
        ("aml", "sanctions_screen", False, 5000, 0.3),  # One failure
    ]
    
    for oracle, tool, success, ms, conf in demos:
        result = on_conductor_call(oracle, tool, success, ms, conf)
        icon = "✅" if success else "❌"
        print(f"  {icon} {oracle}/{tool}: reward={result['reward']}")
    
    # Show learned weights
    print("\n=== Learned Weights ===")
    for cap in ["readiness_check", "sanctions_screen", "cve_latest", "cloud_status"]:
        routes = get_weighted_route(cap)
        for r in routes:
            print(f"  {cap}: {r['oracle_did']} weight={r['weight']} fires={r['fires']} success={r['success_rate']}%")
    
    # Record some rewards
    record_reward("join_success", "did:web:feedoracle.io")
    record_reward("deal_settled", "did:web:feedoracle.io")
    
    # Mesh intelligence
    print("\n=== Mesh Intelligence ===")
    intel = get_mesh_intelligence()
    print(json.dumps(intel, indent=2))
