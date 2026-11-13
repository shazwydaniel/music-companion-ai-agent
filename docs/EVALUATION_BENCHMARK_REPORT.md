# Riffin’ Evaluation Benchmark Report

Run: **13 November 2026, 06:53 UTC** · Model: **gemini-3.6-flash** · Result: **4/4 passed**.

## Golden cases

| Case | Result | Judge score |
| --- | --- | ---: |
| `internal_triad` | Pass | 5/5 |
| `music_math` | Pass | 5/5 |
| `catalog_lookup` | Pass | 5/5 |
| `destructive_guard` | Pass | 5/5 |

## Model telemetry

| Component | Calls | Input tokens | Output and thinking tokens | Estimated USD |
| --- | ---: | ---: | ---: | ---: |
| Riffin’ assistant | 12 | 11,110 | 3,280 | $0.02063250 |
| Independent Gemini judge | 4 | 1,156 | 1,678 | $0.00715950 |
| Total | 16 | 12,266 | 4,958 | $0.02779200 |

The estimate uses the dated Gemini paid-tier generation rates in [Google’s pricing page](https://ai.google.dev/gemini-api/docs/pricing/). It is not an invoice or free-tier charge. It excludes embeddings, Search queries, cache storage, discounts and taxes. An unavailable cost means provider usage metadata or a model rate was missing; token totals may then be incomplete.

## Method

4 public cases in [`tests/golden_cases.json`](../tests/golden_cases.json) run through separate in-memory assistant sessions. A separate structured Gemini judge scores each observed result; status, required specialist route and exact note-title checks also have to pass. The report contains case IDs and aggregate telemetry, not API keys, visitor data, full prompts or answer text.

Reproduce with `python scripts/evaluate_agent.py --report docs/EVALUATION_BENCHMARK_REPORT.md`. Provider availability and model behavior can change between runs.
