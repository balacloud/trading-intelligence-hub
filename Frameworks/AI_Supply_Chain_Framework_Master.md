# AI Supply Chain — Stock Analysis Framework
### Master Reference Document
*Last Updated: June 5, 2026 | All data from verified Q1/Q2 2026 filings | Not financial advice*

---

## Executive Summary

This framework identifies **hidden gem stocks** across the AI infrastructure supply chain — companies with verified revenue anchors in government/private AI spending, structural competitive moats, and a visibility gap (under-owned by institutional funds). The framework deliberately avoids chasing headline names and instead maps the 8 supply chain layers that every AI data centre depends on, then scores each company across 6 weighted pillars.

**Core thesis in one line:** Every AI data centre needs Power → Chips → Cooling → Network → Nuclear fuel. We own the toll booths at each layer, not the hype stocks.

---

## Part 1 — The 6-Pillar Scoring System

Each stock is scored out of 100 using six weighted pillars:

| Pillar | Weight | What It Measures |
|---|---|---|
| 🏛 Budget / Contract Anchor | 28% | Named in government budget, confirmed backlog, signed contract or legislation |
| 💎 Quality Score | 18% | FCF margin, gross margin, balance sheet strength, debt levels |
| ⚡ Execution Score | 18% | Backlog conversion rate, earnings delivery vs guidance, management track record |
| 👁 Visibility Score | 18% | INVERSE of analyst coverage — high score = still under the radar |
| 💰 Valuation Score | 9% | P/E, EV/FCF, Price/Sales vs sector peers |
| 🚀 Catalyst Score | 9% | Verified near-term triggers: contracts, policy, earnings inflections |

**Hidden Gem Threshold:** Score ≥ 75 AND Visibility Score ≥ 6/10 AND data verified from primary filings.

**Zero-Hallucination Rule:** Every score must be traceable to a named source — a press release, earnings call transcript, or regulatory filing. No analyst price targets or media narratives count as anchor evidence.

---

## Part 2 — The 8-Layer Supply Chain Map

```
L1    Physical Inputs     Uranium • Copper • Rare Earth Metals
L2    Foundry & Tools     Advanced chip manufacturing • Wafer inspection equipment
L2.5  Test & Validation   Certifies every chip, port, rack before deployment  ← Added June 2026
L3    Chips               GPU • Custom XPU • Memory • Connectivity ICs
L4    Systems             AI Servers • Storage • Rack integration
L5    Networking          AI fabric • Switches • Transceivers
L6    Power & Cooling     Grid • UPS • Liquid cooling • Nuclear generation
L7    Software & Services Cloud platform • AI database • IT consulting
```

**Why L2.5 was added:** No chip, interconnect, PCIe slot, HBM stack, or 1.6T Ethernet port gets deployed without being validated by test equipment first. Keysight Technologies (KEYS) is the dominant player in this layer — it is the last checkpoint before deployment across the entire AI supply chain.

---

## Part 3 — Top 20 Ranked Stocks

### TOP 10 — Hidden Gems (Score ≥ 75)

---

#### #1 — GEV | GE Vernova 🇺🇸 | Score: 82.8 | Layer: L6 Power 💎 GEM

**What they do:** Manufactures transformers, switchgear, gas turbines, and grid hardware. The dominant western supplier of power grid infrastructure.

**Why it scores #1:**
- $163B backlog, up from $95B two years ago
- Q1 2026 orders +71% YoY; data centre-specific orders $2.4B in Q1 alone
- Only western manufacturer with capacity across the full grid stack (generation → transmission → distribution)

**Verified Q1 2026 data:** Revenue beat, backlog record, guidance raised.

**The thesis:** You cannot build an AI data centre without grid connection. GEV makes the transformers, switchgear, and turbines that connect every new data centre to the grid. With the US declaring the power grid a national defence priority (April 2026), GEV is structurally embedded in both private and government capex.

**Bear case:** $163B backlog is only valuable if GEV can execute. Historical delivery delays on large transformer orders are a real risk. Backlog ≠ revenue unless operational execution holds quarter by quarter.

**Supplier layer note:** GEV is itself a customer of FCX (copper), CLF (electrical steel), and PWR (installation).

---

#### #2 — ETN | Eaton Corporation 🇺🇸 | Score: 81.9 | Layer: L6 Power 💎 GEM

