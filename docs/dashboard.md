# Tableau dashboard guide

[Published dashboard](https://public.tableau.com/views/ExploringK-BeautysAppeal/Dashboard1).

Use logical relationships, with Products at the center:

- Products.product_id → product_key_ingredients.product_id
- Products.product_id → product_claim_categories.product_id
- Products.product_id → Reviews.product_id
- Reviews.review_id → review_themes.review_id
- Reviews.review_id → review_skin_concerns.review_id

Keep evidence available for local details; do not physically join all child tables. Count distinct product IDs from the relevant membership table, and distinct review IDs from the relevant review table.

## Views

1. **Ingredients:** packed bubbles, standardized label on Label, COUNTD(product_id) on Size. Keep five labels with full-sample product count ≥2. No numbers inside bubbles.
2. **Benefits:** packed bubbles, category on Label, COUNTD(product_id) on Size. Skin benefit only, full-sample count ≥2. No numbers inside bubbles.
3. **Themes:** horizontal bars, theme against COUNTD(review_id) from review_themes. Mentions overlap; 3,566 eligible English reviews provide context.
4. **Hydration:** top three product rates, numerator = distinct Hydration theme review IDs, denominator = all eligible review IDs for that product, including untagged reviews. Same zero baseline across bars. Use percentages and tagged/eligible counts in tooltips.

KPI cards: COUNTD(review_id) = 3,600; COUNTD(product_id) = 12; COUNTD(brand) = 3. Do not sum child-table row counts for these measures.

## Hydration calculation

The local validation script computes the denominator directly from Reviews. In Tableau, use the Reviews ID for the denominator and the Review Themes ID for the numerator. Example aliases below distinguish otherwise identical field names:

```tableau
// Hydration Mention: Review ID — Themes comes from review_themes
IF [Theme] = "Hydration" THEN [Review ID — Themes] END
```

```tableau
// Eligible Reviews per Product: Product ID is from Products
{ FIXED [Product ID] :
    COUNTD(IF LOWER(STR([Theme Analysis Eligible])) = "true"
           THEN [Review ID — All Reviews] END)
}
```

```tableau
IF MIN([Eligible Reviews per Product]) > 0 THEN
    COUNTD([Hydration Mention]) / MIN([Eligible Reviews per Product])
END
```

Do not filter Theme to Hydration before calculating denominators. If review-level filters are introduced later, review FIXED-LOD filter behavior and revalidate matching numerators/denominators. The published static comparison uses the saved full snapshot.

## Reading the screenshot

The supplied final PNG is reproduced unchanged. It has no numeric labels inside bubbles. Its hydration bars omit visible axes/percentages, so consult the interactive tooltips and README table for exact values. Light-bubble label contrast and the broad November footer are presentation limitations: November refers to the positioning/project update, not verified original review collection timing. No satisfaction, effectiveness or causal purchase conclusion follows from these views.
