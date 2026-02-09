# What If You Never Had to Write a Resume Again?

## The idea: replace resumes with searchable proof of what you've actually done

Here's a question that has bothered me for a while: why do we still use resumes?

A resume is a document where you make claims about yourself. You say you "led a
team of 8 engineers" or "improved API performance by 40%." The hiring manager
reads it and has no way to verify any of it. They call your references — people
you hand-picked — who say nice things. Then they put you through a coding
interview that tests whether you can invert a binary tree on a whiteboard, which
has approximately zero correlation with your actual job.

The whole system is built on trust in a document that everyone knows is
embellished.

What if instead, a recruiter could just search your actual work?

## How it would work

You run a piece of software on your computer. It takes a screenshot every 60
seconds, extracts the text via OCR, and indexes everything locally in a vector
database. All of this stays on your machine. Nothing is uploaded anywhere.

When you're job hunting, you flip a switch. Your machine becomes searchable. A
recruiter can ask "show me this person's Kubernetes work from the last 6 months"
and get back real, timestamped results showing that yes, you were actually
debugging Helm charts at 2 AM and writing custom operators and reviewing pull
requests on a service mesh migration.

Not claims. Evidence.

A lightweight AI model running on your laptop checks every query before it
reaches your data (is this request malicious?) and every response before it
leaves your machine (does this contain passwords, API keys, or personal
information?). You see a log of every query anyone makes. You control the
whole thing.

## This has been tried before. Sort of.

Every piece of this concept has been attempted individually. None of them
combined it in quite this way. Understanding why each attempt succeeded or
failed is instructive.

### The capture layer works

**Rewind.ai** proved that 24/7 screen recording with local OCR and natural
language search is technically viable. Founded in 2022 by the Optimizely
co-founder, backed by a16z, it recorded your entire screen, compressed it
3,750x, and made it searchable. It worked. Users liked it.

Then it pivoted. The company rebranded to Limitless, launched a $99 physical
pendant for recording conversations, and was acquired by Meta in December 2025.
The desktop recording app was shut down. The reason for the pivot? Running local
AI models on users' machines was computationally expensive, and the market
pulled them toward meetings and conversations — a clearer, more immediate ROI
than "search your entire screen history."

**Microsoft Recall** tried to bake the same concept into Windows itself.
Announced in May 2024, it takes screenshots every few seconds, OCRs them, and
lets you search with natural language. The initial backlash was enormous. A
security researcher found that the first version stored everything in a
plaintext SQLite database with no encryption. Someone built a tool called
"TotalRecall" that could extract all captured data from any machine running it.
Microsoft delayed the launch by nearly a year, added encryption and biometric
auth, and finally shipped an opt-in version in 2025.

**Screenpipe** is the open-source version. It records your screen and
microphone, extracts text, and makes everything searchable with AI. It's
actively developed and growing. It proves the entire capture-and-index pipeline
can be built with open source tools.

The technology is not the problem.

### Proof-of-work hiring is wanted but hasn't been cracked

**GitHub profiles** are the closest thing we have to verified professional
evidence. Recruiters check contribution graphs before they read resumes. You can
see real code, real pull requests, real collaboration. But GitHub only captures
open-source work. Most professional work lives in private repos. It biases
toward people with leisure time for side projects.

**Stack Overflow** tried to turn reputation into a hiring signal with Jobs and
Developer Story. They had the largest developer community on earth and built-in
quality metrics — answer scores, badges, tag expertise. They shut it all down
in 2022. "The effort it would take us to truly differentiate in this space is
not one we could justify."

**Triplebyte** assessed engineers through standardized technical tests instead
of relying on resume credentials. They used ML trained on 200K+ interviews.
YC-backed, raised $48M. Acquired by Karat in 2023 in what looked like a fire
sale. What killed them? They pivoted away from their niche (unlocking
opportunity for non-credentialed engineers) to compete with LinkedIn. They also
launched public profiles that were default-public with opt-out, destroying trust
with their engineering community.

