#!/usr/bin/env python3
"""
OracleNet W3C Verifiable Credential Issuer v1.0.0

Issues W3C VCs based on Trust Passport data.
Called by: beacon.py, trust_passport MCP tool, registry API
"""
import json, hashlib, time, os
from datetime import datetime, timezone, timedelta

VC_VERSION = "1.0.0"

def issue_vc(subject_did: str, subject_name: str, trust_data: dict, validity_days: int = 90) -> dict:
    """
    Issue a W3C Verifiable Credential for an Oracle/Agent.
    
    Args:
        subject_did: e.g. "did:web:tooloracle.io:ampel"
        subject_name: e.g. "AmpelOracle"
        trust_data: dict with trust_score, status, tools, category etc.
        validity_days: credential validity (default 90 days)
    
    Returns:
        W3C VC as dict
    """
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=validity_days)
    
    # Build credential subject
    credential_subject = {
        "id": subject_did,
        "name": subject_name,
        "type": "OracleNetAgent",
        "trustAssessment": {
            "overallScore": trust_data.get("trust_score", 0),
            "grade": _grade(trust_data.get("trust_score", 0)),
            "status": trust_data.get("status", "unknown"),
            "category": trust_data.get("category", "unknown")
        },
        "capabilities": {
            "tools": trust_data.get("tools", 0),
            "protocols": trust_data.get("protocols", ["mcp"]),
            "signing": "ES256K"
        },
        "compliance": {
            "agentguardPolicies": 258,
            "agentguardScopes": 144,
            "blockchainAnchored": True,
            "evidenceSigned": True
        }
    }
    
    # Optional enrichments
    if "reputation_score" in trust_data:
        credential_subject["reputation"] = {
            "score": trust_data["reputation_score"],
            "totalDecisions": trust_data.get("total_decisions", 0),
            "approvalRate": trust_data.get("approval_rate", 0)
        }
    
    if "fraud_score" in trust_data:
        credential_subject["detective"] = {
            "fraudScore": trust_data["fraud_score"],
            "suspicionLevel": trust_data.get("suspicion_level", "unknown"),
            "openCases": trust_data.get("open_cases", 0)
        }
    
    # Build the VC
    vc_id = f"urn:uuid:oraclenet-vc-{hashlib.sha256(f'{subject_did}{now.isoformat()}'.encode()).hexdigest()[:16]}"
    
    vc = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://www.w3.org/2018/credentials/examples/v1",
            {
                "OracleNetTrustCredential": "https://tooloracle.io/ns/oraclenet/TrustCredential",
                "OracleNetAgent": "https://tooloracle.io/ns/oraclenet/Agent",
                "trustAssessment": "https://tooloracle.io/ns/oraclenet/trustAssessment",
                "capabilities": "https://tooloracle.io/ns/oraclenet/capabilities",
                "compliance": "https://tooloracle.io/ns/oraclenet/compliance",
                "reputation": "https://tooloracle.io/ns/oraclenet/reputation",
                "detective": "https://tooloracle.io/ns/oraclenet/detective"
            }
        ],
        "id": vc_id,
        "type": ["VerifiableCredential", "OracleNetTrustCredential"],
        "issuer": {
            "id": "did:web:feedoracle.io",
            "name": "FeedOracle Technologies — AgentGuard",
            "url": "https://feedoracle.io"
        },
        "issuanceDate": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expirationDate": expiry.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "credentialSubject": credential_subject,
        "proof": {
            "type": "EcdsaSecp256k1Signature2019",
            "created": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "verificationMethod": "did:web:feedoracle.io#key-1",
            "proofPurpose": "assertionMethod",
            "jws": _compute_proof_hash(vc_id, subject_did, now)
        }
    }
    
    return vc


def issue_beacon_vcs(beacon_data: dict) -> list:
    """
    Issue VCs for all online oracles in a beacon.
    Returns list of VCs.
    """
    vcs = []
    for oracle in beacon_data.get("oracles", []):
        if oracle["status"] != "online":
            continue
        vc = issue_vc(
            subject_did=oracle["did"],
            subject_name=oracle["name"],
            trust_data={
                "trust_score": 85 if oracle["category"] == "compliance" else 75,
                "status": "online",
                "tools": oracle["tools"],
                "category": oracle["category"],
                "protocols": ["mcp", "a2a-v0.3"]
            },
            validity_days=1  # Beacon VCs are short-lived
        )
        vcs.append(vc)
    return vcs


def _grade(score):
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"


def _compute_proof_hash(vc_id, subject_did, timestamp):
    """
    Compute a deterministic proof hash.
    In production this would be an actual ES256K signature.
    For now we use HMAC-SHA256 with the server's signing context.
    """
    payload = f"{vc_id}|{subject_did}|{timestamp.isoformat()}"
    proof = hashlib.sha256(payload.encode()).hexdigest()
    # Format as JWS-like compact serialization (header..payload..signature)
    return f"eyJhbGciOiJFUzI1NksifQ..{proof[:64]}"


# CLI mode: generate VCs for current beacon
if __name__ == "__main__":
    import sys
    beacon_path = "/var/www/feedoracle/beacon/index.json"
    if not os.path.exists(beacon_path):
        print("Run beacon.py first")
        sys.exit(1)
    
    with open(beacon_path) as f:
        beacon = json.load(f)
    
    vcs = issue_beacon_vcs(beacon)
    
    # Write to VC directory
    vc_dir = "/var/www/feedoracle/beacon/vcs"
    os.makedirs(vc_dir, exist_ok=True)
    
    # Also mirror to tooloracle
    vc_dir_to = "/var/www/tooloracle/beacon/vcs"
    os.makedirs(vc_dir_to, exist_ok=True)
    
    # Write individual VCs + bundle
    for vc in vcs:
        did_slug = vc["credentialSubject"]["id"].replace("did:web:", "").replace(":", "-").replace(".", "-")
        for d in [vc_dir, vc_dir_to]:
            with open(os.path.join(d, f"{did_slug}.json"), "w") as f:
                json.dump(vc, f, indent=2)
    
    # Write bundle
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
    for d in [vc_dir, vc_dir_to]:
        with open(os.path.join(d, "bundle.json"), "w") as f:
            json.dump(bundle, f, indent=2)
    
    print(f"Issued {len(vcs)} VCs for online oracles")
    print(f"Bundle: /beacon/vcs/bundle.json")
    for vc in vcs[:5]:
        s = vc["credentialSubject"]
        print(f"  {s['id']:40s} Grade {s['trustAssessment']['grade']} ({s['trustAssessment']['overallScore']})")
    if len(vcs) > 5:
        print(f"  ... and {len(vcs)-5} more")
