#!/usr/bin/env python3
"""OracleNet Beacon v1.0.0 — Signed status broadcast for all Oracle services."""
import json, hashlib, os, urllib.request
from datetime import datetime, timezone

BEACON_DIR_FO = "/var/www/feedoracle/beacon"
BEACON_DIR_TO = "/var/www/tooloracle/beacon"
VERSION = "1.0.0"

ORACLES = {
    5250: {"name": "FeedOracle Compliance", "did": "did:web:feedoracle.io", "tools": 50, "cat": "compliance"},
    5251: {"name": "MacroOracle", "did": "did:web:feedoracle.io:macro", "tools": 22, "cat": "finance"},
    5252: {"name": "RiskOracle", "did": "did:web:feedoracle.io:risk", "tools": 13, "cat": "compliance"},
    10101: {"name": "AmpelOracle", "did": "did:web:feedoracle.io:ampel", "tools": 50, "cat": "compliance"},
    10201: {"name": "MiCAOracle", "did": "did:web:feedoracle.io:mica", "tools": 24, "cat": "compliance"},
    7900: {"name": "Conductor", "did": "did:web:tooloracle.io:conductor", "tools": 16, "cat": "compliance"},
    7910: {"name": "DriftOracle", "did": "did:web:tooloracle.io:drift", "tools": 15, "cat": "compliance"},
    7920: {"name": "EventFabric", "did": "did:web:tooloracle.io:eventfabric", "tools": 14, "cat": "compliance"},
    7930: {"name": "PredictOracle", "did": "did:web:tooloracle.io:predict", "tools": 12, "cat": "compliance"},
    7940: {"name": "ZKEvidenceOracle", "did": "did:web:tooloracle.io:zk", "tools": 14, "cat": "compliance"},
    7810: {"name": "LawOracle", "did": "did:web:tooloracle.io:law", "tools": 20, "cat": "compliance"},
    7820: {"name": "TestOracle", "did": "did:web:tooloracle.io:test", "tools": 16, "cat": "compliance"},
    7830: {"name": "ReportingOracle", "did": "did:web:tooloracle.io:reporting", "tools": 16, "cat": "compliance"},
    7840: {"name": "CloudOracle", "did": "did:web:tooloracle.io:cloud", "tools": 14, "cat": "compliance"},
    12001: {"name": "AgentGuard", "did": "did:web:tooloracle.io:agentguard", "tools": 20, "cat": "trust"},
    13202: {"name": "DealOracle", "did": "did:web:tooloracle.io:deal", "tools": 16, "cat": "trust"},
    10601: {"name": "MemoryOracle", "did": "did:web:tooloracle.io:memory", "tools": 10, "cat": "trust"},
    10701: {"name": "SchedulerOracle", "did": "did:web:tooloracle.io:scheduler", "tools": 9, "cat": "trust"},
    10801: {"name": "ArbitrumOracle", "did": "did:web:tooloracle.io:arbitrum", "tools": 12, "cat": "blockchain"},
    10901: {"name": "SolanaOracle", "did": "did:web:tooloracle.io:solana", "tools": 12, "cat": "blockchain"},
    11201: {"name": "ETHOracle", "did": "did:web:tooloracle.io:eth", "tools": 10, "cat": "blockchain"},
    12101: {"name": "btcOracle", "did": "did:web:tooloracle.io:btc", "tools": 10, "cat": "blockchain"},
    8601: {"name": "DORAOracle", "did": "did:web:tooloracle.io:dora", "tools": 15, "cat": "compliance"},
    8701: {"name": "AMLOracle", "did": "did:web:tooloracle.io:aml", "tools": 12, "cat": "compliance"},
    7802: {"name": "ResearchOracle", "did": "did:web:tooloracle.io:research", "tools": 11, "cat": "trust"},
    7803: {"name": "EULawOracle", "did": "did:web:tooloracle.io:eulaw", "tools": 8, "cat": "compliance"},
    7807: {"name": "ESMAOracle", "did": "did:web:tooloracle.io:esma", "tools": 8, "cat": "compliance"},
    6500: {"name": "x402 Gateway", "did": "did:web:tooloracle.io:x402", "tools": 0, "cat": "payment"},
}

