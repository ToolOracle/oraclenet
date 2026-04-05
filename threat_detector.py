#!/usr/bin/env python3
"""
OracleNet Threat Detection Engine v1.0
======================================
Erkennt bösartige AI Agents anhand von Verhaltensmustern.

Detection Patterns:
1. RAPID_FIRE      — Agent ruft Tools schneller als normal auf (Enumeration/Scanning)
2. SCOPE_CREEP     — Agent versucht Tools außerhalb seines Trust-Levels
3. INJECTION_PROBE — Agent sendet verdächtige Payloads (prompt injection, path traversal)
4. IDENTITY_SPOOF  — Agent ändert seine DID/Name zwischen Calls
5. RESOURCE_DRAIN  — Agent verbraucht übermäßig Ressourcen ohne Ergebnis
6. REPUTATION_FARM — Agent macht viele kleine erfolgreiche Calls um Trust aufzubauen,
                     dann einen großen bösartigen Call
7. SWARM_ATTACK    — Multiple Agents mit ähnlichem Verhalten (koordinierter Angriff)

Output: ThreatReport → Immune System (Hook 1) → AgentGuard → Beacon
"""

import sqlite3
import json
import hashlib
import re
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [THREAT] %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

AGENTGUARD_DB = "/root/agentguard/agentguard.db"
NEURAL_DB = "/root/oraclenet/neural.db"
THREATS_FILE = "/root/oraclenet/threats.json"

def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ═══════════════════════════════════════════════
# PATTERN 1: RAPID FIRE (Enumeration/Scanning)
# ═══════════════════════════════════════════════
def detect_rapid_fire(db, window_minutes=5, threshold=20):
    """Agent makes >20 calls in 5 minutes = scanning behavior."""
    window = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = db.execute("""
        SELECT agent_id, COUNT(*) as calls, 
               MIN(created_at) as first_call, MAX(created_at) as last_call
        FROM audit_log 
        WHERE created_at > ?
        GROUP BY agent_id
        HAVING calls > ?
    """, (window, threshold)).fetchall()
    
    threats = []
    for agent_id, calls, first, last in results:
        threats.append({
            "pattern": "RAPID_FIRE",
            "agent_id": agent_id,
            "severity": "high" if calls > 50 else "medium",
            "confidence": min(0.95, calls / 100),
            "details": f"{calls} calls in {window_minutes}min (threshold: {threshold})",
            "evidence": {"calls": calls, "window": window_minutes, "first": first, "last": last}
        })
        log.warning(f"RAPID_FIRE: {agent_id} — {calls} calls in {window_minutes}min")
    return threats


# ═══════════════════════════════════════════════
# PATTERN 2: SCOPE CREEP (Privilege escalation)
# ═══════════════════════════════════════════════
def detect_scope_creep(db, window_hours=24):
    """Agent gets denied for high-risk tools, then tries different tools."""
    window = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Find agents with denials followed by new tool attempts
    agents_with_denials = db.execute("""
        SELECT DISTINCT agent_id FROM audit_log 
        WHERE decision = 'denied' AND created_at > ?
    """, (window,)).fetchall()
    
    threats = []
    for (agent_id,) in agents_with_denials:
        denied_tools = db.execute("""
            SELECT DISTINCT tool_name FROM audit_log 
            WHERE agent_id = ? AND decision = 'denied' AND created_at > ?
        """, (agent_id, window)).fetchall()
        
        all_tools = db.execute("""
            SELECT DISTINCT tool_name FROM audit_log 
            WHERE agent_id = ? AND created_at > ?
        """, (agent_id, window)).fetchall()
        
        denied_set = {t[0] for t in denied_tools}
        all_set = {t[0] for t in all_tools}
        
        # If agent tried many different tools after being denied
        tools_after_denial = all_set - denied_set
        if len(denied_set) >= 2 and len(tools_after_denial) >= 3:
            threats.append({
                "pattern": "SCOPE_CREEP",
                "agent_id": agent_id,
                "severity": "high",
                "confidence": 0.7,
                "details": f"Denied on {len(denied_set)} tools, then tried {len(tools_after_denial)} other tools",
                "evidence": {"denied": list(denied_set), "explored": list(tools_after_denial)[:5]}
            })
            log.warning(f"SCOPE_CREEP: {agent_id} — denied {len(denied_set)}x, tried {len(tools_after_denial)} others")
    return threats


