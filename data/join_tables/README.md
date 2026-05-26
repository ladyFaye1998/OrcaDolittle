# Call-type to behavioural-context join table

## How to fill this in

Each row in `call_type_to_context.csv` maps a specific call type to its primary behavioural context.

**Columns:**
- `population`: SRKW, NRKW, SAR, TKW, OKW
- `call_type`: The catalogue call-type ID (e.g., S01, N01, AK01, T01)
- `primary_behavioural_context`: One of: `foraging`, `traveling`, `resting`, `socializing`, `excitement`
- `secondary_context`: Optional secondary association
- `citation_key`: BibTeX key from `paper/refs.bib` (e.g., `ford1989`, `foote2008`)
- `notes`: Any caveats (e.g., "context association weak", "n < 10 encounters")

## Source papers (in priority order)

1. **Ford 1989** (`@ford1989`) — The foundational SRKW/NRKW call-type catalogue. Maps discrete call types to behavioural states for Southern and Northern Residents.
2. **Foote 2008** (`@foote2008`, *Ethology*) — Temporal and contextual patterns of SRKW calls. Key for V4 excitement/foraging association.
3. **Filatova 2015** (`@filatova2015`) — Cultural evolution of call types. Useful for NRKW and cross-population comparisons.
4. **Riesch 2008** (`@riesch2008`) — Discrete calls of NE Pacific transients (TKW). The only systematic catalogue for Bigg's.
5. **Yurk 2002** (`@yurk2002`) — Cultural transmission in Alaska Residents (SAR/NRKW). Key for SAR call types.

## Rules

- Every row MUST have a `citation_key` pointing to `paper/refs.bib`
- If a call type is associated with multiple contexts, use `primary` for the strongest and `secondary` for the weaker
- If the association is uncertain (n < 10 encounters), note it
- DO NOT guess — leave blank if the paper does not explicitly state the association
