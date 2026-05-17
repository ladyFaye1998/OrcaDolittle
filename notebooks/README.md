# Notebooks

Reproducible exploration notebooks. Each is runnable end-to-end on the DCLDE 2026 cache + the playback corpus shipped in the package.

| Notebook | Purpose |
|:---|:---|
| `01_data_exploration.ipynb` | Inspect DCLDE 2026 annotations · per-ecotype class balance · call-type histograms. |
| `02_perception_baseline.ipynb` | Frozen-encoder linear probe for ecotype and call type. |
| `03_generative_head.ipynb` | Conditional VAE training + KID-against-held-out evaluation. |
| `04_selection_policy.ipynb` | Off-policy bandit training + DR-IPS evaluation against the playback corpus. |
| `05_full_loop_demo.ipynb` | End-to-end closed-loop demonstration on an OrcaSound clip. |

To regenerate the notebook outputs:

```bash
pip install -e ".[all]"
jupyter nbconvert --to notebook --execute notebooks/*.ipynb --inplace
```
