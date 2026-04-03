#!/usr/bin/env python3
"""
OracleNet Intelligence Transfer Protocol v1.0.0

When oracles communicate, context travels with data:
- WHO produced this data (source DID)
- HOW it was produced (method, model, confidence)
- WHEN it was produced (timestamp, freshness)
- WHAT evidence backs it (hashes, anchors)
- WHY it matters (regulatory context, cross-references)

Uses JSON-LD + W3C PROV-O (Provenance Ontology)
"""
import json, hashlib, os
from datetime import datetime, timezone

VERSION = "1.0.0"

# ══════════════════════════════════════════════════════════════
# PROV-O Activity Types (what kind of work produced this data)
# ══════════════════════════════════════════════════════════════
ACTIVITY_TYPES = {
    "assessment": "prov:Activity — Compliance assessment against regulatory requirements",
    "evidence_collection": "prov:Activity — Gathering evidence from external sources",
    "risk_scoring": "prov:Activity — Computing risk or trust scores",
    "finding_creation": "prov:Activity — Identifying a compliance gap or issue",
    "report_generation": "prov:Activity — Generating a signed compliance report",
    "drift_detection": "prov:Activity — Detecting regulatory, evidence, or control drift",
    "prediction": "prov:Activity — Forecasting future compliance state",
    "verification": "prov:Activity — Verifying a claim or signature",
    "sanctions_screening": "prov:Activity — Screening against sanctions lists",
    "contract_analysis": "prov:Activity — Analyzing contract clauses against Art. 30",
    "incident_classification": "prov:Activity — Classifying an ICT incident per ITS 2024/1772",
    "threat_intelligence": "prov:Activity — CVE/KEV/CERT-Bund threat data collection",
}

