# Memex for Contracting Work

## The Opportunity

The IT staffing industry is a $123B+ market in the US. Companies like Insight
Global, Robert Half, and TEKsystems charge 50-60% markup on W-2 contractors
and ~30% on 1099. A contractor paid $75/hr gets billed to the client at
$112-120/hr. The staffing firm keeps $37-45/hr for what is essentially:

1. Searching for candidates (LinkedIn, job boards, internal database)
2. Screening resumes (phone calls, reference checks)
3. Presenting candidates to the client
4. Handling payroll and compliance paperwork

Steps 1-3 are information problems. Memex solves them directly — each
contractor's actual work history is searchable, verifiable, and queryable by
AI. Step 4 (payroll/compliance) is a solved problem with existing payroll
APIs.

**The thesis: replace a 30-50% take rate with 1% by doing everything in
software.**

## How It Works

### The Contractor Side

Each contractor runs Memex on their machine. Their screen captures, indexed
by OCR and embedded in ChromaDB, create a living portfolio of what they
actually work on. When they opt in to the contractor network, their Memex
becomes queryable by hiring companies.

```
Contractor publishes to network:
  memex contractor publish \
    --handle "@joenewbry" \
    --rate "$85/hr" \
    --availability "immediate" \
    --tags "kubernetes, golang, aws, terraform" \
    --history "2 years of Memex data"
```

The contractor's data stays on their machine. The network only stores
metadata (handle, rate, tags, availability, MCP endpoint).

### The Company Side

A hiring manager or procurement team connects to the Memex contractor
network via MCP. They describe what they need, and the system searches
across all opted-in contractors.

```
Company searches the network:
  memex hire search "senior golang engineer with kubernetes experience, \
    available immediately, budget $90/hr"

  → Found 12 matching contractors:
    @joenewbry  — $85/hr, immediate, 2yr history (similarity: 0.94)
    @janedoe    — $90/hr, 2 weeks, 18mo history (similarity: 0.91)
    @bobsmith   — $80/hr, immediate, 3yr history (similarity: 0.87)
    ...
```

## What Searches Look Like

### 1. Skill-Based Search

The most basic search. Find people who work with specific technologies.

```
Query: "Find contractors who have used Terraform to manage AWS EKS clusters"

What happens:
  1. Query embeds to a vector
  2. Registry checks each contractor's topic centroid for similarity
  3. Top matches get their MCPs queried directly
  4. Each contractor's Memex returns relevant screen captures + context

Results show:
  - Actual screenshots of them writing Terraform configs
  - Time spent in Terraform (hours per week, derived from capture frequency)
  - Which AWS services they interacted with
  - How recently they used it (last week vs 6 months ago)
```

### 2. Depth-of-Experience Search

Go beyond "have you used X" to "how deeply have you used X."

```
Query: "Find someone who has debugged Kubernetes networking issues,
        not just deployed pods"

What happens:
  - Memex searches for captures showing kubectl logs, network traces,
    CNI configs, pod debugging sessions
  - Distinguishes between someone who runs `kubectl apply` and someone
    who reads Calico network policies and traces packet flows

Results show:
  - Evidence of deep debugging (stack traces, log analysis)
  - Complexity of issues handled
  - Time spent in debugging vs routine deployment
```

### 3. Tool-Stack Search

Find contractors whose daily workflow matches your stack.

```
Query: "Who uses VS Code + Go + Docker + GitHub Actions daily?"

What happens:
  - Memex OCR captures show which applications are open
  - Frequency analysis: how often each tool appears in screenshots
  - Returns contractors whose daily tool usage matches the stack

Results show:
  - Percentage of work time spent in each tool
  - Tool usage patterns over weeks/months
  - Whether they're a power user (complex configs) or basic user
```

### 4. Work-Pattern Search

Find contractors whose work style fits your team.

```
Query: "Who works US Pacific hours and has consistent daily output?"

What happens:
  - Capture timestamps reveal active hours
  - Activity patterns show consistency (or gaps)
  - Can identify timezone, work schedule, productivity patterns

Results show:
  - Typical active hours (e.g., 9am-5pm PST)
  - Days per week active
  - Work consistency score
```