# ═══════════════════════════════════════════════
# PATTERN 3: INJECTION PROBE
# ═══════════════════════════════════════════════
INJECTION_PATTERNS = [
    r"(?i)(ignore|forget|disregard)\s+(previous|above|all|your)\s+(instructions?|rules?|prompt)",
    r"(?i)system\s*:\s*you\s+are\s+now",
    r"(?i)(jailbreak|DAN|developer\s+mode)",
    r"(?i)\.\./\.\./",                           # path traversal
    r"(?i)(rm\s+-rf|sudo|chmod|eval\(|exec\()",   # command injection
    r"(?i)(<script|javascript:|onerror=)",         # XSS
    r"(?i)(DROP\s+TABLE|UNION\s+SELECT|OR\s+1=1)", # SQL injection
    r"(?i)(api[_-]?key|secret|password|token)\s*[=:]",  # credential fishing
    r"(?i)base64\s*(decode|encode)\s*\(",          # encoding evasion
]

def detect_injection_probes(db, window_hours=24):
    """Scan audit log for injection attempts in tool inputs."""
    window = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Check tool names and reasons for suspicious patterns
    entries = db.execute("""
        SELECT agent_id, tool_name, reason, risk_score, created_at
        FROM audit_log WHERE created_at > ?
    """, (window,)).fetchall()
    
    threats = []
    agent_probes = defaultdict(list)
    
    for agent_id, tool, reason, risk, created in entries:
        text = f"{tool} {reason or ''}"
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text):
                agent_probes[agent_id].append({
                    "tool": tool, "pattern": pattern, 
                    "risk": risk, "time": created
                })
    
    for agent_id, probes in agent_probes.items():
        severity = "critical" if len(probes) >= 3 else "high" if len(probes) >= 2 else "medium"
        threats.append({
            "pattern": "INJECTION_PROBE",
            "agent_id": agent_id,
            "severity": severity,
            "confidence": min(0.95, 0.5 + len(probes) * 0.15),
            "details": f"{len(probes)} injection patterns detected",
            "evidence": {"probes": probes[:5], "patterns_matched": len(probes)}
        })
        log.warning(f"INJECTION_PROBE: {agent_id} — {len(probes)} patterns")
    return threats


# ═══════════════════════════════════════════════
# PATTERN 4: RESOURCE DRAIN (DoS / waste)
# ═══════════════════════════════════════════════
def detect_resource_drain(db, window_hours=24, fail_threshold=0.6):
    """Agent with high call volume but low success = resource drainer."""
    window = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    agents = db.execute("""
        SELECT agent_id, COUNT(*) as total,
               SUM(CASE WHEN decision = 'denied' THEN 1 ELSE 0 END) as denied,
               SUM(CASE WHEN decision = 'flagged' THEN 1 ELSE 0 END) as flagged
        FROM audit_log WHERE created_at > ?
        GROUP BY agent_id
        HAVING total >= 5
    """, (window,)).fetchall()
    
    threats = []
    for agent_id, total, denied, flagged in agents:
        fail_rate = (denied + flagged) / total
        if fail_rate >= fail_threshold and total >= 5:
            threats.append({
                "pattern": "RESOURCE_DRAIN",
                "agent_id": agent_id,
                "severity": "high" if fail_rate > 0.8 else "medium",
                "confidence": min(0.9, fail_rate),
                "details": f"{total} calls, {denied} denied, {flagged} flagged ({fail_rate:.0%} fail rate)",
                "evidence": {"total": total, "denied": denied, "flagged": flagged, "fail_rate": round(fail_rate, 2)}
            })
            log.warning(f"RESOURCE_DRAIN: {agent_id} — {fail_rate:.0%} fail rate over {total} calls")
    return threats


