# Proposal: ingredient and claim model v2

Status: design for review, not an executed migration. Reviewed 2026-11-04.

## Evidence and limits

- [K-beauty README at reviewed commit](https://github.com/ines-hdjm/k-beauty-consumer-insights/blob/35cc3d9c00971b49860c604b2990731c11c137c3/README.md).
- [Sephora collection](https://github.com/ines-hdjm/sephora-lip-care-consumer-insights/blob/1105e8521ad62f9108bdaa8c20e66dce496eb8ed/notebooks/01_Data_Collection.ipynb),
  [cleaning](https://github.com/ines-hdjm/sephora-lip-care-consumer-insights/blob/1105e8521ad62f9108bdaa8c20e66dce496eb8ed/notebooks/02_Data_Cleaning_Modeling.ipynb),
  [enrichment](https://github.com/ines-hdjm/sephora-lip-care-consumer-insights/blob/1105e8521ad62f9108bdaa8c20e66dce496eb8ed/notebooks/03_Product_Enrichment.ipynb),
  [final database](https://github.com/ines-hdjm/sephora-lip-care-consumer-insights/blob/1105e8521ad62f9108bdaa8c20e66dce496eb8ed/notebooks/04_Final_Database.ipynb).

The K-beauty main tree publishes only README, requirements, .gitignore, and
a dashboard image. Its notebooks and CSVs are described but absent. Therefore,
K-beauty behavior below is documented behavior, not verified implementation.
Sephora publishes notebooks but excludes real extracts and final data. Neither
project's reported row counts were independently reproduced.

## Comparison

| Area | K-beauty, documented | Sephora, inspected code | Recommendation |
| --- | --- | --- | --- |
| Ingredients | 346 ordered entries, keyed by product_id + ingredient_position; raw and standardized names | Ingredient lookup plus product_ingredients bridge with ingredient_order | Adopt a shared dictionary while retaining every occurrence and raw label |
| Claims | 41 product / claim_text / claim_category assignments; coding_method; original benefits and page sources retained | Claim lookup plus product_claims bridge; separate highlights lookup/bridge | Separate source statements from category coding; preserve K-beauty's category layer |
| Collection | Brand-specific pages; Okendo/Yotpo reviews; variant metadata where available | linkStore currentSku.ingredientDesc and highlights; claims fallback through product.claims, currentSku.claims, productHighlights | Use source-specific adapters; record which field was used |
| Cleaning | Formatting and label standardization, unknowns preserved; exact code unavailable | Ingredient disclaimer removal; comma splitting; literal-list or pipe parsing for claims/highlights | Retain raw blocks; parse conservatively and report ambiguity |
| Integrity | README reports key, pair, range, row-count and orphan checks | Uniqueness and product checks in enrichment; both sides of bridges checked in final notebook | Validate before publishing, with explicit failures and reconciliation reports |
| Provenance | Product-page sources and original benefits documented; collection month inconsistent | Enrichment raw rows lack source URL, collection time, raw HTML and field-path provenance | Immutable source records and per-run manifests; keep unknown historical dates unknown |

Sephora patterns to adapt with care:

- split_ingredients returns no entries for a nonempty single-ingredient string.
  It splits on every comma, including commas inside parentheses.
- Dropping duplicate product_id / ingredient_id pairs loses repeated occurrences
  and their positions. K-beauty's ordered-entry grain should be preserved.
- Sorted sequential lookup IDs can shift when new names are inserted. Use
  persistent assigned IDs or versioned mappings, not newly numbered lookups per run.
- Claim fallback can treat productHighlights as claims without recording the
  original field. Preserve statement type and source field separately.
- List parsing sorts and deduplicates values. That is acceptable for a derived
  membership table, but not as the only surviving source evidence.
- Final product-ID matching uses SKU/name dictionaries; ambiguous keys can
  overwrite matches. K-beauty's existing product IDs should remain unchanged.

## Proposed schema

CSV remains sufficient. This is a v2 export model alongside the existing tables,
not a requirement to introduce SQL. PK means unique and nonempty; FK must resolve.

| Table | Grain / key | Required fields and rules |
| --- | --- | --- |
| products | Existing product_id PK | Preserve existing IDs and attributes |
| source_records | One captured field/block, source_record_id PK | product_id FK, source_url, source_field, statement_type, raw_text, raw_sha256, collection_status, extraction_method, parser_version; collected_at_utc and variant_id nullable |
| ingredient_lists | One formula/list snapshot, ingredient_list_id PK | source_record_id FK unique, parse_status; source record identifies product and variant |
| ingredients | One conservative canonical label, ingredient_id PK | canonical_name, normalization_version; canonical names unique within normalization version |
| product_ingredients | One occurrence, PK ingredient_list_id + ingredient_position | ingredient_id FK, ingredient_name_raw; position positive integer, preserving original order and repeats |
| claims | One normalized source statement, claim_id PK | claim_text, normalization_version; unique normalized statement within version |
| product_claims | One statement occurrence, product_claim_id PK | source_record_id FK, claim_id FK, statement_position; unique source_record_id + statement_position |
| claim_categories | One analytical category, claim_category_id PK | category_name, definition, taxonomy_version |
| claim_codings | One coding assignment, claim_coding_id PK | product_claim_id FK, claim_category_id FK, coding_method, coding_version, validation_status; coded_at_utc and coder nullable |
| legacy_crosswalk | One original row, PK legacy_table + legacy_row_number + input_sha256 | New row identifier(s), mapping_status; retain original keys and category text |

source_records.statement_type distinguishes full_ingredient_list,
benefit_claim, and highlight. Unknown source fields or historical timestamps must
be null with an explicit provenance_status such as legacy_unknown; never invent
a capture date. raw_sha256 is SHA-256 of the exact UTF-8 raw_text, not the
normalized label. Keep a separate file checksum for original bytes.

A source record can have many claim occurrences. A claim occurrence can have
multiple category assignments. Different original statements must remain
separate occurrences even when they share a canonical claim.

The product is reached through ingredient_lists -> source_records or
product_claims -> source_records. Optional product_id convenience columns must
be validated against that path. Do not allow them to create conflicting joins.

## Extraction and normalization contract

1. Freeze existing local notebooks, original CSV bytes, and saved raw extracts.
   Record file SHA-256, relative path, run ID, code revision, configuration,
   dependency versions, and actual known collection dates in a manifest.
2. Prefer existing saved extracts. Migration does not require recollection.
   Recollection is a separate snapshot with a new run and source IDs.
3. Adapt each brand's saved structured field or HTML section independently.
   Store exact extracted text, field/selector, URL, product and available variant.
   Record found, missing, request_error, extraction_error, and ambiguous states;
   an empty list is not evidence that a formula has no ingredients.
4. For full ingredient lists, split only at top-level separators outside balanced
   parentheses/brackets. Preserve punctuation within tokens, token order, and
   repeats. Accept one nonempty token. Unbalanced delimiters, embedded headings,
   or unsupported structures require review rather than silent repair.
5. Use whitespace normalization and Unicode NFC for canonical labels. Retain
   original case/text separately; document any case-folding policy. Do not
   automatically equate water/aqua, botanical variants, salts, concentrations,
   or similar-looking names. Add reviewed aliases as a versioned mapping with
   rationale. Never infer ingredient presence from benefit copy.
6. Keep literal claims intact. Parse only a known list encoding for each adapter;
   do not guess that a pipe inside prose is a delimiter. Keep highlights separate.
   Claims describe brand messaging, not verified clinical outcomes.
7. Copy existing manual category assignments via the legacy crosswalk. Missing
   coding remains uncoded. Keep coding version and method; do not generate
   categories from ingredient names or convert review-theme mentions to claims.
8. Validate all candidate tables before making a complete run directory visible.
   Export to a fresh staging directory, then publish by renaming on the same
   filesystem. Refuse an existing output destination. No source overwrites.

## Migration and acceptance checks

The local K-beauty notebooks and CSV headers are needed to implement adapters.
Do not guess the missing columns from README examples.

- Validate nonempty keys, unique PKs, all FKs, product ownership, valid positions,
  and duplicate coding assignments. Use explicit exceptions, not only assert.
- Retain IDs as strings, including leading zeros; never normalize IDs through
  floating-point conversion. Reject conflicting product or variant mappings.
- Reconcile the documented 346 ingredient entries and 41 claim-category
  assignments against actual input counts. Report differences; do not force
  data to fit README counts.
- Prove each legacy ingredient row maps to exactly one occurrence, including
  duplicate ingredients at different positions. Compare raw names and order.
- Prove every original claim text, category assignment and coding method is
  retained. Canonical deduplication may reduce lookup rows, not source evidence.
- Check missing metadata counts before/after; unknown dates, variants and coding
  methods must stay unknown. Do not resolve the README's September/October
  collection discrepancy without original evidence.
- Test single ingredients, commas in parentheses, repeated ingredients,
  unbalanced delimiters, empty/missing fields, literal pipes, multilingual text,
  duplicate inputs, orphan keys, conflicting mappings and multiple categories.
- Verify a rerun on identical inputs/configuration produces identical IDs,
  ordered table contents and checksums, apart from declared run metadata.
- Keep malformed or ambiguous input in an exceptions report with source IDs.
  Block promotion while unresolved rows would be omitted or misinterpreted.
- Confirm reviews, review themes and product attributes have identical original
  file hashes; this migration concerns ingredient and claim modeling only.

## Tableau transition and rollback

Preserve the current six-table exports and published dashboard. Write candidate
exports to data/tableau_v2/<run_id>/ with a manifest and validation report.

Provide a compatibility view joining ingredient occurrences to their dictionary
and source product, retaining ingredient_position, ingredient_name and
ingredient_name_standardized. Provide another joining claim occurrences,
claims and claim_codings to recover product_id, claim_text, claim_category and
coding_method. Carry legacy row identifiers so exact source labels and
assignments can be reconstructed even when canonical labels are shared.

Do not replace existing CSVs until their complete headers and workbook
relationships have been inspected. Compare product counts, distinct ingredient
membership counts, claim-category product counts and filter behavior with the
current dashboard. Use Tableau relationships and distinct product/review counts:
flattening ingredients, claims and reviews into one join multiplies rows.

Rollback means reconnecting to the preserved original exports. Keep new
provenance and dictionary tables as additional artifacts; never rewrite the
historical snapshot or change the published research findings during migration.

## Suggested implementation order

1. Obtain the local notebooks 02, 03 and 05 plus products, ingredients,
   product_claims and any raw benefit/ingredient extracts. Keep third-party data
   local; only sanitized fixtures need to enter version control.
2. Verify actual headers, keys, raw fields and collection metadata; write the
   crosswalk and normalization specification against those files.
3. Implement pure transformation functions and source adapters, then the
   edge-case and reconciliation checks above.
4. Run against a copy of the historical snapshot, review exceptions, and export
   v2 plus compatibility views.
5. Review Tableau comparisons before a separate dashboard migration.

This proposal changes documentation only. No historical rows were migrated,
no collection was run, and no changes to existing results are claimed.
