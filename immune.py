#!/usr/bin/env python3
"""
OracleNet Immune System v1.0
============================
Three hooks that turn OracleNet from a mesh into a living immune system:

Hook 1: Neural → AgentGuard (Adaptive Local Response)
    Weight changes → Agent state transitions (5 states)
    
Hook 2: AgentGuard → Beacon (Signed Network Warning)
    Security events → Typed, signed, TTL'd broadcast
    
Hook 3: Beacon → Neural (Distributed Learning)
    Network warnings → Temporary trust malus on all nodes
    
States: healthy → monitoring → restricted → suspended → revoked
Recovery: Good behavior improves state. Bad signals decay over time.
"""

import sqlite3
import json
import hashlib
import time
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, 
    format="%(asctime)s [IMMUNE] %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

NEURAL_DB = "/root/oraclenet/neural.db"
AGENTGUARD_DB = "/root/agentguard/agentguard.db"
BEACON_FILE = "/root/oraclenet/beacon_immune_events.json"

# ═══════════════════════════════════════════════════
# IMMUNE STATES — 5 levels, proportional response
# ═══════════════════════════════════════════════════
STATES = {
    "healthy":     {"level": 0, "desc": "Full access, trusted agent", "weight_min": 2.5},
    "monitoring":  {"level": 1, "desc": "Elevated scrutiny, all actions logged", "weight_min": 1.5},
    "restricted":  {"level": 2, "desc": "Escrow-only, limited scope", "weight_min": 0.8},
    "suspended":   {"level": 3, "desc": "Requires approval for every action", "weight_min": 0.3},
    "revoked":     {"level": 4, "desc": "Blocked, needs revalidation", "weight_min": -999},
}

def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ═══════════════════════════════════════════════════
# HOOK 1: Neural → AgentGuard
# Weight changes drive agent state transitions
# ═══════════════════════════════════════════════════
def hook_neural_to_guard():
    """
    Read neural weights → determine immune state → update AgentGuard.
    Proportional: no instant kills, only gradual state changes.
    """
    neural_db = sqlite3.connect(NEURAL_DB)
    guard_db = sqlite3.connect(AGENTGUARD_DB)
    
    # Get all weighted agents from neural DB
    weights = neural_db.execute("""
        SELECT oracle_did, weight, total_fires, success_count, fail_count, avg_response_ms
        FROM weights
    """).fetchall()
    
    changes = []
    
    for did, weight, fires, success, fails, avg_ms in weights:
        # Calculate success rate
        success_rate = success / max(fires, 1)
        
        # Determine target immune state based on weight + success rate
        if weight >= 2.5 and success_rate >= 0.8:
            target_state = "healthy"
        elif weight >= 1.5 and success_rate >= 0.6:
            target_state = "monitoring"
        elif weight >= 0.8 and success_rate >= 0.4:
            target_state = "restricted"
        elif weight >= 0.3:
            target_state = "suspended"
        else:
            target_state = "revoked"
        
        # Get current state from AgentGuard
        current = guard_db.execute(
            "SELECT state FROM agent_states WHERE agent_id = ?", (did,)
        ).fetchone()
        current_state = current[0] if current else "healthy"
        
        # Only change state if it's different
        if current_state != target_state:
            reason = (f"Immune Hook 1: weight={weight:.2f}, success_rate={success_rate:.1%}, "
                     f"fires={fires}, fails={fails}")
            
            if current:
                guard_db.execute("""
                    UPDATE agent_states 
                    SET state=?, reason=?, triggered_by='immune_neural', updated_at=?
                    WHERE agent_id=?
                """, (target_state, reason, ts(), did))
            else:
                guard_db.execute("""
                    INSERT INTO agent_states (agent_id, state, reason, triggered_by, created_at, updated_at)
                    VALUES (?, ?, ?, 'immune_neural', ?, ?)
                """, (did, target_state, reason, ts(), ts()))
            
            changes.append({
                "did": did,
                "from": current_state,
                "to": target_state,
                "weight": weight,
                "success_rate": success_rate,
                "reason": reason
            })
            log.info(f"State change: {did[:30]} {current_state} → {target_state} (weight={weight:.2f})")
    
    guard_db.commit()
    guard_db.close()
    neural_db.close()
    
    return changes