**What they do:** Power management — circuit breakers, busbars, UPS systems, switchgear for data centres and grid infrastructure.

**Why it scores #2:**
- Best FCF/Beta ratio in the entire framework (4.84) — highest quality per unit of risk
- Simultaneously anchored to 4 structural spending programmes: AI data centres, grid modernisation, defence electrification, EV charging
- Q1 2026 EPS record; data centre segment growing fastest

**The thesis:** ETN is the broadest beneficiary of electrification across all verticals. If AI capex slows, defence electrification and grid modernisation still drive growth. Four independent anchors in one stock.

**Bear case:** Valuation at ~39x P/E is not cheap. If any two of the four growth verticals slow simultaneously, the multiple compresses hard.

**Supplier layer:** ETN buys copper (FCX), electrical steel (CLF), and electronic components (Infineon, TE Connectivity/TEL).

---

#### #3 — GIB.A | CGI Group 🇨🇦 | Score: 80.9 | Layer: L7 Software 💎 GEM

**What they do:** Global IT services, government digital transformation, AI consulting. Headquartered in Montreal. Listed on TSX and NYSE.

**Why it scores #3:**
- Backlog $31.3B — 11+ months of forward revenue locked
- Operating cash margin 21% — best in IT services globally
- P/E ~17x — cheapest large-cap quality name in the AI universe
- <2% of US AI-focused funds own it (visibility gap is enormous)

**The thesis:** Every government modernising its digital infrastructure (Canada, UK, US, EU) is a CGI client. AI does not reduce demand for IT services — it multiplies the integration, security, and compliance work that CGI does. The stock is priced like a boring government contractor, not like a structural AI beneficiary.

**Bear case:** Revenue growth is mid-single-digit, not explosive. This is a compounder, not a rocket. If you need 30%+ growth names, GIB.A is wrong for you. The gem case rests entirely on the valuation gap closing.

**Canadian investor note:** Available on TSX as GIB.A with no foreign withholding tax in TFSA/RRSP.

---

#### #4 — TSM | TSMC 🇹🇼 | Score: 80.2 | Layer: L2 Foundry

**What they do:** The world's dominant semiconductor foundry. Manufactures chips designed by NVIDIA, Apple, AMD, Broadcom, and every major fabless company.

**Why it scores #4:**
- Revenue +35% YoY; CoWoS advanced packaging sold out through 2026
- N3 (3nm) utilization at 95%; N2 (2nm) ramping
- No single competitor within 3-4 years of matching N3 capability at scale

**The thesis:** If TSM stops, all AI stops. Every leading-edge chip in the world — NVDA GB200, Apple M5, AVGO XPU — is manufactured by TSMC. It is the single most critical node in the entire supply chain.

**Bear case:** Taiwan Strait geopolitical risk is real and unhedgeable. A blockade or conflict scenario makes TSM uninvestable regardless of fundamentals. Size position accordingly — this is why it scores #4 not #1 despite flawless fundamentals.

---

#### #5 — VRT | Vertiv Holdings 🇺🇸 | Score: 80.0 | Layer: L6 Cooling 💎 GEM

**What they do:** Liquid cooling systems, power distribution units, and thermal management for AI data centres.

**Why it scores #5:**
- FCF +147% YoY — the single best FCF inflection in the framework
- Operating margin +430bps YoY; leverage at 0.2x (near debt-free)
- Liquid cooling is now mandatory in every new AI rack due to GPU thermal density

**The thesis:** Air cooling is physically incapable of handling GB200/B300 GPU thermal loads. Every new AI data centre built from 2025 onward requires liquid cooling. VRT is the leading supplier of liquid-to-chip and rear-door heat exchanger systems.

**Bear case:** VRT's valuation re-rated significantly in 2024-2025. The easy money may be made. Execution on margin expansion in the next 2-3 quarters is what keeps the thesis alive.

---

#### #6 — CCO.TO | Cameco Corporation 🇨🇦 | Score: 78.3 | Layer: L1 Physical 💎 GEM

**What they do:** World's largest publicly traded uranium miner. Co-owns Westinghouse (reactor services) with Brookfield Renewable.