### 5. Project-Similarity Search

Find someone who's done work similar to your project.

```
Query: "Who has migrated a monolithic Java app to microservices on k8s?"

What happens:
  - Semantic search across contractor Memex nodes
  - Looks for evidence of: Java codebases, Docker containerization,
    Kubernetes deployment manifests, service mesh configs, API gateway setup
  - Temporal analysis: did these appear in sequence (suggesting a migration)?

Results show:
  - Evidence of migration work (before/after patterns)
  - Duration of the migration effort
  - Technologies used in the process
  - Complexity indicators
```

### 6. Collaboration-Fit Search

Find someone who communicates well with certain types of teams.

```
Query: "Who has worked closely with design teams on frontend projects?"

What happens:
  - Memex captures show Figma, Slack conversations with designers,
    design review meetings, CSS/component work
  - Cross-references with team topology data if available

Results show:
  - Evidence of design tool usage (Figma, Sketch)
  - Communication patterns with non-engineering roles
  - Frontend work that implements design specs
```

## Candidate Evaluation Templates

Templates are structured evaluation criteria that run automatically against
a contractor's Memex. They produce a score and evidence package.

### How Templates Work

```python
class EvaluationTemplate:
    name: str                    # "Senior Backend Engineer"
    queries: list[EvalQuery]     # Questions to ask each candidate's Memex
    thresholds: dict[str, float] # Minimum scores to pass
    weights: dict[str, float]    # How much each criterion matters

class EvalQuery:
    criterion: str               # "kubernetes_experience"
    query: str                   # The actual search query
    scoring: str                 # "frequency", "depth", "recency", "boolean"
    weight: float                # Relative importance (0-1)
```

### Template: Senior Kubernetes Engineer

```yaml
name: Senior Kubernetes Engineer
description: >
  Evaluates contractors for senior-level Kubernetes work.
  Expects deep operational experience, not just deployment.

queries:
  - criterion: kubernetes_depth
    query: >
      Show evidence of debugging Kubernetes issues at the cluster level:
      node problems, networking, storage, RBAC, or control plane issues.
      Not just deploying pods.
    scoring: depth
    weight: 0.30

  - criterion: infrastructure_as_code
    query: >
      Show Terraform, Pulumi, or CloudFormation usage for managing
      Kubernetes infrastructure (EKS, GKE, AKS clusters).
    scoring: frequency
    weight: 0.20

  - criterion: ci_cd_pipeline
    query: >
      Show CI/CD pipeline work that deploys to Kubernetes.
      GitHub Actions, Jenkins, ArgoCD, FluxCD, etc.
    scoring: depth
    weight: 0.15

  - criterion: monitoring_observability
    query: >
      Show usage of Prometheus, Grafana, Datadog, or similar tools
      for monitoring Kubernetes workloads.
    scoring: frequency
    weight: 0.15

  - criterion: recency
    query: >
      How recently was Kubernetes-related work captured?
      Within the last month, 3 months, or longer?
    scoring: recency
    weight: 0.10

  - criterion: golang_proficiency
    query: >
      Show Go/Golang development work. Writing services,
      CLIs, or operators. Not just reading Go code.
    scoring: depth
    weight: 0.10

thresholds:
  overall: 0.70            # Must score 70% or above overall
  kubernetes_depth: 0.60   # Must show real depth in k8s
  recency: 0.50            # Must have recent k8s work

output:
  - score_breakdown          # Score per criterion
  - evidence_package         # Screenshots + OCR excerpts as proof
  - time_in_domain           # Total hours estimated in k8s work
  - trajectory               # Getting deeper? Plateaued? Moving away?
```

### Template: Full-Stack React/Node Engineer

