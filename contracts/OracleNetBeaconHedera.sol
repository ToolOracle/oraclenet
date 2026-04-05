// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract OracleNetBeacon {
    address public owner;
    
    struct BeaconPulse {
        uint256 timestamp;
        bytes32 meshHash;
        uint32 servers;
        uint32 tools;
        uint32 oraclesOnline;
        uint16 uptimeBps;
        uint8 chainAnchors;
    }
    
    BeaconPulse public latestPulse;
    uint256 public pulseCount;
    
    event Beacon(uint256 indexed pulseId, bytes32 meshHash, uint32 servers, uint32 tools, uint32 oraclesOnline, uint16 uptimeBps);
    
    struct Agent {
        string did;
        string name;
        uint256 joinedAt;
        uint256 dealsCompleted;
        uint256 dealsDisputed;
        bool active;
    }
    
    mapping(address => Agent) public agents;
    address[] public agentList;
    uint256 public totalAgents;
    
    event AgentJoined(address indexed agent, string did, string name);
    
    struct Deal {
        address client;
        address oracle;
        uint256 amount;
        bytes32 taskHash;
        uint8 state;
        uint256 createdAt;
    }
    
    mapping(uint256 => Deal) public deals;
    uint256 public dealCount;
    uint256 public totalSettled;
    
    event DealCreated(uint256 indexed dealId, address indexed client, address indexed oracle, uint256 amount);
    event DealSettled(uint256 indexed dealId, uint256 amount);
    event DealDisputed(uint256 indexed dealId);
    
    constructor() {
        owner = msg.sender;
        latestPulse = BeaconPulse({
            timestamp: block.timestamp,
            meshHash: keccak256("OracleNet-Genesis-Hedera-Mainnet"),
            servers: 96,
            tools: 1093,
            oraclesOnline: 35,
            uptimeBps: 10000,
            chainAnchors: 4
        });
        pulseCount = 1;
        emit Beacon(1, latestPulse.meshHash, 96, 1093, 35, 10000);
    }
    
    modifier onlyOwner() { require(msg.sender == owner, "Not owner"); _; }
    
    function pulse(bytes32 meshHash, uint32 servers, uint32 tools, uint32 oraclesOnline, uint16 uptimeBps, uint8 chainAnchors) external onlyOwner {
        pulseCount++;
        latestPulse = BeaconPulse(block.timestamp, meshHash, servers, tools, oraclesOnline, uptimeBps, chainAnchors);
        emit Beacon(pulseCount, meshHash, servers, tools, oraclesOnline, uptimeBps);
    }
    
    function joinMesh(string calldata did, string calldata name) external {
        require(bytes(did).length > 0, "DID required");
        require(!agents[msg.sender].active, "Already joined");
        agents[msg.sender] = Agent(did, name, block.timestamp, 0, 0, true);
        agentList.push(msg.sender);
        totalAgents++;
        emit AgentJoined(msg.sender, did, name);
    }
    
    function trustScore(address agent) external view returns (uint256) {
        Agent memory a = agents[agent];
        if (a.dealsCompleted == 0) return 0;
        return (a.dealsCompleted * 100) / (a.dealsCompleted + a.dealsDisputed);
    }
    
    function createDeal(address oracle, bytes32 taskHash) external payable returns (uint256) {
        require(msg.value > 0, "No HBAR");
        dealCount++;
        deals[dealCount] = Deal(msg.sender, oracle, msg.value, taskHash, 0, block.timestamp);
        emit DealCreated(dealCount, msg.sender, oracle, msg.value);
        return dealCount;
    }
    
    function deliver(uint256 dealId) external {
        Deal storage d = deals[dealId];
        require(d.state == 0 && msg.sender == d.oracle, "Invalid");
        d.state = 1;
    }
    
    function settle(uint256 dealId) external {
        Deal storage d = deals[dealId];
        require(d.state == 0 || d.state == 1, "Wrong state");
        require(msg.sender == d.client || msg.sender == d.oracle, "Not party");
        d.state = 2;
        totalSettled += d.amount;
        if (agents[d.oracle].active) agents[d.oracle].dealsCompleted++;
        if (agents[d.client].active) agents[d.client].dealsCompleted++;
        payable(d.oracle).transfer(d.amount);
        emit DealSettled(dealId, d.amount);
    }
    
    function dispute(uint256 dealId) external {
        Deal storage d = deals[dealId];
        require((d.state == 0 || d.state == 1) && msg.sender == d.client, "Invalid");
        require(block.timestamp > d.createdAt + 24 hours, "Too early");
        d.state = 3;
        if (agents[d.oracle].active) agents[d.oracle].dealsDisputed++;
        payable(d.client).transfer(d.amount);
        emit DealDisputed(dealId);
    }
    
    function meshStatus() external view returns (
        uint256, bytes32, uint32, uint32, uint32, uint16, uint8, uint256, uint256, uint256, uint256
    ) {
        return (latestPulse.timestamp, latestPulse.meshHash, latestPulse.servers, latestPulse.tools,
            latestPulse.oraclesOnline, latestPulse.uptimeBps, latestPulse.chainAnchors,
            pulseCount, totalAgents, dealCount, totalSettled);
    }
}
