# Synthetic Steel-Remnant and Plate-Nesting Demonstrations

A small, deterministic proof of concept exploring two problems relevant
to structural steel fabrication:

1. Determining whether steel remnants are eligible for reuse.
2. Comparing simple rectangular plate-packing heuristics against a
   defined baseline.

The prototype uses invented data only. It is intended to demonstrate
specific engineering principles, not to represent a production-ready
steel-nesting system.

**No machine-learning model is trained.** The remnant matcher uses
rule-based eligibility checks, while the plate-packing demonstration
uses deterministic geometric heuristics.

## 1. Remnant Eligibility and Matching

Source: `src/remnant_matcher.py`

This demonstration checks whether a remnant is eligible for a material
requirement using criteria such as:

- Material grade and form.
- Dimensional compatibility.
- Availability and material status.
- Traceability.
- Drawing-revision release status.
- Project-transfer permissions.

Eligible candidates are ranked using a simple greedy best-fit rule.

The synthetic example deliberately rejects an unauthorised
cross-project candidate.

**Engineering principle:** A remnant should not be recommended merely
because its dimensions fit. Material compatibility, traceability,
revision status, and allocation policy must also be satisfied.

## 2. Rectangular Plate-Packing Heuristics

Source: `src/plate_nesting_demo.py`

This demonstration compares two simple shelf-packing strategies on a
synthetic batch of 13 rectangular parts using nominal stock dimensions
of 1,000 × 800 mm.

| Method | Strategy | Plates used |
|---|---|---:|
| Baseline | Next-fit shelf packing in input order | 5 |
| Alternative | Best-fit-decreasing shelf packing | 3 |

For this specific example, net-part area yield is approximately:

- Baseline: 39.61%
- Alternative: 66.01%

The alternative uses two fewer plates for this synthetic batch.

These results illustrate how heuristic selection can affect packing
efficiency. They do not establish global optimality, generalise to all
part mixes, or demonstrate savings for any real fabricator.

### What the metric means

Net-part area yield is calculated as:

`Total net area of placed rectangular parts / Gross stock area × 100`

Gross stock area is the number of plates used multiplied by the nominal
area of each plate.

The unaccounted area includes unused space, trim, kerf allowances, and
other residual area under the demonstration's simplified assumptions.

It is **not an audited scrap rate** and should not be equated with the
client's reported material wastage.

The generated placement coordinates are illustrative coordinates
relative to the usable stock region. They are not CNC-ready output.

## 3. Reproduce the Demonstrations

Requirements: Python 3.10 or later. No third-party packages are required.

Run the remnant-matching demonstration:

```bash
python src/remnant_matcher.py --input data/synthetic_cases.json
```

Run the plate-packing comparison:

```bash
python src/plate_nesting_demo.py --input data/plate_nesting_cases.json
```

Run the automated test suite:

```bash
python -m unittest discover -s tests -v
```

The included tests validate selected behaviours of the demonstration
code. Passing tests does not establish industrial suitability or
real-world performance.

## 4. Repository Structure

```text
.
├── README.md
├── src/
│   ├── remnant_matcher.py
│   └── plate_nesting_demo.py
├── data/
│   ├── synthetic_cases.json
│   ├── plate_nesting_cases.json
│   ├── remnant_matcher_demo_output.json
│   └── plate_nesting_demo_output.json
└── tests/
    ├── test_remnant_matcher.py
    └── test_plate_nesting_demo.py
```

## 5. Scope and Limitations

Neither demonstration is a production system, CAD parser, CNC-ready
planner, or globally optimal nesting solver.

The plate-packing example uses rectangular geometry and simplified
kerf and edge-trim approximations. It does not model the full range
of industrial nesting constraints.

A production deployment would require, at minimum:

- Validated part geometry and material specifications.
- Approved drawing revisions and material traceability.
- Machine-specific cutting and handling constraints.
- Appropriate optimisation methods for the actual material and part
  geometries.
- Integration testing with existing operational systems.
- Engineering and production approval before a cutting plan is released.
- Evaluation against measured production outcomes.

## 6. Confidentiality

All input data is synthetic.

No discovery-call notes, client datasets, proprietary records, or
client-specific commercial information are included in this repository.

The prototype demonstrates a possible technical approach; it does not
establish production performance, material savings, or financial returns.