```yaml
name: Full-Stack React/Node Engineer
queries:
  - criterion: react_depth
    query: >
      Show React development: component architecture, state management
      (Redux, Zustand, Context), hooks, performance optimization.
    scoring: depth
    weight: 0.25

  - criterion: node_backend
    query: >
      Show Node.js/Express/NestJS backend work: API development,
      database queries, authentication, middleware.
    scoring: depth
    weight: 0.25

  - criterion: typescript
    query: >
      Is the codebase in TypeScript? Show type definitions, interfaces,
      generics usage. Not just .ts file extensions.
    scoring: frequency
    weight: 0.15

  - criterion: testing
    query: >
      Show testing work: Jest, React Testing Library, Cypress, Playwright.
      Writing tests, not just running them.
    scoring: frequency
    weight: 0.15

  - criterion: design_collaboration
    query: >
      Show evidence of working with design tools (Figma, Sketch) and
      implementing designs pixel-accurately.
    scoring: depth
    weight: 0.10

  - criterion: shipping
    query: >
      Show deployment and release work. Merging PRs, deploying to
      production, monitoring releases.
    scoring: frequency
    weight: 0.10

thresholds:
  overall: 0.65
  react_depth: 0.60
  node_backend: 0.50
```

### Running a Template

```bash
# Run a template against the contractor network
memex hire evaluate \
  --template "senior-kubernetes-engineer" \
  --budget "$90/hr" \
  --availability "within 2 weeks" \
  --min-history "6 months"

# Output:
# ┌─────────────────────────────────────────────────────────────┐
# │ Evaluation: Senior Kubernetes Engineer                      │
# │ Budget: ≤$90/hr | Available: ≤2 weeks | Min history: 6mo   │
# ├─────────────┬───────┬────────┬──────────┬──────────────────┤
# │ Contractor  │ Score │ Rate   │ Avail    │ Top Strengths    │
# ├─────────────┼───────┼────────┼──────────┼──────────────────┤
# │ @joenewbry  │ 0.91  │ $85/hr │ Now      │ k8s debug, IaC  │
# │ @janedoe    │ 0.84  │ $90/hr │ 1 week   │ CI/CD, monitoring│
# │ @bobsmith   │ 0.78  │ $80/hr │ Now      │ k8s, golang      │
# │ @alicew     │ 0.71  │ $88/hr │ 2 weeks  │ k8s, terraform   │
# │ @charlie    │ 0.65  │ $75/hr │ Now      │ k8s basic, Go    │
# │ ─── below threshold ──────────────────────────────────────│
# │ @dave       │ 0.58  │ $70/hr │ Now      │ k8s deploy only  │
# └─────────────┴───────┴────────┴──────────┴──────────────────┘
#
# View full evidence: memex hire evidence @joenewbry --template senior-kubernetes-engineer
```

### Custom Templates

Companies can write their own templates for their specific needs:

```bash
# Create a custom template
memex hire template create "our-backend-role" \
  --from "senior-kubernetes-engineer" \
  --add-criterion "aws_experience:0.20" \
  --add-query "Show AWS console usage, CloudWatch, IAM policy editing" \
  --adjust-weight "golang_proficiency:0.25" \
  --threshold "overall:0.75"
```

## The Economics

### Current Staffing Industry Model

```
Client pays:         $120/hr
Contractor receives: $75/hr
Staffing firm keeps:  $45/hr (37.5% of billing)

For a 6-month contract (1,000 hours):
  Client total cost:       $120,000
  Contractor receives:      $75,000
  Staffing firm revenue:    $45,000
```

The staffing firm's $45,000 covers:
- Recruiter salary + commission (~$15,000)
- Payroll processing, insurance, compliance (~$10,000)
- Sales/account management (~$8,000)
- Office overhead, tools, job board subscriptions (~$7,000)
- Profit (~$5,000)

### Memex Model: 1% Take Rate

```
Client pays:         $76.50/hr (contractor rate + 1% + compliance fee)
Contractor receives: $75/hr
Memex network keeps:  $0.75/hr (1% of contractor rate)
Compliance layer:     $0.75/hr (payroll, insurance, legal — outsourced)

For a 6-month contract (1,000 hours):
  Client total cost:       $76,500
  Contractor receives:      $75,000
  Memex network revenue:      $750
  Compliance costs:           $750
```

**The client saves $43,500 on a single 6-month contract.**

### Where the 1% Goes

