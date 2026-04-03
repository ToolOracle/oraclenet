# OracleNet Protocol Specification v1.0.0

## Overview

OracleNet is a 9-layer protocol stack for autonomous AI agent commerce in regulated industries.

## Layers

### 1. Identity — W3C DID (did:web)
Each oracle has a decentralized identifier resolvable via `/.well-known/did.json`.

### 2. Discovery — ANP Agent Description Protocol
JSON-LD documents at `/.well-known/agent-descriptions` describe agent capabilities using schema.org vocabulary.

### 3. Communication — A2A v0.3
Agent Cards at `/.well-known/agent.json` enable Google A2A protocol task delegation.

### 4. Tool Access — MCP
Standard Model Context Protocol for tool discovery and execution.

### 5. Trust — W3C Verifiable Credentials
Each online oracle has a short-lived VC issued by AgentGuard. Grade A-F based on trust assessment.

### 6. Status — OracleNet Beacon
Real-time status broadcast at `/beacon/index.json`, regenerated every 5 minutes.

### 7. Provenance — Intelligence Transfer Protocol (ITP)
When oracles exchange data, full provenance travels with it: WHO produced it, HOW (confidence), WHEN, WHAT evidence backs it, WHY it matters (regulatory context). Based on W3C PROV-O.

### 8. Payment — x402 USDC
Pay-per-call micropayments via the x402 standard on Base.

### 9. Escrow — Smart Contract
Complex multi-tool workflows use on-chain USDC escrow with auto-settlement on Base.

## Namespace

OracleNet types are defined at `https://tooloracle.io/ns/oraclenet/`