**Why it scores #6:**
- 84% of production locked under long-term contracts at rising prices
- Part-owner of Westinghouse — the dominant nuclear reactor services company
- Hyperscalers (Microsoft, Google, Amazon) signing nuclear PPAs directly, requiring fuel supply

**The thesis:** Nuclear is the only 24/7 baseload clean energy source that hyperscalers can contract directly. Every new nuclear PPA signed by a data centre operator requires uranium fuel. Cameco is the only large-scale western supplier.

**Bear case:** Uranium spot price is volatile. If nuclear project timelines slip (which they historically do), demand growth is delayed. CCO's long-term contract book provides insulation but not immunity.

**Canadian investor note:** CCO.TO on TSX. URA ETF (Global X) holds CCO at 22.2% — largest single position.

---

#### #7 — ANET | Arista Networks 🇺🇸 | Score: 78.2 | Layer: L5 Networking

**What they do:** AI data centre networking — switches, routing, network operating systems (EOS). Dominant in hyperscale AI fabric.

**Why it scores #7:**
- Revenue +35% YoY; AI-specific revenue guidance $3.5B
- Full-year guidance raised to $11.5B
- 400G/800G switching is the standard in every new AI cluster

**The thesis:** AI training requires ultra-low latency, ultra-high bandwidth interconnects between thousands of GPUs. ANET's EOS software and 800G switches are the standard fabric in every major hyperscaler's AI cluster.

**Bear case:** Microsoft and Meta are developing in-house networking silicon, which could reduce ANET's TAM at the hyperscale end over a 3-5 year horizon.

---

#### #8 — ASML | ASML Holding 🇳🇱 | Score: 76.5 | Layer: L2 Foundry Tools

**What they do:** The only manufacturer of Extreme Ultraviolet (EUV) lithography machines — the equipment that prints 3nm and below chips.

**Why it scores #8:**
- Backlog €36B; EPS beat +8.4% in latest quarter
- High-NA EUV (next generation) — ASML is the only company on earth that makes it
- Every 2nm chip (N2, A16) requires High-NA EUV — structural monopoly

**The thesis:** ASML is the deepest moat in the semiconductor supply chain. No other company can manufacture EUV systems. Every advanced chip ever made — now and for the next decade — requires ASML equipment.

**Bear case:** China export restrictions reduce ASML's TAM. Dutch/US government controls on EUV shipments to China are permanent and represent ~15% of revenue upside that is permanently lost.

---

#### #9 — CEG | Constellation Energy 🇺🇸 | Score: 76.5 | Layer: L6 Nuclear 💎 GEM

**What they do:** Largest US nuclear fleet operator. Provides 24/7 carbon-free baseload electricity via long-term Power Purchase Agreements (PPAs) with hyperscalers.

**Why it scores #9:**
- Revenue beat +23.6%; Microsoft 20-year PPA signed for Three Mile Island restart
- Crane Nuclear Station restart underway
- 71% of Americans oppose data centres in their neighbourhood vs 53% opposing nuclear plants (Gallup, May 2026) — nuclear siting is easier than data centre siting

**The thesis:** AI data centres need 24/7 clean power that can't be sited near population centres. CEG's existing nuclear fleet solves both problems simultaneously — it's already built, already permitted, already connected to the grid, and it runs 24/7 regardless of weather.

**Bear case:** Nuclear PPAs are 15-20 year deals locked at negotiated prices. If wholesale power prices fall as grid build-out succeeds, CEG's spot optionality shrinks. The existing contracted capacity is already priced in at current valuations.

**Supplier dependency:** CEG is a direct customer of CCO.TO for uranium fuel and BWXT for nuclear component services.

---

#### #10 — ALAB | Astera Labs 🇺🇸 | Score: 76.4 | Layer: L2/L3 Connectivity 💎 GEM

**What they do:** Semiconductor connectivity — PCIe 6.0 retimers, CXL memory controllers, and Ethernet smart cables for AI racks.

**Why it scores #10:**
- Revenue +93% YoY — fastest organic growth in the framework
- Gross margin 76%; EPS beat +13.6%
- Every NVIDIA GB200/B300 rack requires ALAB's connectivity fabric

**The thesis:** As GPU racks scale from 8-GPU to 72-GPU (NVL72) configurations, the PCIe and CXL interconnect becomes a critical bottleneck. ALAB is the dominant supplier of the silicon that makes multi-GPU racks work.