def create_intelligence_package(
    source_did: str,
    source_name: str,
    target_did: str,
    activity_type: str,
    data: dict,
    data_sources: list = None,
    confidence: float = 0.9,
    regulatory_context: list = None,
    cross_references: list = None,
    parent_package_id: str = None,
) -> dict:
    """
    Create an Intelligence Transfer Package (ITP).
    
    This is what travels between oracles instead of raw JSON.
    It carries the full provenance graph of how the data was produced.
    """
    now = datetime.now(timezone.utc)
    
    # Compute content hash of the actual data
    data_hash = hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()
    
    # Package ID based on source + target + time + data hash
    pkg_id = f"itp:{hashlib.sha256(f'{source_did}:{target_did}:{now.isoformat()}:{data_hash}'.encode()).hexdigest()[:24]}"
    
    package = {
        "@context": {
            "@vocab": "https://schema.org/",
            "prov": "http://www.w3.org/ns/prov#",
            "oraclenet": "https://tooloracle.io/ns/oraclenet/",
            "xsd": "http://www.w3.org/2001/XMLSchema#"
        },
        "@type": "oraclenet:IntelligenceTransferPackage",
        "id": pkg_id,
        "version": VERSION,
        
        # ── WHO ──
        "prov:wasGeneratedBy": {
            "@type": "prov:Activity",
            "prov:type": activity_type,
            "prov:description": ACTIVITY_TYPES.get(activity_type, "Unknown activity"),
            "prov:wasAssociatedWith": {
                "@type": "prov:Agent",
                "prov:id": source_did,
                "name": source_name
            },
            "prov:startedAtTime": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        
        # ── FROM → TO ──
        "source": {
            "did": source_did,
            "name": source_name,
            "vc": f"https://feedoracle.io/beacon/vcs/{source_did.replace('did:web:', '').replace(':', '-').replace('.', '-')}.json"
        },
        "target": {
            "did": target_did
        },
        
        # ── WHAT ──
        "payload": {
            "data": data,
            "contentHash": data_hash,
            "hashAlgorithm": "SHA-256"
        },
        
        # ── HOW (Confidence + Method) ──
        "confidence": {
            "score": confidence,
            "level": "high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low"
        },
        
        # ── WHEN ──
        "temporality": {
            "generatedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "freshness": "real-time",
            "ttl_seconds": 300  # Valid for 5 minutes by default
        },
        
        # ── WHERE (Data Sources with full provenance) ──
        "prov:wasDerivedFrom": [],
        
        # ── WHY (Regulatory Context) ──
        "regulatoryContext": regulatory_context or [],
        
        # ── LINKS ──
        "crossReferences": cross_references or [],
        
        # ── LINEAGE ──
        "lineage": {
            "parentPackageId": parent_package_id,
            "depth": 0 if parent_package_id is None else 1
        },
        
        # ── VERIFICATION ──
        "verification": {
            "signing": "ES256K",
            "jwks": "https://feedoracle.io/.well-known/jwks.json",
            "issuerDid": "did:web:feedoracle.io",
            "proof": hashlib.sha256(f"{pkg_id}:{data_hash}:{now.isoformat()}".encode()).hexdigest()
        }
    }
    
    # Add data sources as PROV-O derivation chain
    if data_sources:
        for ds in data_sources:
            package["prov:wasDerivedFrom"].append({
                "@type": "prov:Entity",
                "prov:id": ds.get("id", "unknown"),
                "name": ds.get("name", "unknown"),
                "prov:type": ds.get("type", "external_api"),
                "url": ds.get("url", ""),
                "fetchedAt": ds.get("fetched_at", now.strftime("%Y-%m-%dT%H:%M:%SZ")),
                "freshness": ds.get("freshness", "unknown"),
                "contentHash": ds.get("content_hash", "")
            })
    
    return package


def wrap_oracle_call(source_did, source_name, target_did, tool_name, result, data_sources=None, regulatory_refs=None):
    """
    Convenience wrapper: wrap a raw oracle tool call result in an ITP.
    
    Usage in Conductor:
        raw = _call_oracle("ampel", "readiness_check", {"entity_id": "..."})
        itp = wrap_oracle_call(
            source_did="did:web:feedoracle.io:ampel",
            source_name="AmpelOracle",
            target_did="did:web:tooloracle.io:conductor",
            tool_name="readiness_check",
            result=raw,
            data_sources=[{"name": "DORA Ampel DB", "type": "internal_db"}],
            regulatory_refs=["DORA Art. 5-6"]
        )
    """
    # Map tool names to activity types
    activity_map = {
        "readiness_check": "assessment",
        "board_report": "report_generation",
        "board_summary": "report_generation",
        "gap_report": "assessment",
        "evidence_summary": "evidence_collection",
        "collect_art10": "threat_intelligence",
        "freshness_check": "evidence_collection",
        "escalation_status": "finding_creation",
        "full_drift_scan": "drift_detection",
        "predict_score": "prediction",
        "early_warning": "prediction",
        "sanctions_screen": "sanctions_screening",
        "kyc_bundle": "sanctions_screening",
        "clause_check": "contract_analysis",
        "incident_report": "incident_classification",
        "cve_search": "threat_intelligence",
        "kev_check": "threat_intelligence",
        "threshold_proof": "verification",
        "compliance_preflight": "assessment",
    }
    
    activity = activity_map.get(tool_name, "assessment")
    
    return create_intelligence_package(
        source_did=source_did,
        source_name=source_name,
        target_did=target_did,
        activity_type=activity,
        data=result,
        data_sources=data_sources,
        confidence=0.95 if isinstance(result, dict) and "error" not in result else 0.3,
        regulatory_context=regulatory_refs,
    )


# ══════════════════════════════════════════════════════════════
# ITP Log — Persistent record of all intelligence transfers
# ══════════════════════════════════════════════════════════════

ITP_LOG_DIR = "/root/oraclenet/itp_log"

def log_transfer(package: dict):
    """Log an ITP to the persistent transfer log."""
    os.makedirs(ITP_LOG_DIR, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = os.path.join(ITP_LOG_DIR, f"{date}.jsonl")
    
    entry = {
        "id": package["id"],
        "timestamp": package["temporality"]["generatedAt"],
        "source": package["source"]["did"],
        "target": package["target"]["did"],
        "activity": package["prov:wasGeneratedBy"]["prov:type"],
        "confidence": package["confidence"]["score"],
        "data_hash": package["payload"]["contentHash"],
        "sources_count": len(package["prov:wasDerivedFrom"]),
        "regulatory": package["regulatoryContext"]
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ══════════════════════════════════════════════════════════════
# CLI Test
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Demo: AmpelOracle sends readiness result to Conductor
    demo_result = {
        "entity_id": "ent_09e73b0d",
        "entity_name": "Acme Zahlungsinstitut GmbH",
        "score": 86.5,
        "verdict": "ON TRACK",
        "green": 22, "yellow": 1, "red": 2,
        "findings_open": 3,
        "days_to_deadline": 88
    }
    
    itp = create_intelligence_package(
        source_did="did:web:feedoracle.io:ampel",
        source_name="AmpelOracle",
        target_did="did:web:tooloracle.io:conductor",
        activity_type="assessment",
        data=demo_result,
        data_sources=[
            {"id": "dora_ampel_db", "name": "DORA Ampel Database", "type": "internal_db", "freshness": "real-time"},
            {"id": "cisa_kev", "name": "CISA KEV", "type": "external_api", "url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "freshness": "daily"},
            {"id": "nvd", "name": "NIST NVD", "type": "external_api", "url": "https://nvd.nist.gov/", "freshness": "hourly"}
        ],
        confidence=0.95,
        regulatory_context=["DORA Art. 5-6", "DORA Art. 8", "RTS 2024/1774"],
        cross_references=[
            {"type": "obligation", "id": "DORA-GOV-01", "source": "did:web:tooloracle.io:law"},
            {"type": "polygon_anchor", "block": 84921488}
        ]
    )
    
    log_transfer(itp)
    
    print("=== Intelligence Transfer Package (ITP) ===")
    print(f"ID: {itp['id']}")
    print(f"Source: {itp['source']['did']} ({itp['source']['name']})")
    print(f"Target: {itp['target']['did']}")
    print(f"Activity: {itp['prov:wasGeneratedBy']['prov:type']}")
    print(f"Confidence: {itp['confidence']['score']} ({itp['confidence']['level']})")
    print(f"Data Hash: {itp['payload']['contentHash'][:20]}...")
    print(f"Data Sources: {len(itp['prov:wasDerivedFrom'])}")
    for ds in itp['prov:wasDerivedFrom']:
        print(f"  - {ds['name']} ({ds['prov:type']}, {ds['freshness']})")
    print(f"Regulatory: {itp['regulatoryContext']}")
    print(f"Cross-refs: {len(itp['crossReferences'])}")
    print(f"Verification: {itp['verification']['signing']}, JWKS: {itp['verification']['jwks']}")
    print(f"Logged to: {ITP_LOG_DIR}")
    
    # Write example to beacon directory for public access
    for d in ["/var/www/feedoracle/beacon", "/var/www/tooloracle/beacon"]:
        with open(os.path.join(d, "itp-example.json"), "w") as f:
            json.dump(itp, f, indent=2)
    print(f"\nExample published at /beacon/itp-example.json")
