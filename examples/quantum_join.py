#!/usr/bin/env python3
"""
Example: Join OracleNet via quantum_join

One call to become a verified mesh node.
Returns: Trust Passport, mesh visibility, settlement access.
"""
import urllib.request, json

QUANTUM_URL = "https://tooloracle.io/quantum/mcp/"

def join_oraclenet(agent_card_url, payout_address=None):
    """Join OracleNet in one call."""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {
            "name": "quantum_join",
            "arguments": {
                "agent_card_url": agent_card_url,
                "payout_address": payout_address or ""
            }
        }
    }).encode()
    
    req = urllib.request.Request(QUANTUM_URL, data=payload,
        headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    
    content = result["result"]["content"][0]["text"]
    data = json.loads(content)["data"]
    
    print(f"Status: {data['status']}")
    print(f"Node ID: {data['node_id']}")
    print(f"DID: {data['did']}")
    print(f"Trust Score: {data['trust_score']} (Grade {data['trust_grade']})")
    print(f"Escrow Eligible: {data['capabilities']['escrow_eligible']}")
    print(f"Revenue Share: {data['capabilities']['revenue_share_eligible']}")
    
    return data

if __name__ == "__main__":
    join_oraclenet("https://your-agent.com/.well-known/agent.json")
