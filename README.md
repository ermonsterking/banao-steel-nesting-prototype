# Synthetic steel-remnant and plate-nesting demonstrations

This repository contains two **small, deterministic demonstrations using invented data only**. They support two narrow points in the case-study proposal: (1) operational rules must gate material reuse, and (2) even a simple cutting heuristic should be measured against a defined baseline rather than assumed to be better.

## Demo A — Remnant eligibility and matching

`src/remnant_matcher.py` checks material grade/form, dimensions, status, traceability, revision release, and project-transfer policy. It applies a simple greedy best-fit rule to match requirements with eligible remnants. The sample intentionally rejects an unauthorised cross-project candidate.

## Demo B — 2D rectangular plate-packing heuristics

`src/plate_nesting_demo.py` compares two shelf-packing heuristics on a synthetic batch:

- **Baseline:** next-fit shelf packing in input order.
- **Alternative:** best-fit-decreasing shelf packing, considering existing shelf openings before adding another row or plate.

For the included synthetic example (13 rectangular parts; 1,000 × 800 mm stock), the baseline uses 5 plates and the alternative uses 3. Net-part area yield is reported as 39.61% and 66.01%, respectively. These numbers demonstrate how heuristic choices can affect a toy example; **they are not client results, do not establish savings, and do not show global optimality**. Results depend on part mix and the chosen baseline. The algorithms are simple shelf heuristics, not industrial nesting algorithms.

Run it with:

```bash
python src/plate_nesting_demo.py --input data/plate_nesting_cases.json
```

The output includes placements and explicitly labels the case as synthetic. Area yield uses the sum of net rectangular part areas divided by gross stock area; residual area includes trim, kerf, shelf gaps and other unused areas and is not an audited scrap rate.

## What neither demo does

Neither demo is a production system, CAD parser, CNC-ready planner, global optimiser, or evidence of actual savings. The plate demo uses rectangular parts and simplified kerf/edge-trim approximations. Real deployment needs validated geometry, steel specifications and traceability, machine restrictions, approved revisions, cutting sequence, handling constraints, integration testing and Engineering/production sign-off.

## Run tests

Requires Python 3.10+ and no third-party packages:

```bash
python -m unittest discover -s tests -v
python src/remnant_matcher.py --input data/synthetic_cases.json
python src/plate_nesting_demo.py --input data/plate_nesting_cases.json
```

All inputs are synthetic. No discovery notes, client data, proprietary records, or real commercial figures are included.
