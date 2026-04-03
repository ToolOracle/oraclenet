"""
Example: Run a MiCA compliance check on a stablecoin.
No API key needed for free tools.
"""
import httpx

def check_stablecoin(symbol: str):
    r = httpx.post("https://mcp.feedoracle.io/mcp/", json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {
            "name": "compliance_preflight",
            "arguments": {"symbol": symbol}
        }
    }, headers={"Accept": "application/json, text/event-stream"})
    return r.json()

if __name__ == "__main__":
    for token in ["USDC", "USDT", "EURC", "RLUSD", "DAI"]:
        result = check_stablecoin(token)
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        print(f"{token}: {content[:120]}...")
        print()
