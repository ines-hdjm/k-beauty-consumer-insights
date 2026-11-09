# Data model and provenance

Keys describe the logical CSV grain and are validated in Python; a CSV engine does not enforce them. See `../data/README.md` for stage paths.

| Table | Logical key | Parent / meaning |
| --- | --- | --- |
| products | product_id | Product inventory, historical metadata |
| reviews | review_id | product_id → products |
| review_themes | review_id, theme | review_id → reviews; multiple themes allowed |
| review_skin_concerns | review_id, skin_concern_standardized | review_id → reviews |
| key_ingredient_evidence | product_id, key_ingredient_name | product_id → products; exact highlighted labels and available descriptions |
| product_key_ingredients | product_id, key_ingredient_standardized | product_id → products; deduplicated marketing-label membership |
| claim_evidence | product_id, claim_text | product_id → products; exactly one category per statement |
| product_claim_categories | product_id, claim_category, claim_type | product_id → products; deduplicated category membership |

Evidence fields include source_url, processed_at_utc, available description, manual coding method/notes and source section/extraction method where recorded. BOJ cleanser's original evidence did not include source_section/extraction_method; missing historical metadata is not silently invented. The documented method is captured HTML parsing. Other records are manually transcribed screenshots. Missing ingredient descriptions are retained; statements that only have a bullet or icon label have no separate claim description.

November update: 37 ingredient entries → 36 membership pairs because two COSRX cream snail labels share one comparison label. 44 claims → 41 membership pairs because some product statements share a category. The 44 claims comprise 36 skin benefits, 4 usage labels and 4 testing labels. Deduplication occurs only in membership tables; evidence survives.

## Explicit ingredient mapping

| Original label | Comparison label |
| --- | --- |
| 72.6% Propolis Extract | Propolis Extract |
| 10.7% Honey Extract | Honey Extract |
| 0.2% Panthenol | Panthenol |
| Blue Hyaluronic Acid (Blue HA) | Blue Hyaluronic Acid |
| Snail Mucin 92% | Snail mucin |
| Snail Filtrate | Snail mucin |

Other labels remain unchanged. Stated percentages are separate numeric fields and missing percentages are unknown. The snail grouping supports marketing comparison, not chemical identity. Peptide, Peptides, Peptide Blend, 6 Peptide Complex and Ceramide and Peptide Complex remain distinct.

## Claim category rule

Assign one main category per exact product statement. Prioritize the heading's main benefit, use description for ambiguity, and choose the first explicit benefit when equally weighted benefits share one bullet. For example, “Hydrating cleanse without stripping” → Cleansing; “Deep hydration, fresh glow” → Hydration; “Plump, glowing skin” → Plumping. This means category counts do not include all secondary moisture/glow references.

Usage timing and Dermatologist testing remain in evidence and membership, but are excluded from the skin-benefit chart. Derm Tested records a brand testing statement, not independently verified efficacy.

## Historical tables

`ingredients.csv`: 346 full-formula rows keyed by product_id + ingredient_position, preserving original and standardized names. `product_claims.csv`: 41 older product/claim/category assignments, including multiple categories per statement. These are distinct from the new 41-row category membership table. The older 11-product Hydration claim count and the newer 7-product count use different source coverage and category rules.

## Source sections and timing

COSRX cleanser/toner: Details > Benefits and Ingredients > Key Ingredients. COSRX cream/serum: Concerns & Benefits table. LANEIGE: Summary Benefits icons; ingredient text/labels from Summary, except Cream Skin ingredients from expanded Benefits. The closed expanded benefit panels for other LANEIGE products were not inferred.

Page processing timestamps are November 4, 2026; they are not evidence that historical reviews were captured that day. The earlier collection month has conflicting September/October notes. November positioning can differ from historical copy/formulas. COSRX serum bundle and LANEIGE cream Matin Kim variant source mappings remain caveats. Screenshot files remain local; publication uses transcribed text, not original screenshot binaries.