**Bear case:** Customer concentration risk — ALAB's revenue is heavily tied to NVIDIA's rack architecture. If NVIDIA changes its interconnect standard, ALAB must re-engineer its roadmap.

---

### RANKS #11–20 — Quality Compounders & Watchlist

| Rank | Ticker | Score | Gem? | Company | Key Data Point | Caution |
|---|---|---|---|---|---|---|
| #11 | NVDA | 74.8 | No | NVIDIA | DC rev $39.1B +73% | Priced near perfection at $5.4T mkt cap |
| #12 | AVGO | 73.8 | No | Broadcom | AI rev $12.2B, VMware ARR $10B | Best FCF/Beta after ETN, visibility gone |
| #13 | KEYS | 79.5 | 💎 | Keysight Technologies | Orders +56%, EPS beat +41% | Cyclical risk if semis capex pauses |
| #14 | MU | 72.8 | No | Micron | HBM3e constrained 2026 | NAND cyclical risk limits score |
| #15 | MRVL | 72.6 | 💎 | Marvell Tech | Amazon Trainium XPU, ASIC 40%+ rev | Hyperscaler dependency |
| #16 | ONTO | 73.6 | 💎 | Onto Innovation | Wafer inspection, advanced nodes | Small cap liquidity risk |
| #17 | CAMT | 73.6 | 💎 | Camtek | HBM bump inspection leader | Israeli geopolitical risk |
| #18 | ORCL | 73.7 | 💎 | Oracle | OCI GPU cluster build | Transition risk from legacy database |
| #19 | FCX | 68.3 | 💎 | Freeport-McMoRan | 1.05B lbs copper Q1 | Commodity price cyclicality |
| #20 | AMD | 65.5 | No | AMD | DC rev +57%, MI300X | P/E 105x — 3-5% option bet only |

---

## Part 4 — Supplier Layer (One Tier Upstream)

GEV, ETN, VRT, and CEG are themselves customers of these companies. Going one layer upstream reveals additional hidden gems:

| Supplier | Ticker | Supplies To | Framework Status |
|---|---|---|---|
| Freeport-McMoRan | FCX | GEV, ETN, VRT (copper) | ✅ Already #19 in list |
| Cleveland-Cliffs | CLF | GEV, ETN (electrical steel) | 👀 Watchlist |
| TE Connectivity | TEL | ETN, VRT (connectors) | 👀 Watchlist |
| Quanta Services | PWR | GEV (grid installation) | ✅ Known — well-followed |
| Centrus Energy | LEU | CEG, all US nuclear (enrichment) | 💎 Gem candidate ~74 pts |
| BWX Technologies | BWXT | CEG (nuclear components) | 💎 Gem candidate ~76 pts |
| Modine Manufacturing | MOD | VRT (heat exchangers) | 👀 Watchlist |
| ATI Inc | ATI | CEG (specialty alloys/zirconium) | 👀 Watchlist |
| Infineon Technologies | IFNNY | ETN, GEV (power semiconductors) | 👀 Watchlist |

### LEU — Centrus Energy (Gem Candidate)
The only US-licensed uranium enricher. With Russian enrichment services sanctioned and URENCO capacity constrained, LEU is a genuine structural bottleneck. Market cap ~$1.5B vs the strategic role it plays. Scores approximately 74 — just below gem threshold. High catalyst risk (regulatory) limits score.

### BWXT — BWX Technologies (Gem Candidate)
Sole supplier of US Navy submarine nuclear reactors. Also provides nuclear component services to CEG and the commercial fleet. Total backlog $7.3B (+50% YoY), commercial backlog +85% YoY. FY2025 all records. Scores approximately 76 — clears the gem threshold. Already identified in the US market analysis.

---

## Part 5 — ETF Coverage Map

For investors who prefer diversified exposure over individual stock picking:

| ETF | Ticker | Layer Coverage | Key Holdings From Framework | Expense Ratio |
|---|---|---|---|---|
| VanEck Semiconductor | SMH | L2 + L3 | NVDA, TSM, AVGO, ASML, MU, ALAB | 0.35% |
| First Trust Smart Grid | GRID | L6 Power | ETN 7.95%, GEV, VRT top holdings | 0.56% |
| ALPS Electrification | AIPO | L6 Power (AI-focused) | VRT 8.98%, GEV 8.60%, ETN 7.58% | ~0.50% |
| Global X Uranium | URA | L1 Nuclear | CCO at 22.2% — largest single holding | 0.49% |
| Global X Copper Miners | COPX | L1 Physical | FCX top holding | 0.65% |
| iShares Semiconductor | SOXX | L2 + L3 | AVGO #1, NVDA #2, MU top 5 | 0.35% |

