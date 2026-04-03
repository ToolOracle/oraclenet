"""
Example: Screen a name against EU + OFAC + UN sanctions lists.
87,000+ names cached in memory. Sub-second response.
"""
import httpx

def screen(name: str):
    r = httpx.post("https://tooloracle.io/aml/mcp", json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {
            "name": "sanctions_screen",
            "arguments": {"name": name}
        }
    }, headers={"Content-Type": "application/json"})
    return r.json()

if __name__ == "__main__":
    result = screen("Acme Corporation")
    content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
    print(content[:500])