The pattern: proof-of-work hiring is desired — 87% of hiring managers say they
prefer portfolios to resumes — but nobody has built the right system yet. GitHub
is too narrow. Stack Overflow couldn't justify the effort. Triplebyte lost trust
with the people it was supposed to serve.

### Every LinkedIn alternative has failed

**Polywork** raised $13M from the Stripe founders and Alexis Ohanian to build a
LinkedIn alternative that embraced multiple professional identities. Shut down
January 2025. Couldn't achieve critical mass against LinkedIn's network effects.

**Braintrust** built a blockchain-based talent network with 0% take rate, backed
by Tiger Global and Coatue. Clients included Goldman Sachs and Nike. Then they
quietly pivoted away from the blockchain part to become an AI hiring platform.
The decentralization was de-emphasized because the market wanted AI features,
not governance tokens.

**Sovrin**, a blockchain specifically for self-sovereign identity, announced
likely shutdown by March 2025 after seven years. The community moved on.
Microsoft's **ION** (decentralized identity on Bitcoin) launched in 2021 and
went nowhere.

LinkedIn's network effect is a moat. Every challenger has drowned in it.

### Screen monitoring triggers deep anxiety — but the power dynamic matters

Here are the numbers: 74% of US employers use online tracking tools. 50% of
tech workers say they'd rather quit than endure constant monitoring. 59% say
digital tracking hurts trust.

**Crossover's WorkSmart** is the cautionary tale. It takes screenshots every 10
minutes, logs keystrokes, and ties compensation to "focus scores." Glassdoor
reviews call it "slave labor." The EFF calls this category of software
"bossware."

But every one of these controversies shares a common trait: **the employer
controls the monitoring, not the employee.** The person being watched has no
say in what's captured, who sees it, or how it's used.

What happens when you invert that? When the worker runs the software, owns the
data, controls the guard model, sees the audit log, and can turn it off
at any time?

That's a meaningfully different product. Not bossware. A professional memory
that you choose to share.

## What makes this concept different

The key architectural decisions that distinguish this from everything that's
come before:

**1. The data never leaves your machine (until you want it to)**

There is no cloud. No server that holds everyone's data. No company that can
get breached and leak your screen history. Your ChromaDB runs locally. Your
screenshots stay on your disk. When you turn off the sharing switch, the data
is completely inaccessible.

**2. You control the security policy — in plain English**

The security policy is literally a markdown file on your computer. It says
things like "block queries about personal life" and "redact API keys matching
sk-*" in plain language. A lightweight AI model (Qwen3Guard, 0.6B parameters,
runs on any MacBook) reads this policy and enforces it on every request and
response. To change the policy, you edit the file. No code, no configuration
UI, no support ticket.

**3. Every query is logged**

You see exactly what people asked and what they received. If a recruiter queries
"show me their salary negotiations" (which the guard model would block), you
know they tried. This creates accountability on the searcher side that doesn't
exist in any current system.

**4. The network is decentralized by default**

Each person is a node. There's no central database of everyone's work history.
A lightweight registry helps people discover each other (like DNS for
professional identity), but all actual data stays with individuals. If the
registry disappears, you still have your data. If you want to leave the
network, you just stop publishing.

## The hard problems

I want to be honest about what's genuinely difficult here.

### The trust triangle

Three parties need to trust the system simultaneously:

- **The worker** must trust that the guard model won't leak sensitive data
- **The worker's employer** must accept that their employee runs screen
  recording software (even if the data is filtered before sharing)
- **The recruiter** must trust that the evidence is genuine and not fabricated

Each relationship is hard alone. All three holding simultaneously is very hard.

### The proprietary work problem

Most interesting professional work is proprietary. If you're building internal
tools at a company, your screen captures contain that company's code, data, and
architecture. Even with an AI guard, the line between "evidence of my skills"
and "my employer's trade secrets" is blurry.

