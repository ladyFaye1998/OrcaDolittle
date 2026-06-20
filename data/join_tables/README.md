# Call-type to behavioural-context join table

## Status

**Complete extraction from all available sources (2026-05-26).** 30 rows covering NRKW, SRKW, SAR, and TKW populations from Ford 1989, Foote 2008, Riesch 2006, and Yurk 2005.

## Key insight

The call-type-to-context mapping is NOT a clean 1:1 relationship. Ford 1989 explicitly states: "no call type was correlated exclusively with any behaviour." Instead, there are three types of associations:

1. **Activity-associated** (Ford 1989): Some calls shift in relative frequency between foraging/travelling/resting/socializing
2. **Social-context-associated** (Foote 2008): "Dominant" calls (pod identity) decrease in multi-pod groups; "rare" biphonic calls (inter-pod affiliation) increase
3. **Arousal-associated** (Ford 1989): Excited calls are shorter, higher-pitched, faster; N2 spikes during pod meetings

This means H1 probes should predict **distributional shifts** (which activity state is most likely given this embedding), not deterministic labels. Frame as: "embeddings predict the probability distribution over behavioural states."

## Columns

- `population`: SRKW, NRKW, SAR, TKW, OKW
- `call_type`: Catalogue ID (N-series = Northern Resident, S-series = Southern Resident)
- `primary_context`: The strongest context association
- `secondary_context`: Optional weaker association
- `context_type`: One of `activity`, `social`, `arousal`
- `proportion`: Quantitative proportion where available (e.g., "52.4%")
- `citation_key`: BibTeX key from `paper/refs.bib`
- `notes`: Caveats and specifics

## Source papers

1. **Ford 1989** — 5 activity states (foraging, travelling, resting, socializing, beach-rubbing) × 16 Northern Resident pods. Key: N3=resting, S1=foraging, S2/S44/S42=travelling.
2. **Foote 2008** — Single-pod vs multi-pod context for Southern Residents over 27 years. Key: dominant calls = pod identity; rare biphonic calls = inter-pod affiliation.
3. **Riesch 2006** — Stereotyped whistles (W1-W6 in NR, SW1-SW4 in SR). Key: NR whistles = close-range socializing; SR whistles = long-range contact (like discrete calls).
4. **Yurk 2005** — Southern Alaska residents. Key: two vocal clans (AB, AD) reflecting matrilineal ancestry; call sharing correlates with association rate; transients use entirely distinct LFC syllables.
5. **Ford 1989** (transients) — TKW are largely silent during foraging (prey detection avoidance); vocal post-kill and during travel.