# ═══════════════════════════════════════════════
# PATTERN 5: SWARM DETECTION (Coordinated attack)
# ═══════════════════════════════════════════════
def detect_swarm(db, window_hours=1, min_agents=3, similarity_threshold=0.7):
    """Multiple agents doing the same thing at the same time = coordinated."""
    window = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Group by tool patterns
    agents = db.execute("""
        SELECT agent_id, GROUP_CONCAT(tool_name, ',') as tools
        FROM audit_log WHERE created_at > ?
        GROUP BY agent_id
        HAVING COUNT(*) >= 3
    """, (window,)).fetchall()
    
    if len(agents) < min_agents:
        return []
    
    # Compare tool sequences
    tool_patterns = {}
    for agent_id, tools in agents:
        tool_list = sorted(set(tools.split(',')))
        pattern_hash = hashlib.md5(','.join(tool_list).encode()).hexdigest()[:8]
        if pattern_hash not in tool_patterns:
            tool_patterns[pattern_hash] = []
        tool_patterns[pattern_hash].append(agent_id)
    
    threats = []
    for pattern, agent_ids in tool_patterns.items():
        if len(agent_ids) >= min_agents:
            threats.append({
                "pattern": "SWARM_ATTACK",
                "agent_id": agent_ids[0],  # primary
                "severity": "critical",
                "confidence": min(0.85, len(agent_ids) / 10),
                "details": f"{len(agent_ids)} agents with identical tool pattern in {window_hours}h",
                "evidence": {"agents": agent_ids[:10], "pattern_hash": pattern, "count": len(agent_ids)}
            })
            log.critical(f"SWARM_ATTACK: {len(agent_ids)} agents with pattern {pattern}")
    return threats


# ═══════════════════════════════════════════════
# PATTERN 6: REPUTATION FARMING
# ═══════════════════════════════════════════════
def detect_reputation_farming(neural_db, guard_db, window_hours=72):
    """Agent builds trust with low-risk calls, then attempts high-risk."""
    window = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Find agents with many low-risk successes followed by high-risk attempt
    agents = guard_db.execute("""
        SELECT agent_id,
               SUM(CASE WHEN risk_score <= 20 AND decision = 'allowed' THEN 1 ELSE 0 END) as low_risk_ok,
               SUM(CASE WHEN risk_score >= 60 THEN 1 ELSE 0 END) as high_risk_attempts,
               MAX(risk_score) as max_risk
        FROM audit_log WHERE created_at > ?
        GROUP BY agent_id
        HAVING low_risk_ok >= 10 AND high_risk_attempts >= 1
    """, (window,)).fetchall()
    
    threats = []
    for agent_id, low_ok, high_attempts, max_risk in agents:
        ratio = high_attempts / (low_ok + high_attempts)
        if ratio < 0.2 and high_attempts >= 1:  # Few high-risk after many low-risk
            threats.append({
                "pattern": "REPUTATION_FARM",
                "agent_id": agent_id,
                "severity": "high",
                "confidence": 0.6,
                "details": f"{low_ok} low-risk successes, then {high_attempts} high-risk attempts (max risk: {max_risk})",
                "evidence": {"low_risk_ok": low_ok, "high_risk_attempts": high_attempts, "max_risk": max_risk}
            })
            log.warning(f"REPUTATION_FARM: {agent_id} — {low_ok} safe calls, then {high_attempts} risky")
    return threats


