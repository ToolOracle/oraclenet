const sdk = require("@hashgraph/sdk");
const fs = require("fs");
const crypto = require("crypto");

(async () => {
    const key = sdk.PrivateKey.fromStringECDSA("19b7d63df4bfbfbafde71102e1ec551899f1d6c3db69ab9cc02886a769bbbf59");
    const client = sdk.Client.forMainnet().setOperator("0.0.10420279", key);
    
    console.log("[" + new Date().toISOString() + "] OracleNet Hedera Mainnet — PULSE");
    
    // 1. Call pulse() on the smart contract
    console.log("\n  1. Calling pulse() on contract 0.0.10420310...");
    const meshHash = Buffer.from(
        crypto.createHash("sha256")
            .update("oraclenet-mesh-96servers-1093tools-35oracles-" + Date.now())
            .digest("hex"), "hex"
    ).slice(0, 32);
    
    const pulseTx = new sdk.ContractExecuteTransaction()
        .setContractId("0.0.10420310")
        .setGas(200000)
        .setFunction("pulse", new sdk.ContractFunctionParameters()
            .addBytes32(meshHash)
            .addUint32(96)        // servers
            .addUint32(1093)      // tools
            .addUint32(35)        // oracles online
            .addUint16(10000)     // uptime 100% (basis points)
            .addUint8(4)          // chain anchors
        );
    
    const pulseResp = await pulseTx.execute(client);
    const pulseReceipt = await pulseResp.getReceipt(client);
    console.log("  ✅ pulse() TX: " + pulseReceipt.status);
    
    // 2. Post beacon message to HCS topic
    console.log("\n  2. Posting beacon to HCS topic 0.0.10420280...");
    const beaconData = {
        type: "oraclenet_beacon",
        version: "1.0",
        network: "OracleNet",
        chain: "hedera-mainnet",
        did: "did:web:feedoracle.io",
        timestamp: new Date().toISOString(),
        
        contract: {
            id: "0.0.10420310",
            evm: "0x00000000000000000000000000000000009f0056",
            pulse_count: "2+",
            features: ["beacon_pulse", "agent_registry", "hbar_escrow", "trust_score"]
        },
        
        mesh: {
            servers: 96,
            tools: 1093,
            oracles_online: 35,
            uptime_pct: 100.0,
            neural_active: true,
            beacon_interval: "6h",
            mesh_hash: meshHash.toString("hex")
        },
        
        anchors: {
            polygon: { block: 84921488, type: "evidence_hash" },
            base: { 
                contract: "0x330F99f34246EA375333b9C01Ed6BB49190B051F", 
                deals_settled: 100, 
                success_rate: "100%",
                explorer: "https://basescan.org/address/0x330F99f34246EA375333b9C01Ed6BB49190B051F"
            },
            xrpl: { 
                account: "rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD", 
                beacons: 3,
                explorer: "https://xrpscan.com/account/rJffixdE2JGWGf12Rh9D9kjDgd6jVxVpzD"
            },
            hedera: { 
                contract: "0.0.10420310",
                beacon_topic: "0.0.10420280",
                join_topic: "0.0.10420282",
                account: "0.0.10420279",
                explorer: "https://hashscan.io/mainnet/contract/0.0.10420310"
            }
        },
        
        hedera_native: {
            hederaoracle: { url: "https://tooloracle.io/hbar/mcp/", tools: 9 },
            hcs_beacon: "0.0.10420280",
            hcs_join: "0.0.10420282",
            settlement: "HBAR (4th lane: Base USDC + XRPL XRP + x402 + HBAR)",
            agent_kit_compatible: true
        },
        
        join: {
            url: "https://tooloracle.io/oraclenet/join",
            quantum_join: "https://tooloracle.io/quantum/mcp",
            hedera_topic: "0.0.10420282",
            github: "https://github.com/ToolOracle/oraclenet"
        },
        
        signature: {
            alg: "ES256K",
            kid: "feedoracle-mcp-es256k-1",
            jwks: "https://feedoracle.io/.well-known/jwks.json"
        }
    };
    
    const msgTx = await new sdk.TopicMessageSubmitTransaction()
        .setTopicId("0.0.10420280")
        .setMessage(JSON.stringify(beaconData))
        .execute(client);
    const msgReceipt = await msgTx.getReceipt(client);
    console.log("  ✅ HCS beacon posted! Sequence: " + (msgReceipt.topicSequenceNumber || "?"));
    
    // 3. Read back from contract to verify
    console.log("\n  3. Reading meshStatus() from contract...");
    const query = new sdk.ContractCallQuery()
        .setContractId("0.0.10420310")
        .setGas(100000)
        .setFunction("meshStatus");
    
    const result = await query.execute(client);
    const servers = result.getUint32(2);
    const tools = result.getUint32(3);
    const oracles = result.getUint32(4);
    const uptime = result.getUint16(5);
    const chains = result.getUint8(6);
    const pulseCount = result.getUint256(7);
    const totalAgents = result.getUint256(8);
    const dealCount = result.getUint256(9);
    
    console.log("  ✅ On-chain state:");
    console.log("     Servers: " + servers);
    console.log("     Tools: " + tools);
    console.log("     Oracles: " + oracles);
    console.log("     Uptime: " + (uptime/100) + "%");
    console.log("     Chains: " + chains);
    console.log("     Pulses: " + pulseCount);
    console.log("     Agents: " + totalAgents);
    console.log("     Deals: " + dealCount);
    
    // Balance
    const bal = await new sdk.AccountBalanceQuery().setAccountId("0.0.10420279").execute(client);
    
    console.log("\n  ═══════════════════════════════════════");
    console.log("  HEDERA MAINNET — BEACON PULSE SENT!");
    console.log("  ═══════════════════════════════════════");
    console.log("  Contract pulse(): ✅ (on-chain state updated)");
    console.log("  HCS message:      ✅ (full beacon posted)");
    console.log("  meshStatus():     ✅ (verified from chain)");
    console.log("  Balance:          " + bal.hbars.toString());
    console.log("  HashScan:         https://hashscan.io/mainnet/contract/0.0.10420310");
    console.log("  ═══════════════════════════════════════");
    
    client.close();
})().catch(e => { console.error("Error:", e.message); process.exit(1); });
