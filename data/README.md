# Local data contract

Actual product/review extracts are excluded from GitHub. Do not upload review text, reviewer details or raw page dumps. Restore your own local snapshot before executing the review pipeline.

| Stage | Local folder | Files |
| --- | --- | --- |
| 01–02 collection | data/processed/product-or-brand-folder/ | products, reviews, ingredients, review_skin_concerns CSVs |
| 02 combined | data/processed/all_products/ | Same four canonical filenames |
| 03 cleaning | data/cleaned/all_products/ | Same four canonical filenames, standardized columns |
| 04 exploration | data/analysis/ | Aggregates, review windows and local case studies |
| 05 themes | data/tableau/ | products.csv, reviews.csv, ingredients.csv, review_skin_concerns.csv, review_themes.csv; optional historical product_claims.csv |
| 06 positioning | data/tableau_key_ingredients_claims/timestamp/ | key_ingredient_evidence.csv, claim_evidence.csv, product_key_ingredients.csv, product_claim_categories.csv and run manifest |

Notebook 06 requires products.csv for validation. Set KBEAUTY_PRODUCTS_CSV to its location if needed. It defaults to embedded November positioning, requiring no review files or web request. Original 01–05 export paths may overwrite local files; run on a copy. A later 05 run does not incorporate 06's updated coding into old products.key_benefits: those fields remain historical. Use the evidence and membership tables for the current positioning.

For local final validation, place canonical files together, or use the original author filenames: products (3).csv, reviews (4).csv, ingredients (2).csv, product_claims (3).csv. The four new export names have no numeric suffix. Preserve originals; renaming is not required.

All IDs are text. Empty descriptions and percentages are unknown/not shown, never zero or inferred absence. No full Tableau workbook is distributed; the published dashboard is linked in README.