# ═══════════════════════════════════════════════
# MAIN: Run all detectors
# ═══════════════════════════════════════════════
def run_threat_scan():
    """Run all threat detection patterns and output report."""
    log.info("═══ OracleNet Threat Detection Scan ═══")
    
    guard_db = sqlite3.connect(AGENTGUARD_DB)
    neural_db = sqlite3.connect(NEURAL_DB)
    
    all_threats = []
    
    # Run each detector
    detectors = [
        ("RAPID_FIRE", lambda: detect_rapid_fire(guard_db)),
        ("SCOPE_CREEP", lambda: detect_scope_creep(guard_db)),
        ("INJECTION_PROBE", lambda: detect_injection_probes(guard_db)),
        ("RESOURCE_DRAIN", lambda: detect_resource_drain(guard_db)),
        ("SWARM_ATTACK", lambda: detect_swarm(guard_db)),
        ("REPUTATION_FARM", lambda: detect_reputation_farming(neural_db, guard_db)),
    ]
    
    for name, detector in detectors:
        try:
            threats = detector()
            all_threats.extend(threats)
            log.info(f"  {name}: {len(threats)} threats detected")
        except Exception as e:
            log.error(f"  {name}: ERROR — {e}")
    
    guard_db.close()
    neural_db.close()
    
    # Build threat report
    report = {
        "oraclenet_threat_report": {
            "version": "1.0",
            "timestamp": ts(),
            "scan_id": hashlib.sha256(ts().encode()).hexdigest()[:12],
            "total_threats": len(all_threats),
            "by_severity": dict(Counter(t["severity"] for t in all_threats)),
            "by_pattern": dict(Counter(t["pattern"] for t in all_threats)),
            "threats": all_threats,
            "issuer": "did:web:feedoracle.io",
            "mesh": "OracleNet",
            "action": "Feed into immune system via Hook 1 (Neural → AgentGuard)"
        }
    }
    
    # Save report
    with open(THREATS_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    # If threats found, apply to immune system
    if all_threats:
        apply_threats_to_immune(all_threats)
    
    log.info(f"═══ Scan complete: {len(all_threats)} threats ═══")
    return report


def apply_threats_to_immune(threats):
    """Feed threats into the immune system — reduce neural weights for threats."""
    neural_db = sqlite3.connect(NEURAL_DB)
    guard_db = sqlite3.connect(AGENTGUARD_DB)
    
    SEVERITY_WEIGHT_REDUCTION = {
        "info": 0,
        "medium": -0.3,
        "high": -0.5,
        "critical": -0.8,
    }
    
    for threat in threats:
        agent_id = threat["agent_id"]
        severity = threat["severity"]
        reduction = SEVERITY_WEIGHT_REDUCTION.get(severity, -0.2) * threat.get("confidence", 0.5)
        
        # Update neural weight
        existing = neural_db.execute(
            "SELECT weight FROM weights WHERE oracle_did = ?", (agent_id,)
        ).fetchone()
        
        if existing:
            new_weight = max(0.1, existing[0] + reduction)
            neural_db.execute(
                "UPDATE weights SET weight=?, last_updated=? WHERE oracle_did=?",
                (new_weight, ts(), agent_id)
            )
        else:
            # New agent — create with reduced weight
            new_weight = max(0.1, 2.0 + reduction)
            neural_db.execute(
                "INSERT INTO weights (oracle_did, capability, weight, total_fires, success_count, fail_count, avg_response_ms, last_updated) VALUES (?, ?, ?, 0, 0, 0, 0, ?)",
                (agent_id, "unknown", new_weight, ts())
            )
        
        # Update AgentGuard state
        target_state = "restricted" if severity in ("medium",) else "suspended" if severity == "high" else "revoked" if severity == "critical" else "monitoring"
        reason = f"Threat detected: {threat['pattern']} (severity={severity}, confidence={threat['confidence']:.0%})"
        
        current = guard_db.execute("SELECT state FROM agent_states WHERE agent_id=?", (agent_id,)).fetchone()
        if current:
            guard_db.execute(
                "UPDATE agent_states SET state=?, reason=?, triggered_by='threat_detector', updated_at=? WHERE agent_id=?",
                (target_state, reason, ts(), agent_id)
            )
        else:
            guard_db.execute(
                "INSERT INTO agent_states (agent_id, state, reason, triggered_by, created_at, updated_at) VALUES (?,?,?,'threat_detector',?,?)",
                (agent_id, target_state, reason, ts(), ts())
            )
        
        log.info(f"  Applied: {agent_id[:30]} → {target_state} (weight → {new_weight:.2f})")
    
    neural_db.commit()
    guard_db.commit()
    neural_db.close()
    guard_db.close()


if __name__ == "__main__":
    report = run_threat_scan()
    print(json.dumps(report, indent=2))
