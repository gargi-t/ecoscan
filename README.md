# 🌱 EcoScan -- AI-Powered Sustainability Scanner

A capstone prototype built for the AI Project Logbook / IBM EdTech Youth Challenge.
EcoScan looks up a product (by barcode or name) and generates an instant
0-100 sustainability score across four factors -- **Sourcing, Packaging,
Transport, and Labor** -- then suggests greener alternatives in the same
category. Built in support of **SDG 12: Responsible Consumption and
Production**.

> This README doubles as the technical section of our project write-up --
> see the Logbook (sections 7 & 8) for the problem/user research behind
> these design decisions.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will open the app at `http://localhost:8501`. Try barcode
`8901111000028` (Baked Veggie Crisps) or search by name for "chocolate" to
see it in action. If you're offline or the live API is unreachable, the app
automatically falls back to the bundled sample dataset (`data/sample_products.csv`)
so a demo still works without wifi.

Run the test suite with:

```bash
pytest
```

Generate the analysis charts (brand distribution, origin map, word cloud,
correlation heatmap) with:

```bash
python analysis/exploratory_analysis.py
```

## Project structure

```
ecoscan/
├── app.py                        # Streamlit UI (2 tabs: Scan a Product, Dataset Insights)
├── scanner/
│   ├── data_fetcher.py           # Open Food Facts / Open Product Facts API calls
│   ├── scoring.py                # The scoring engine -- see "How scoring works" below
│   ├── recommender.py            # Finds & ranks greener alternatives
│   ├── utils.py                  # Distance lookup, CO2-equivalent messaging
│   └── geo_data.py                # Country -> approx. distance-from-India table
├── data/sample_products.csv      # Offline demo dataset (fictional brands)
├── analysis/exploratory_analysis.py  # The 4 analyst-facing charts
└── tests/test_scoring.py         # Unit tests for the scoring logic
```

## How scoring works

We do **not** use a trained machine-learning model in this prototype. We
don't have a labelled dataset of "true" sustainability scores to train one
on, and inventing fake ground-truth labels would make the model worse, not
better. Instead, `scanner/scoring.py` implements a **transparent, explainable
scoring model**:

| Factor | 0-25 pts | How it's calculated |
|---|---|---|
| **Sourcing** | keyword matching **+** a small TF-IDF/cosine-similarity "semantic lean" check | This is our lightweight, fully-local stand-in for the "large language model + semantic search" idea in our original concept (Logbook 5.1) -- it compares meaning, not just exact keywords, without needing a paid API |
| **Packaging** | keyword match | cardboard/glass/metal/recyclable score higher than single-use plastic |
| **Transport** | distance banding | estimated shipping distance from the product's country of origin (see `geo_data.py`) |
| **Labor** | label match | recognised fair-trade/ethical labels raise the score; their *absence* is treated as neutral, not penalised, since small/local producers often can't afford certification -- see the fairness note in `scoring.py` |

Every function is commented with its reasoning so the score is explainable
to a user, a teacher, or a judge -- ask "why did this product get 62/100?"
and the answer is always traceable to specific text in the product data.

**Planned upgrade path:** once we log enough user feedback (thumbs up/down
on suggestions) and verified scores, `scanner/scoring.py` is the only file
we'd need to change to swap in a trained model -- everything else
(`data_fetcher.py`, `recommender.py`, `app.py`) reads from the same output
shape (`{total, sourcing, packaging, transport, labor}`) and wouldn't need
to change.

## Data sources & attribution

- **[Open Food Facts](https://world.openfoodfacts.org)** and **[Open Product
  Facts](https://world.openproductfacts.org)** -- crowdsourced, free, no-API-key
  product databases, used under the [Open Database License
  (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/). We send a
  descriptive `User-Agent` header on every request as their API guidelines
  ask (see `scanner/data_fetcher.py`) -- update the contact email in that
  file to your own before deploying this beyond a school demo.
- Full-text search ("search by name") uses Open Food Facts' v1 search
  endpoint (`/cgi/search.pl`) because the newer v2 endpoint only supports
  structured/tag filters, not free text, as of when we built this.
  Category-based lookups (used by the recommender) use the v2 endpoint.
- **Sample dataset** (`data/sample_products.csv`): a **fictional** set of
  ~30 products we made up ourselves for offline demos and the analysis
  charts -- brand names like "GreenLeaf Foods" and "ValuePack Co." are not
  real companies. We did this deliberately so the demo dataset never makes
  sustainability claims -- true or false -- about an actual brand.
- Ideas for further sourcing (not yet integrated -- see Logbook 7.2):
  [WikiRate](https://wikirate.org) for brand sustainability scores,
  [Open Supply Hub](https://opensupplyhub.org) for supply-chain mapping, and
  certification sites (Fair Trade, Rainforest Alliance) for label verification.

## Known limitations / what testing surfaced

See Logbook section 9 for the full testing write-up. Headline items:

- No live camera barcode scanning yet -- users type the barcode or name.
- Coverage is only as good as Open Food Facts/Open Product Facts' data,
  which is stronger for large/international brands than small local ones.
- The CO2-equivalent "impact summary" numbers are illustrative estimates
  for engagement, not certified carbon-accounting figures.

## Future improvements

- Real camera-based barcode scanning (`st.camera_input` + a barcode-decoding
  library).
- A trained ML scoring model once we have verified, labelled data.
- Local/regional brand coverage via manual data entry or partnerships.
- Multilingual UI for wider community use.

## Team

See the AI Project Logbook for team roles, the full project timeline, user
research, and testing notes.
