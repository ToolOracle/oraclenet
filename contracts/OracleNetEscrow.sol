// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title OracleNetEscrow
 * @notice Autonomous escrow for AI agent commerce on Base.
 *         Agents negotiate deals, lock USDC, receive deliverables, settle automatically.
 * @dev Part of OracleNet — the compliance-first AI agent mesh.
 *      https://tooloracle.io | did:web:feedoracle.io
 */
contract OracleNetEscrow is ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ══════════════════════════════════════════════════════════
    // Types
    // ══════════════════════════════════════════════════════════

    enum DealState {
        Created,        // Client locked funds
        Delivered,      // Oracle submitted proof of delivery
        Settled,        // Funds released to oracle
        Refunded,       // Funds returned to client
        Disputed        // Under arbitration
    }

    struct Deal {
        address client;            // Paying agent's wallet
        address oracle;            // Oracle provider's wallet
        address token;             // Payment token (USDC)
        uint256 amount;            // Escrowed amount
        bytes32 deliverableHash;   // Expected SHA-256 hash of deliverables
        bytes32 proofHash;         // Actual proof submitted by oracle
        uint256 createdAt;         // Block timestamp
        uint256 deadline;          // Auto-refund after this timestamp
        DealState state;           // Current state
        string  dealType;          // "audit", "report", "screening", "workflow"
        string  itpId;             // Intelligence Transfer Package ID
    }

    // ══════════════════════════════════════════════════════════
    // State
    // ══════════════════════════════════════════════════════════

    address public immutable owner;        // FeedOracle Technologies
    address public arbiter;                // AgentGuard (dispute resolver)
    uint256 public dealCount;
    uint256 public platformFeeBps;         // Basis points (100 = 1%)
    uint256 public totalVolume;
    uint256 public totalDeals;
    uint256 public totalSettled;

    mapping(uint256 => Deal) public deals;
    mapping(address => uint256[]) public clientDeals;
    mapping(address => uint256[]) public oracleDeals;

    // Oracle reputation: wallet → (completed, disputed, refunded)
    mapping(address => uint256) public oracleCompleted;
    mapping(address => uint256) public oracleDisputed;
    mapping(address => uint256) public oracleRefunded;

    // ══════════════════════════════════════════════════════════
    // Events
    // ══════════════════════════════════════════════════════════

    event DealCreated(
        uint256 indexed dealId,
        address indexed client,
        address indexed oracle,
        uint256 amount,
        bytes32 deliverableHash,
        uint256 deadline,
        string dealType
    );
    event DealDelivered(uint256 indexed dealId, bytes32 proofHash, string itpId);
    event DealSettled(uint256 indexed dealId, uint256 oracleAmount, uint256 feeAmount);
    event DealRefunded(uint256 indexed dealId, uint256 amount);
    event DealDisputed(uint256 indexed dealId, address disputedBy);
    event DisputeResolved(uint256 indexed dealId, DealState resolution);

    // ══════════════════════════════════════════════════════════
    // Constructor
    // ══════════════════════════════════════════════════════════

    constructor(address _arbiter, uint256 _feeBps) {
        require(_feeBps <= 500, "Fee too high"); // Max 5%
        owner = msg.sender;
        arbiter = _arbiter;
        platformFeeBps = _feeBps;
    }

    // ══════════════════════════════════════════════════════════
    // Core: Create Deal (Client locks funds)
    // ══════════════════════════════════════════════════════════

    /**
     * @notice Client creates a deal and locks USDC in escrow.
     * @param _oracle Oracle provider wallet
     * @param _token Payment token (USDC address)
     * @param _amount Amount to lock
     * @param _deliverableHash Expected SHA-256 of deliverables
     * @param _deadline Auto-refund timestamp (e.g. block.timestamp + 1 hour)
     * @param _dealType Type of deal ("audit", "report", etc.)
     */
    function createDeal(
        address _oracle,
        address _token,
        uint256 _amount,
        bytes32 _deliverableHash,
        uint256 _deadline,
        string calldata _dealType
    ) external nonReentrant returns (uint256 dealId) {
        require(_oracle != address(0), "Invalid oracle");
        require(_amount > 0, "Amount must be > 0");
        require(_deadline > block.timestamp, "Deadline must be future");
        require(_deadline <= block.timestamp + 7 days, "Deadline max 7 days");

        // Transfer USDC from client to this contract
        IERC20(_token).safeTransferFrom(msg.sender, address(this), _amount);

        dealId = dealCount++;
        deals[dealId] = Deal({
            client: msg.sender,
            oracle: _oracle,
            token: _token,
            amount: _amount,
            deliverableHash: _deliverableHash,
            proofHash: bytes32(0),
            createdAt: block.timestamp,
            deadline: _deadline,
            state: DealState.Created,
            dealType: _dealType,
            itpId: ""
        });

        clientDeals[msg.sender].push(dealId);
        oracleDeals[_oracle].push(dealId);
        totalVolume += _amount;
        totalDeals++;

        emit DealCreated(dealId, msg.sender, _oracle, _amount, _deliverableHash, _deadline, _dealType);
    }

    // ══════════════════════════════════════════════════════════
    // Core: Deliver (Oracle submits proof)
    // ══════════════════════════════════════════════════════════

    /**
     * @notice Oracle submits proof of delivery.
     * @param _dealId Deal ID
     * @param _proofHash SHA-256 hash of the actual deliverables (ITP content_hash)
     * @param _itpId Intelligence Transfer Package ID
     */
    function deliver(
        uint256 _dealId,
        bytes32 _proofHash,
        string calldata _itpId
    ) external {
        Deal storage d = deals[_dealId];
        require(msg.sender == d.oracle, "Only oracle");
        require(d.state == DealState.Created, "Wrong state");
        require(block.timestamp <= d.deadline, "Deadline passed");

        d.proofHash = _proofHash;
        d.itpId = _itpId;
        d.state = DealState.Delivered;

        emit DealDelivered(_dealId, _proofHash, _itpId);
    }

    // ══════════════════════════════════════════════════════════
    // Core: Settle (Client confirms, funds release)
    // ══════════════════════════════════════════════════════════

    /**
     * @notice Client confirms delivery. Funds released to oracle minus fee.
     *         OR: Auto-settle if proofHash matches deliverableHash.
     */
    function settle(uint256 _dealId) external nonReentrant {
        Deal storage d = deals[_dealId];
        require(d.state == DealState.Delivered, "Not delivered");
        require(
            msg.sender == d.client || 
            msg.sender == d.oracle ||
            msg.sender == arbiter,
            "Not authorized"
        );

        // Client and arbiter can always settle (client confirms delivery)
        // Oracle can only self-settle if proof hash matches deliverable hash
        if (msg.sender != d.client && msg.sender != arbiter) {
            // Must be oracle — require hash match for auto-settlement
            require(d.proofHash == d.deliverableHash, "Hash mismatch - client must confirm");
        }

        _settle(_dealId);
    }

    function _settle(uint256 _dealId) internal {
        Deal storage d = deals[_dealId];
        d.state = DealState.Settled;

        uint256 fee = (d.amount * platformFeeBps) / 10000;
        uint256 oracleAmount = d.amount - fee;

        IERC20(d.token).safeTransfer(d.oracle, oracleAmount);
        if (fee > 0) {
            IERC20(d.token).safeTransfer(owner, fee);
        }

        oracleCompleted[d.oracle]++;
        totalSettled++;

        emit DealSettled(_dealId, oracleAmount, fee);
    }

    // ══════════════════════════════════════════════════════════
    // Core: Refund (Timeout or client cancels before delivery)
    // ══════════════════════════════════════════════════════════

    /**
     * @notice Refund if deadline passed without delivery, or client cancels.
     */
    function refund(uint256 _dealId) external nonReentrant {
        Deal storage d = deals[_dealId];
        require(d.state == DealState.Created, "Not refundable");
        require(
            block.timestamp > d.deadline || msg.sender == d.client,
            "Deadline not passed"
        );

        d.state = DealState.Refunded;
        IERC20(d.token).safeTransfer(d.client, d.amount);
        oracleRefunded[d.oracle]++;

        emit DealRefunded(_dealId, d.amount);
    }

    // ══════════════════════════════════════════════════════════
    // Disputes (AgentGuard as arbiter)
    // ══════════════════════════════════════════════════════════

    function dispute(uint256 _dealId) external {
        Deal storage d = deals[_dealId];
        require(
            d.state == DealState.Created || d.state == DealState.Delivered,
            "Cannot dispute"
        );
        require(msg.sender == d.client || msg.sender == d.oracle, "Not party");

        d.state = DealState.Disputed;
        oracleDisputed[d.oracle]++;

        emit DealDisputed(_dealId, msg.sender);
    }

    /**
     * @notice Arbiter (AgentGuard) resolves dispute.
     * @param _favorClient True = refund client, False = pay oracle
     */
    function resolveDispute(uint256 _dealId, bool _favorClient) external nonReentrant {
        require(msg.sender == arbiter, "Only arbiter");
        Deal storage d = deals[_dealId];
        require(d.state == DealState.Disputed, "Not disputed");

        if (_favorClient) {
            d.state = DealState.Refunded;
            IERC20(d.token).safeTransfer(d.client, d.amount);
            emit DisputeResolved(_dealId, DealState.Refunded);
        } else {
            _settle(_dealId);
            emit DisputeResolved(_dealId, DealState.Settled);
        }
    }

    // ══════════════════════════════════════════════════════════
    // Views (for DealOracle 2.0 to read on-chain)
    // ══════════════════════════════════════════════════════════

    function getDeal(uint256 _dealId) external view returns (Deal memory) {
        return deals[_dealId];
    }

    function getClientDeals(address _client) external view returns (uint256[] memory) {
        return clientDeals[_client];
    }

    function getOracleDeals(address _oracle) external view returns (uint256[] memory) {
        return oracleDeals[_oracle];
    }

    function getOracleReputation(address _oracle) external view returns (
        uint256 completed, uint256 disputed, uint256 refunded, uint256 successRate
    ) {
        completed = oracleCompleted[_oracle];
        disputed = oracleDisputed[_oracle];
        refunded = oracleRefunded[_oracle];
        uint256 total = completed + disputed + refunded;
        successRate = total > 0 ? (completed * 10000) / total : 0; // Basis points
    }

    function platformStats() external view returns (
        uint256 _totalDeals, uint256 _totalSettled, uint256 _totalVolume, uint256 _feeBps
    ) {
        return (totalDeals, totalSettled, totalVolume, platformFeeBps);
    }

    // ══════════════════════════════════════════════════════════
    // Admin
    // ══════════════════════════════════════════════════════════

    function setArbiter(address _newArbiter) external {
        require(msg.sender == owner, "Only owner");
        arbiter = _newArbiter;
    }

    function setFee(uint256 _newFeeBps) external {
        require(msg.sender == owner, "Only owner");
        require(_newFeeBps <= 500, "Fee too high");
        platformFeeBps = _newFeeBps;
    }
}