This is solvable — the guard model can be tuned to share patterns ("they work
with Kubernetes, Terraform, and Go") without sharing specifics ("they're
building a multi-tenant billing system for Acme Corp"). But it requires
sophisticated filtering, and the consequences of getting it wrong are serious.

### The cold start problem

A network of searchable professional histories is only valuable when enough
people are on it. Recruiters won't search if there are 50 nodes. Engineers
won't publish if no recruiters are searching. This is the same chicken-and-egg
problem that killed Triplebyte and Polywork.

The advantage here is that Memex is useful even with zero network — it's your
personal searchable memory first, a professional tool second. You don't join
the network for the network. You use the tool for yourself, and the network
is an optional feature you turn on when job hunting.

### The fabrication problem

What stops someone from faking their Memex data? A few things:

- **Volume**: A year of data is ~500K screenshots. Fabricating that is
  impractical.
- **Temporal patterns**: Real work has natural rhythms — 9-5 activity, weekend
  gaps, context switches. Fakes tend to be too uniform.
- **Depth**: A recruiter can ask follow-up questions. Faked data breaks down
  under scrutiny because the underlying context doesn't exist.
- **Cross-referencing**: If two people worked on the same project, their data
  should overlap. This creates a web of verifiability.

None of these are bulletproof. But they're significantly more verification than
a resume offers.

## Why now?

Three things have changed that make this concept more viable than it was even
two years ago:

**1. Local AI models are good enough.** A 0.6B parameter model can run on any
MacBook at 200+ tokens per second. Two years ago, you needed a cloud API for
any useful AI inference. Now you can run a capable guard model as local
middleware with no internet connection required.

**2. The tools are open source.** Screenpipe, ChromaDB, Ollama, Tesseract —
every component of this stack exists as a mature, open-source project. You
don't need to build the capture engine or the vector database or the model
runtime. You need to build the privacy layer and the network layer.

**3. The hiring market is broken in a way that hurts everyone.** Companies
spend $4,700 per hire on average. The average time to fill a position is 44
days. 75% of resumes are never seen by a human. Meanwhile, engineers spend
weeks grinding LeetCode for interviews that don't reflect actual work.
Both sides are wasting enormous amounts of time and money on a process
that produces poor signal.

## What this looks like in practice

A recruiter searches: "engineers with production Kubernetes experience who've
worked with service meshes in the last year."

The registry returns a list of online nodes. The recruiter queries them. Each
node's guard model checks the query (legitimate, professional), searches the
local ChromaDB, filters the results (strips company names, internal URLs, API
keys), and returns timestamped evidence: this person was writing Istio configs
on these dates, debugging Envoy proxy issues on these dates, reviewing Helm
chart PRs on these dates.

Not "5 years of Kubernetes experience" on a resume. Actual evidence of actual
work.

The engineer sees in their audit log: "recruiter@bigtech.com searched
'kubernetes service mesh' — 12 results returned, 3 fields redacted." They know
exactly what was shared.

## The bigger picture

The internet was supposed to be decentralized. Your professional identity was
supposed to be yours. Instead, LinkedIn owns your professional graph, and
recruiters pay LinkedIn to access you. Your work history lives on their
servers. Your connections are their data. If LinkedIn changes their algorithm
or their pricing or their terms, you have no recourse.

A decentralized network of personal Memex nodes inverts this. Your data lives
on your machine. Your professional identity is a searchable, verifiable history
of what you've actually done. You control who sees what. The network helps
people find you, but the data belongs to you.

Is this harder to build than a centralized platform? Yes. Is the cold start
problem real? Absolutely. Will incumbents fight it? Of course.

But the alternative — continuing to pretend that a two-page PDF of
self-reported claims is a useful signal for hiring decisions — is increasingly
absurd. The technology to do better exists today. The question is whether
enough people want it badly enough to build the network.

I think they do.

---

*If you want to try Memex for yourself, the project is open source at
[github.com/joenewbry/memex](https://github.com/joenewbry/memex). It runs
locally on macOS, captures your screen history, and makes it searchable. The
network features described in this post are on the roadmap.*