```
Revenue per placement: $750 (for a 1,000-hour contract)

Costs:
  - MCP query infrastructure:    ~$5   (server costs for search)
  - Template evaluation compute: ~$10  (AI inference for scoring)
  - Payment processing:          ~$20  (Stripe fees)
  - Network operations:          ~$15  (registry, monitoring)

Profit per placement:            ~$700

At scale (1,000 active contracts):
  Monthly revenue:    $75,000
  Monthly costs:      ~$5,000
  Monthly profit:     ~$70,000
```

The economics work because the marginal cost of an AI-powered search is
near zero. A recruiter costs $60-80K/year and handles 15-25 placements.
Memex handles unlimited searches at compute cost.

### Why Not 0%?

Zero take rate isn't sustainable. The 1% covers:
- Running the contractor registry
- Template development and maintenance
- Dispute resolution (when evaluations are contested)
- Compliance tooling partnerships
- Network security and abuse prevention

### The Search Fee Model

Companies pay to search the network. Contractors are found for free (they
benefit from being discovered).

```
Search Pricing:

Free tier:
  - Browse contractor profiles (metadata only)
  - See tags, rate, availability, history depth
  - 5 deep searches per month (queries that hit actual MCPs)

Pro tier ($99/month):
  - Unlimited deep searches
  - Run evaluation templates
  - Save and compare candidates
  - Priority query routing (your searches run first)

Enterprise tier ($499/month):
  - Everything in Pro
  - Custom evaluation templates
  - API access for ATS integration
  - Dedicated support
  - Bulk search (evaluate 50+ candidates at once)
  - Compliance documentation package
```

### Revenue Mix

```
Revenue sources at scale (1,000 active contracts, 500 searching companies):

1. Take rate (1% of contractor billing):
   Average contract: $75/hr × 160 hrs/mo = $12,000/mo billed
   1% = $120/mo per active contract
   1,000 contracts = $120,000/mo

2. Search subscriptions:
   Free: 300 companies × $0 = $0
   Pro: 150 companies × $99 = $14,850/mo
   Enterprise: 50 companies × $499 = $24,950/mo
   Total search revenue: $39,800/mo

3. Total monthly revenue: ~$160,000
4. Total annual revenue: ~$1.9M

Comparison:
  Insight Global annual revenue: ~$4.4B
  Their margin on same 1,000 contracts: ~$45M/year
  Memex network on same 1,000 contracts: ~$1.9M/year

  Client savings: ~$43M/year across those 1,000 contracts
```

The value proposition isn't Memex's revenue — it's the $43M clients don't
pay to staffing firms.

## What Makes This Different from Upwork/Toptal

| Feature | Upwork | Toptal | Insight Global | Memex Network |
|---------|--------|--------|----------------|---------------|
| Take rate | 10-20% | ~30-50% (hidden) | 30-50% | 1% |
| Candidate data | Self-reported profile | Curated interview | Resume + recruiter notes | Verified screen history |
| Evaluation | Client interviews | Toptal screening | Recruiter judgment | AI templates + evidence |
| Search method | Keyword + filters | Toptal matches you | Recruiter searches | Semantic vector search |
| Proof of work | Portfolio links | Past projects | References | Actual screenshots of work |
| Data ownership | Upwork owns it | Toptal owns it | Staffing firm owns it | Contractor owns it |
| Ongoing verification | None | None | None | Continuous (daily captures) |
| Fake detection | Reviews, but gameable | Interview process | Recruiter gut feel | Temporal + depth analysis |

### The Key Differentiator: Verified Work History

Traditional platforms rely on claims. Memex relies on captures.

```
Traditional:
  Resume says: "5 years Kubernetes experience"
  Reality: Used kubectl twice in 2021

Memex:
  Captures show: 847 screenshots of Kubernetes work over 14 months
  Activity: kubectl, Helm charts, Terraform EKS modules, Datadog k8s dashboards
  Depth: Debugging CNI issues, writing custom operators, managing cluster upgrades
  Recency: Last k8s-related capture: 3 hours ago
```

You can't fake 847 screenshots of Kubernetes work spanning 14 months.

## Compliance Layer

The 1% take rate doesn't include compliance costs. For W-2 placements,
there's payroll tax, workers' comp, benefits, and employment paperwork.
This is outsourced to an Employer of Record (EOR).

