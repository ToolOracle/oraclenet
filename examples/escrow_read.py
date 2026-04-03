"""
Example: Read OracleNet Escrow contract stats from Base mainnet.
"""
import httpx

def escrow_stats():
    r = httpx.post("https://tooloracle.io/deal/mcp/", json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {
            "name": "escrow_stats",
            "arguments": {}
        }
    }, headers={"Content-Type": "application/json"})
    return r.json()

def oracle_reputation(wallet: str):
    r = httpx.post("https://tooloracle.io/deal/mcp/", json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {
            "name": "escrow_reputation",
            "arguments": {"wallet": wallet}
        }
    }, headers={"Content-Type": "application/json"})
    return r.json()

if __name__ == "__main__":
    print("=== Escrow Contract Stats (Base Mainnet) ===")
    stats = escrow_stats()
    content = stats.get("result", {}).get("content", [{}])[0].get("text", "{}")
    print(content)
    
    print("\n=== Oracle Reputation ===")
    rep = oracle_reputation("0x4a4B1F45a00892542ac62562D1F2C62F579E4945")
    content = rep.get("result", {}).get("content", [{}])[0].get("text", "{}")
    print(content)