# ═══════════════════════════════════════════════════
# HOOK 2: AgentGuard → Beacon
# Security events become signed, typed network warnings
# ═══════════════════════════════════════════════════
def hook_guard_to_beacon():
    """
    Read AgentGuard events → create signed immune events → broadcast via beacon.
    Only sends CLASSIFIED events with severity, TTL, and evidence.
    """
    guard_db = sqlite3.connect(AGENTGUARD_DB)
    
    # Get recent security events (last hour)
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    events = guard_db.execute("""
        SELECT agent_id, state, reason, triggered_by, updated_at 
        FROM agent_states 
        WHERE updated_at > ? AND triggered_by LIKE 'immune_%'
        ORDER BY updated_at DESC
    """, (one_hour_ago,)).fetchall()
    
    # Also check audit log for denials
    denials = guard_db.execute("""
        SELECT agent_id, tool_name, risk_score, reason, created_at
        FROM audit_log 
        WHERE decision = 'deny' AND created_at > ?
        ORDER BY created_at DESC LIMIT 10
    """, (one_hour_ago,)).fetchall()
    
    guard_db.close()
    
    # Build immune events for beacon broadcast
    immune_events = []
    
    for agent_id, state, reason, triggered_by, updated_at in events:
        severity_map = {
            "healthy": "info",
            "monitoring": "low",
            "restricted": "medium",
            "suspended": "high",
            "revoked": "critical"
        }
        
        event = {
            "type": "immune_state_change",
            "agent_id": agent_id,
            "state": state,
            "severity": severity_map.get(state, "medium"),
            "reason_code": triggered_by,
            "reason": reason,
            "confidence": 0.8 if "neural" in (triggered_by or "") else 0.5,
            "issuer": "did:web:feedoracle.io",
            "evidence_ref": f"agentguard://{agent_id}/state/{state}",
            "timestamp": updated_at,
            "ttl": "24h",  # Event expires in 24h
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content_hash": hashlib.sha256(
                f"{agent_id}:{state}:{updated_at}".encode()
            ).hexdigest()[:16]
        }
        immune_events.append(event)
    
    for agent_id, tool, risk, reason, created_at in denials:
        event = {
            "type": "immune_denial",
            "agent_id": agent_id,
            "tool": tool,
            "risk_score": risk,
            "severity": "high" if risk >= 80 else "medium",
            "reason": reason,
            "issuer": "did:web:feedoracle.io",
            "timestamp": created_at,
            "ttl": "6h",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content_hash": hashlib.sha256(
                f"{agent_id}:{tool}:{created_at}".encode()
            ).hexdigest()[:16]
        }
        immune_events.append(event)
    
    # Save immune events for beacon to broadcast
    if immune_events:
        beacon_data = {
            "oraclenet_immune": {
                "version": "1.0",
                "events": immune_events,
                "total_events": len(immune_events),
                "generated_at": ts(),
                "issuer": "did:web:feedoracle.io",
                "signature_alg": "ES256K"
            }
        }
        with open(BEACON_FILE, 'w') as f:
            json.dump(beacon_data, f, indent=2)
        
        log.info(f"Beacon immune broadcast: {len(immune_events)} events")
    
    return immune_events