```
Compliance options:

1099 (Independent Contractor):
  - Memex handles: nothing (contractor bills client directly)
  - Memex take rate: 1%
  - Client responsibility: verify classification, issue 1099
  - Total client cost: contractor rate + 1%

W-2 (via EOR partner):
  - EOR handles: payroll, tax withholding, workers' comp, benefits
  - EOR fee: typically 15-25% of payroll (standard industry rate)
  - Memex take rate: 1% (on top of EOR fee)
  - Total client cost: contractor rate + EOR fee + 1%
  - Still cheaper than staffing firms (EOR + 1% < staffing firm markup)

Corp-to-Corp (C2C):
  - Contractor has their own LLC/Corp
  - Memex handles: nothing beyond the match
  - Memex take rate: 1%
  - Total client cost: contractor rate + 1%
```

For 1099 and C2C, the total cost is contractor rate + 1%. For W-2, the EOR
adds 15-25%, but that's the same overhead a staffing firm has — the
difference is they're not also charging 30% on top for the search.

## Trust and Anti-Gaming

### How Do Companies Trust Memex Data?

1. **Volume of evidence** — a real work history has thousands of captures.
   Faking this at scale is harder than doing the actual work.

2. **Temporal consistency** — real work has natural patterns: 9-5 activity,
   lunch breaks, context switches between tools, weekend gaps. AI can detect
   synthetic patterns.

3. **Depth queries** — a company can ask follow-up questions. Faked data
   breaks under scrutiny because the underlying captures don't support it.

4. **Cross-reference** — if a contractor claims they worked at Company X,
   their Memex should show Company X's tools, Slack, email, codebase. This
   is verifiable without Company X's cooperation.

5. **Evaluation templates** — standardized scoring makes it hard to game
   specific criteria. You'd need to fake depth in multiple categories
   simultaneously.

### What About Privacy?

Contractors control what's queryable:

```
memex contractor config \
  --allow "technology queries, project type queries, skill depth queries" \
  --block "salary info, personal messages, company confidential data" \
  --redact "API keys, passwords, internal URLs, Slack DMs" \
  --guard-model "qwen3guard:0.6b"
```

The guard model on each contractor's machine filters every query and
response. Companies see evidence of work, not private information.

## Implementation Path

### Phase 1: Contractor Registry

```
- Contractors opt in to the network
- Registry stores: handle, rate, availability, tags, MCP endpoint
- Companies can browse and do basic searches
- Direct MCP queries to individual contractors
- Take rate: 0% (free to build network effects)
```

### Phase 2: Evaluation Templates

```
- Standard templates for common roles
- Companies run templates against candidates
- Scoring and evidence packages
- Search subscription pricing begins
- Take rate: still 0% (building trust)
```

### Phase 3: Monetization

```
- 1% take rate on placements made through the network
- Search subscriptions (Free / Pro / Enterprise)
- Custom template marketplace
- ATS integrations (Greenhouse, Lever, Workday)
```

### Phase 4: Compliance Integration

```
- EOR partnerships for W-2 placements
- Automated 1099 generation
- Background check integration
- SOC 2 certification for enterprise clients
```

### Phase 5: Network Effects

```
- Contractor ratings and reviews
- Repeat-hire tracking (companies rehiring same contractors)
- Team-based contractor search (find 3 people who've worked together)
- Predictive availability (contractor's current engagement ends in ~2 weeks)
```

## The Pitch

**To contractors:**
"Keep 99% of what you earn. Your work history is your resume — verifiable,
searchable, and under your control. No more recruiter calls asking you to
update your LinkedIn."

**To companies:**
"Find contractors based on what they've actually done, not what they claim.
Pay $76.50/hr instead of $120/hr for the same person. Run evaluation
templates that give you evidence, not resumes."

**The math:**
A company hiring 10 contractors at $75/hr through Insight Global pays
~$1.2M/yr. Through Memex, they pay ~$765K/yr. That's $435K saved per year,
and the candidates are better vetted because the evaluation is based on
verified work, not recruiter judgment.