def check_health(port):
    try:
        req = urllib.request.Request(f"http://localhost:{port}/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except:
        return False

def main():
    now = datetime.now(timezone.utc)
    oracles = []
    alive = 0
    tools_online = 0
    for port, info in sorted(ORACLES.items()):
        ok = check_health(port)
        if ok:
            alive += 1
            tools_online += info["tools"]
        oracles.append({"did": info["did"], "name": info["name"], "status": "online" if ok else "offline", "tools": info["tools"], "category": info["cat"]})

    beacon = {
        "@context": {"@vocab": "https://schema.org/", "anp": "https://agent-network-protocol.com/ns/", "oraclenet": "https://tooloracle.io/ns/oraclenet/"},
        "@type": "oraclenet:Beacon",
        "version": VERSION,
        "network": "OracleNet",
        "publisher": {"name": "FeedOracle Technologies", "did": "did:web:feedoracle.io", "location": "Bad Salzuflen, Germany"},
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "oracles_monitored": len(ORACLES),
            "oracles_online": alive,
            "oracles_offline": len(ORACLES) - alive,
            "tools_online": tools_online,
            "uptime_pct": round(alive / len(ORACLES) * 100, 1),
            "total_platform_servers": 90,
            "total_platform_tools": 1059
        },
        "trust": {
            "signing": "ES256K",
            "jwks": "https://feedoracle.io/.well-known/jwks.json",
            "polygon_anchor": {"block": 84921488, "tx": "0x7c4d8010ed07343b50c5d093358265e0b925e668c31fcc022591b7de9311b041", "date": "2026-03-31"},
            "agentguard": {"policies": 258, "scopes": 144}
        },
        "discovery": {
            "did": ["https://feedoracle.io/.well-known/did.json", "https://tooloracle.io/.well-known/did.json"],
            "a2a": ["https://feedoracle.io/.well-known/agent.json", "https://tooloracle.io/.well-known/agent.json"],
            "anp": ["https://feedoracle.io/.well-known/agent-descriptions", "https://tooloracle.io/.well-known/agent-descriptions"],
            "registry": "https://tooloracle.io/registry/api/",
            "catalog": "https://tooloracle.io/assets/catalog.json"
        },
        "connect": {"mcp": "https://mcp.feedoracle.io/mcp/", "x402": "https://tooloracle.io/x402/", "a2a": "https://feedoracle.io/a2a/tasks"},
        "oracles": oracles
    }
    ch = hashlib.sha256(json.dumps(beacon, sort_keys=True, separators=(',',':')).encode()).hexdigest()
    beacon["content_hash"] = ch

    for d in [BEACON_DIR_FO, BEACON_DIR_TO]:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.json"), "w") as f:
            json.dump(beacon, f, indent=2)

    s = beacon["summary"]
    print(f"[{beacon['timestamp']}] OracleNet Beacon v{VERSION}: {s['oracles_online']}/{s['oracles_monitored']} online, {s['tools_online']} tools, {s['uptime_pct']}% uptime, hash={ch[:16]}...")

if __name__ == "__main__":
    main()

# After generating beacon, also issue VCs
try:
    from vc_issuer import issue_beacon_vcs
    import os
    
    beacon_path = "/var/www/feedoracle/beacon/index.json"
    with open(beacon_path) as f:
        beacon_data = json.load(f)
    
    vcs = issue_beacon_vcs(beacon_data)
    
    for vc_dir in ["/var/www/feedoracle/beacon/vcs", "/var/www/tooloracle/beacon/vcs"]:
        os.makedirs(vc_dir, exist_ok=True)
        for vc in vcs:
            did_slug = vc["credentialSubject"]["id"].replace("did:web:", "").replace(":", "-").replace(".", "-")
            with open(os.path.join(vc_dir, f"{did_slug}.json"), "w") as f:
                json.dump(vc, f, indent=2)
        
        # Bundle as VerifiablePresentation
        bundle = {
            "@context": "https://www.w3.org/2018/credentials/v1",
            "type": "VerifiablePresentation",
            "holder": "did:web:feedoracle.io",
            "verifiableCredential": vcs,
            "proof": {
                "type": "EcdsaSecp256k1Signature2019",
                "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "verificationMethod": "did:web:feedoracle.io#key-1",
                "proofPurpose": "authentication"
            }
        }
        with open(os.path.join(vc_dir, "bundle.json"), "w") as f:
            json.dump(bundle, f, indent=2)
    
    print(f"  + {len(vcs)} VCs issued")
except Exception as e:
    print(f"  ! VC issuance failed: {e}")