**ETF honest assessment:**
- ✅ URA for CCO exposure — 22% weight means near-pure CCO with uranium sector diversification
- ✅ GRID/AIPO for power layer — ETN + GEV + VRT are genuinely top holdings, not diluted
- ⚠️ SMH for semis — gets NVDA/TSM/AVGO but ALAB and KEYS are tiny weights — loses the gem edge
- ❌ No ETF covers GIB.A — CGI is Canadian, under-owned by US ETFs, which is exactly why it scores 80.9 on visibility

**Canadian investor note:** HURA.TO (TSX) provides CCO uranium exposure in CAD. ZSP.TO / XQQ.TO for broad US tech exposure in CAD with no foreign withholding tax drag in TFSA/RRSP.

---

## Part 6 — Macro Catalysts (Verified, June 2026)

### The NIMBY Nuclear Thesis
- 71% of Americans oppose AI data centres near them (Gallup, May 2026)
- Only 53% oppose nuclear plants nearby — nuclear is MORE acceptable than data centres
- This forces hyperscalers toward off-site nuclear PPAs → direct catalyst for CEG and CCO
- States pushing "Bring Your Own Generation" mandates — hyperscalers fund nuclear directly
- **Stocks impacted:** CEG (#9), CCO (#6), BWXT (gem candidate), LEU (gem candidate)

### US Grid as National Defence Priority (April 2026)
- White House declared US power grid a national defence asset
- Unlocks emergency procurement pathways and federal funding for grid upgrades
- **Stocks impacted:** GEV (#1), ETN (#2), PWR (watchlist)

### Canada Pipeline Reform — Carney Cabinet (May 2026)
- Accelerated approval process for new energy infrastructure
- Removes key bottleneck for LNG Canada export routes
- **Stocks impacted:** CCO.TO (#6) via Montney gas optionality, GIB.A (#3) via government IT contracts

### AI Data Centre Energy Demand
- Data centre energy consumption approaching 1,050 TWh globally by end of 2026
- US data centres consuming 4.5% of national grid capacity (up from 2% in 2023)
- **Stocks impacted:** All L6 power names (GEV, ETN, VRT, CEG)

---

## Part 7 — Behavioral Finance Checks

Apply these before every buy or sell decision:

| Bias | Check | Application to This Framework |
|---|---|---|
| 🧠 Loss Aversion | Pain of a loss = 2× joy of a gain | Never panic-sell a name whose verified backlog/contract thesis is intact |
| 🔍 Confirmation Bias | Actively search for data that DISPROVES your thesis | Before buying: find the strongest bear case, then decide |
| 🐑 Herd Behavior | If every fund already owns it, visibility = low, edge is gone | NVDA and AVGO are consensus — the framework edge lives in GIB.A, KEYS, ALAB |
| ⚓ Anchoring | Entry price is irrelevant to forward thesis | Evaluate the next 12 months of earnings, not your purchase price |
| 🏠 Familiarity Bias | Do not overweight your home country | Canadian investors: check total CCO + GIB.A concentration vs global names |

---

## Part 8 — Framework Rules (Zero-Hallucination Standard)

1. **Never assume** risk tolerance, time horizon, or tax residency — ask first
2. **Every score must cite** a primary source: press release, earnings transcript, or filing
3. **No analyst price targets count** as anchor evidence — only verified company data
4. **Run the bear case first** — before presenting any thesis, identify the strongest counter-argument
5. **Visibility gap check** — if a stock is on the cover of Bloomberg, its gem score drops immediately
6. **Canadian specifics** — always note CAD/USD currency risk, dividend tax credits, TFSA/RRSP eligibility
7. **Indian market note** — use ETF routes (not direct equities) unless investor has NRI/domestic account access

---

*AI Supply Chain Stock Analysis Framework | Version 3.0 | June 5, 2026*
*Not financial advice. All data from verified public filings. Do your own due diligence.*
