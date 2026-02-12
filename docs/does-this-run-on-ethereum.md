# Does This Run on Ethereum?

## The Question

Memex is a decentralized system where each person owns their data and exposes
it via MCP. When we add teams and orgs — people querying each other's Memex
nodes — we introduce new problems:

- **Who accessed whose data?** (audit trail that nobody can tamper with)
- **Can we charge micro-fees for access?** (economics of the network)
- **How do we verify identity across nodes?** (trust without a central authority)
- **Can the org chart be trustless?** (derived from real activity, not HR's spreadsheet)

Ethereum and blockchain-like protocols are designed for exactly these problems.
But at what cost?

## Cost Analysis: Ethereum Mainnet

The hard constraint: **total cost must be less than $0.01/day per person.**

### Ethereum L1 (Mainnet)

| Operation | Gas Cost | At 30 gwei, ETH=$2,500 | Notes |
|-----------|----------|------------------------|-------|
| Simple transfer | 21,000 gas | ~$1.58 | Just sending ETH |
| Store 32 bytes | ~20,000 gas | ~$1.50 | SSTORE (new slot) |
| Contract call (simple) | ~50,000 gas | ~$3.75 | Minimal logic |
| Contract call (medium) | ~200,000 gas | ~$15.00 | Write + emit event |
| Deploy contract | ~1,000,000+ gas | ~$75+ | One-time |

**Verdict: Ethereum L1 is 100-1000x too expensive.** A single state write costs
more than the entire daily budget. You can't even log "Person A queried Person B"
for a penny.

### Ethereum L2s (Rollups)

L2s batch transactions and post proofs to L1. Costs are 10-100x cheaper.

| L2 Network | Simple Transfer | Contract Call | Notes |
|------------|----------------|---------------|-------|
| Arbitrum | ~$0.01-0.10 | ~$0.05-0.50 | Most popular, Optimistic Rollup |
| Optimism (OP Stack) | ~$0.01-0.10 | ~$0.05-0.50 | Coinbase's Base uses this |
| Base | ~$0.001-0.01 | ~$0.01-0.10 | Cheapest mainstream L2 |
| zkSync Era | ~$0.01-0.05 | ~$0.05-0.30 | ZK Rollup, faster finality |
| Polygon zkEVM | ~$0.01-0.05 | ~$0.02-0.20 | Polygon's ZK solution |

**Base is the closest to our budget.** A simple contract call on Base costs
~$0.01-0.10. If we batch operations and keep them minimal, we might hit the
penny-per-day target — but only barely, and only for low-frequency operations.

### L3s and App-Specific Chains

| Option | Cost per Tx | Setup Cost | Notes |
|--------|-------------|------------|-------|
| Arbitrum Orbit (L3) | ~$0.001 | Moderate | Your own L3 settling to Arbitrum |
| OP Stack chain | ~$0.001 | Moderate | Your own L2/L3 |
| Polygon CDK | ~$0.001 | Moderate | App-specific ZK chain |

**An app-specific L3 gets us to sub-penny transactions.** But you're now running
blockchain infrastructure, which is its own complexity.

## Alternatives to Ethereum

### Option 1: Solana

| Metric | Value |
|--------|-------|
| Transaction cost | ~$0.00025 |
| Throughput | ~4,000 TPS |
| Finality | ~400ms |
| Smart contracts | Rust (Anchor framework) |

**Solana is cheap enough.** At $0.00025 per transaction, a person could log 40
queries per day and stay under $0.01. The downside: Solana's ecosystem is more
DeFi/NFT-oriented, and the developer experience for non-financial use cases is
rougher.

### Option 2: NEAR Protocol

| Metric | Value |
|--------|-------|
| Transaction cost | ~$0.001 |
| Storage cost | 1 NEAR per 100KB (~$3) |
| Smart contracts | Rust or JavaScript |
| Finality | ~1-2s |

**NEAR is interesting because of its account model.** Named accounts
(`joenewbry.near`) map naturally to Memex handles. Storage staking means you
pay once to reserve space, not per-write. But the storage cost model doesn't
fit — we don't want to store data on-chain, just log access events.

### Option 3: Ceramic Network (Not a Blockchain)

| Metric | Value |
|--------|-------|
| Write cost | Free (you run your own node) |
| Data model | Streams (append-only documents) |
| Identity | DID-based (decentralized identifiers) |
| Storage | IPFS + your node |

**Ceramic is purpose-built for decentralized data.** It's not a blockchain — it's
a decentralized data network. Each person has streams (like Memex entries) tied
to their DID. Other people can read streams if permissioned. No gas fees because
there's no global consensus — just local nodes that sync.

**This is the closest fit to what Memex actually needs.**

### Option 4: Lens Protocol / Farcaster

Social protocols built on Ethereum L2s. Designed for decentralized social graphs.
Could model org relationships and team structures as social connections.

- **Lens:** On Polygon, uses NFTs for profiles. Over-engineered for our use case.
- **Farcaster:** Hybrid (on-chain identity + off-chain data). Interesting model
  but tightly coupled to its social feed UX.

### Option 5: Just Sign Things (No Blockchain)

Use cryptographic signatures without a blockchain:

```
Each person has a keypair.
When Person A queries Person B's Memex:
  1. A signs the query with their private key
  2. B verifies A's signature
  3. B signs the response
  4. Both parties have a signed, timestamped, tamper-proof record
```

**Cost: $0.00.** Signing is a local CPU operation.

No blockchain needed. You get:
- Tamper-proof audit trails (both parties have signed receipts)
- Identity verification (public key = identity)
- Non-repudiation (A can't deny they made a query)

You don't get:
- Global ordering (no consensus on what happened first)
- Public verifiability (only A and B have the receipts)
- Smart contract logic (no programmable rules)

## What Would We Actually Put On-Chain?

If we do use a blockchain, we should put as little as possible on it:

### On-Chain (Expensive, Immutable)
- **Org registry:** Org ID, name, admin public key
- **Team registry:** Team ID, org ID, member public keys
- **Access events:** Hash of (querier + target + timestamp) — not the actual query
- **Micropayment channels:** Payment state for query fees
- **Reputation scores:** Aggregated, not raw data

### Off-Chain (Free, Mutable)
- **Actual Memex data** (stays on each person's machine)
- **Query content** (stays between querier and target)
- **Full audit logs** (stored locally, signed by both parties)
- **Vector embeddings** (in each person's ChromaDB)
- **Org chart visualizations** (computed from on-chain events)

## The Micro-Fee Model

> "If somebody hits my MCP, they have to pay a little fee just to see what's there."

### How It Would Work

```
Person A wants to query Person B's Memex:

1. A sends a signed query + micropayment (e.g., 0.001 USDC)
2. B's Memex processes the query
3. B returns results + signed receipt
4. Payment settles (could be batched via payment channel)
```

### Payment Channel Approach (Best for Micro-Fees)

Instead of one on-chain transaction per query, use a payment channel:

```
1. A opens a channel with B: deposits 1 USDC on-chain (one tx)
2. A queries B 100 times: each query deducts 0.001 USDC off-chain
3. When done, close the channel: final balance settles on-chain (one tx)

Total on-chain cost: 2 transactions for 100 queries
Per-query cost: ~$0.00002 (on Base L2)
```

This is similar to Bitcoin's Lightning Network or Ethereum's state channels.

### The Free-First Problem

> "I think the downside is this makes sharing worse, so I'd like it if it's free initially."

**Recommendation: Free tier with optional paid tier.**

```
Tier 1 (Free):
  - Query any Memex in your org: free
  - Intra-team queries: always free
  - First 10 queries/day to external nodes: free

Tier 2 (Paid):
  - Unlimited cross-org queries: micropayment per query
  - Priority response (skip the queue)
  - Access to historical data beyond 30 days

The node owner sets their policy:
  memex config --external-query-fee 0.001  # USDC per query
  memex config --org-query-fee 0           # free for org members
  memex config --team-query-fee 0          # free for team members
```

## Cost Summary

| Approach | Per-Query Cost | Daily Cost (20 queries) | Infrastructure |
|----------|---------------|------------------------|----------------|
| Ethereum L1 | $3-15 | $60-300 | None |
| Base L2 | $0.01-0.10 | $0.20-2.00 | None |
| Solana | $0.00025 | $0.005 | None |
| App-specific L3 | ~$0.001 | $0.02 | Must run chain |
| Ceramic | $0 | $0 | Must run node |
| Signed receipts (no chain) | $0 | $0 | None |
| Payment channels (Base) | ~$0.00002/query | $0.0004 | Open/close channel |

## Recommendation

### Start: Signed Receipts (No Blockchain)

For the team/org use case, **don't start with a blockchain.** Use cryptographic
signatures for identity and audit trails. This gives you:

- Zero cost
- Instant finality
- Works offline
- No infrastructure beyond what Memex already has

Each person generates a keypair on first run. Their public key is their identity
in the org. Queries are signed. Responses are signed. Both parties keep receipts.

### Later: Payment Channels on Base (If Micro-Fees Are Wanted)

If the network grows and micro-fees make sense, add payment channels on Base L2.
The per-query cost would be effectively zero ($0.00002), and the UX is simple:
deposit some USDC, query freely, settle when done.

### Maybe Never: Full On-Chain

Unless there's a specific reason to need global consensus (e.g., a public
reputation system where scores must be verifiable by anyone), there's no reason
to put Memex operations on a blockchain. The data is private. The interactions
are bilateral. Signatures give you everything you need.

### The Exception: On-Chain Org Registry

One thing that *does* make sense on-chain: **the org registry.** If orgs and
teams are publicly verifiable ("yes, this person is a member of Org X"), then
putting the org membership list on-chain (or a Merkle root of it) provides
trustless verification without revealing individual data.

```
On-chain: merkle_root(team_members) per team
Off-chain: actual member list, managed by org admin
Verification: "Prove you're in Team Engineering" → provide Merkle proof
Cost: One on-chain update per team change (~$0.01 on Base)
```

This is cheap (team membership changes infrequently) and useful (anyone can
verify membership without trusting a central server).