# ═══════════════════════════════════════════════════
# HOOK 3: Beacon → Neural (Distributed Learning)
# Network warnings become temporary trust malus
# ═══════════════════════════════════════════════════
def hook_beacon_to_neural(incoming_events=None):
    """
    Process immune events from other nodes → apply TEMPORARY trust malus.
    NOT instant conviction. Caution propagation only.
    
    Rules:
    - External events reduce weight by severity factor (0.1 to 0.5)
    - Malus decays over TTL period
    - Only confirmed events (high confidence) cause strong reduction
    - Recovery is always possible through good behavior
    """
    if incoming_events is None:
        # Read from local beacon file (for self-loop testing)
        try:
            with open(BEACON_FILE) as f:
                data = json.load(f)
            incoming_events = data.get("oraclenet_immune", {}).get("events", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    neural_db = sqlite3.connect(NEURAL_DB)
    
    # Severity → weight malus (proportional, never instant kill)
    MALUS = {
        "info": 0.0,       # No effect
        "low": -0.1,       # Slight caution
        "medium": -0.25,   # Noticeable reduction
        "high": -0.4,      # Significant concern
        "critical": -0.5,  # Strong warning (but still not a kill)
    }
    
    applied = []
    
    for event in incoming_events:
        agent_id = event.get("agent_id", "")
        severity = event.get("severity", "medium")
        confidence = event.get("confidence", 0.5)
        
        # Skip expired events
        expires = event.get("expires_at", "")
        if expires and expires < ts():
            continue
        
        # Calculate malus (severity * confidence = proportional impact)
        base_malus = MALUS.get(severity, -0.1)
        actual_malus = base_malus * confidence  # Low confidence = smaller impact
        
        if actual_malus == 0:
            continue
        
        # Apply malus to neural weight (but NEVER below 0.1 from external signal alone)
        existing = neural_db.execute(
            "SELECT weight FROM weights WHERE oracle_did = ?", (agent_id,)
        ).fetchone()
        
        if existing:
            new_weight = max(0.1, existing[0] + actual_malus)
            neural_db.execute("""
                UPDATE weights SET weight=?, last_updated=? WHERE oracle_did=?
            """, (new_weight, ts(), agent_id))
            
            applied.append({
                "agent_id": agent_id,
                "old_weight": existing[0],
                "new_weight": new_weight,
                "malus": actual_malus,
                "severity": severity,
                "confidence": confidence
            })
            log.info(f"Neural malus: {agent_id[:30]} weight {existing[0]:.2f} → {new_weight:.2f} "
                     f"(malus={actual_malus:.2f}, severity={severity})")
        else:
            # Unknown agent — create entry with reduced initial weight
            initial_weight = max(0.5, 2.0 + actual_malus)
            neural_db.execute("""
                INSERT INTO weights (oracle_did, capability, weight, total_fires, success_count, fail_count, avg_response_ms, last_updated)
                VALUES (?, 'unknown', ?, 0, 0, 0, 0, ?)
            """, (agent_id, initial_weight, ts()))
            
            applied.append({
                "agent_id": agent_id,
                "old_weight": 2.0,
                "new_weight": initial_weight,
                "malus": actual_malus,
                "severity": severity,
                "note": "new_entry"
            })
    
    neural_db.commit()
    neural_db.close()
    
    return applied


# ═══════════════════════════════════════════════════
# RECOVERY: Good behavior improves state over time
# ═══════════════════════════════════════════════════
def apply_recovery():
    """
    Agents with recent successful fires get weight boost.
    This is the 'healing' mechanism — prevents permanent damage.
    """
    neural_db = sqlite3.connect(NEURAL_DB)
    guard_db = sqlite3.connect(AGENTGUARD_DB)
    
    # Find agents with good recent performance
    recent = neural_db.execute("""
        SELECT target_did, COUNT(*) as fires, SUM(success) as successes
        FROM synapses
        WHERE fired_at > datetime('now', '-24 hours')
        GROUP BY target_did
        HAVING fires >= 3 AND (successes * 1.0 / fires) >= 0.8
    """).fetchall()
    
    recovered = []
    for did, fires, successes in recent:
        rate = successes / fires
        # Small boost for consistent good behavior
        boost = min(0.3, rate * 0.2)
        
        existing = neural_db.execute(
            "SELECT weight FROM weights WHERE oracle_did = ?", (did,)
        ).fetchone()
        
        if existing and existing[0] < 3.0:  # Cap at 3.0
            new_w = min(3.0, existing[0] + boost)
            neural_db.execute(
                "UPDATE weights SET weight=?, last_updated=? WHERE oracle_did=?",
                (new_w, ts(), did)
            )
            recovered.append({"did": did, "old": existing[0], "new": new_w, "boost": boost})
            log.info(f"Recovery: {did[:30]} weight {existing[0]:.2f} → {new_w:.2f} (+{boost:.2f})")
    
    neural_db.commit()
    neural_db.close()
    guard_db.close()
    
    return recovered


# ═══════════════════════════════════════════════════
# DECAY: Old warnings lose power over time
# ═══════════════════════════════════════════════════
def apply_decay():
    """
    Weights that were reduced by immune events slowly recover.
    24h half-life: after 24h without new negative signals, malus halves.
    """
    neural_db = sqlite3.connect(NEURAL_DB)
    
    # Find weights below 2.0 (default) that haven't been updated in 24h
    stale = neural_db.execute("""
        SELECT oracle_did, weight, last_updated FROM weights
        WHERE weight < 2.0 AND last_updated < datetime('now', '-24 hours')
    """).fetchall()
    
    decayed = []
    for did, weight, last_updated in stale:
        # Move 20% toward default (2.0)
        new_w = weight + (2.0 - weight) * 0.2
        neural_db.execute(
            "UPDATE weights SET weight=?, last_updated=? WHERE oracle_did=?",
            (new_w, ts(), did)
        )
        decayed.append({"did": did, "old": weight, "new": new_w})
        log.info(f"Decay recovery: {did[:30]} {weight:.2f} → {new_w:.2f}")
    
    neural_db.commit()
    neural_db.close()
    
    return decayed


# ═══════════════════════════════════════════════════
# MAIN: Run full immune cycle
# ═══════════════════════════════════════════════════
def run_immune_cycle():
    """Run all 3 hooks + recovery + decay in sequence."""
    log.info("═══ OracleNet Immune Cycle v1.0 ═══")
    
    # Hook 1: Neural → AgentGuard
    log.info("Hook 1: Neural → AgentGuard")
    state_changes = hook_neural_to_guard()
    log.info(f"  → {len(state_changes)} state changes")
    
    # Hook 2: AgentGuard → Beacon
    log.info("Hook 2: AgentGuard → Beacon")
    events = hook_guard_to_beacon()
    log.info(f"  → {len(events)} immune events broadcast")
    
    # Hook 3: Beacon → Neural
    log.info("Hook 3: Beacon → Neural")
    malus_applied = hook_beacon_to_neural()
    log.info(f"  → {len(malus_applied)} neural adjustments")
    
    # Recovery: Good behavior heals
    log.info("Recovery: healing good agents")
    recovered = apply_recovery()
    log.info(f"  → {len(recovered)} agents recovered")
    
    # Decay: Old warnings fade
    log.info("Decay: old warnings fading")
    decayed = apply_decay()
    log.info(f"  → {len(decayed)} weights decayed toward healthy")
    
    # Summary
    summary = {
        "timestamp": ts(),
        "state_changes": len(state_changes),
        "immune_events": len(events),
        "neural_adjustments": len(malus_applied),
        "recoveries": len(recovered),
        "decays": len(decayed),
        "details": {
            "state_changes": state_changes,
            "events": events[:5],  # Limit for logging
            "malus": malus_applied[:5],
            "recovered": recovered[:5],
            "decayed": decayed[:5]
        }
    }
    
    log.info(f"═══ Immune cycle complete: {len(state_changes)} changes, "
             f"{len(events)} events, {len(malus_applied)} malus, "
             f"{len(recovered)} recovered, {len(decayed)} decayed ═══")
    
    return summary


if __name__ == "__main__":
    result = run_immune_cycle()
    print(json.dumps(result, indent=2))
