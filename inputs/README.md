# Inputs — your elicited judgements

The pipeline reads the pairwise-comparison matrices from `interview_data.py` in
this folder. That file is **not** in the repository, because it holds your own
study data. A synthetic, clearly-labelled template ships as
`interview_data.example.py`; if `interview_data.py` is absent, the template is
used automatically so a fresh checkout runs.

## To use your own study

1. Copy the template:
   ```bash
   cp inputs/interview_data.example.py inputs/interview_data.py
   ```
2. Replace every matrix in `interview_data.py` with your own judgements.
   Keep the orderings: alternatives **MBR, EC, CW**; criteria **Efficiency,
   Cost, Land, Energy, Chemical, Odor**. Matrices are reciprocal, Saaty 1-9.

`inputs/interview_data.py` is git-ignored, so your data will not be committed
by accident.

## Starting from raw interviews

If you have raw per-respondent judgements rather than group matrices, build the
group matrices first (geometric-mean aggregation with consistency screening):

```bash
python scripts/build_matrices_from_interviews.py
```

Edit that script to feed in your own respondent rows, then paste the resulting
matrices into `interview_data.py`.
