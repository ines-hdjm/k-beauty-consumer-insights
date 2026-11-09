"""Validate local final CSVs without printing review text or reviewer details."""
from pathlib import Path
import argparse
import csv
import json
from collections import Counter


FILES = {
    'products': ('products.csv', 'products (3).csv'),
    'reviews': ('reviews.csv', 'reviews (4).csv'),
    'review_themes': ('review_themes.csv',),
    'review_skin_concerns': ('review_skin_concerns.csv',),
    'key_ingredient_evidence': ('key_ingredient_evidence.csv',),
    'claim_evidence': ('claim_evidence.csv',),
    'product_key_ingredients': ('product_key_ingredients.csv',),
    'product_claim_categories': ('product_claim_categories.csv',),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_key(rows, fields, name):
    keys = [tuple(row[field] for field in fields) for row in rows]
    require(all(all(value.strip() for value in key) for key in keys), f'Blank key: {name}')
    require(len(keys) == len(set(keys)), f'Duplicate key: {name}')


def validate(folder):
    tables = {}
    for name, filenames in FILES.items():
        found = [folder / filename for filename in filenames if (folder / filename).is_file()]
        require(len(found) == 1, f'Provide exactly one recognized file for {name}: {filenames}')
        with found[0].open(encoding='utf-8-sig', newline='') as handle:
            tables[name] = list(csv.DictReader(handle))
    expected = dict(zip(FILES, [12, 3600, 3374, 4277, 37, 44, 36, 41]))
    require({k: len(v) for k, v in tables.items()} == expected, 'Snapshot row counts differ; inspect rather than dropping rows')
    keys = {
        'products': ['product_id'], 'reviews': ['review_id'],
        'review_themes': ['review_id', 'theme'],
        'review_skin_concerns': ['review_id', 'skin_concern_standardized'],
        'key_ingredient_evidence': ['product_id', 'key_ingredient_name'],
        'claim_evidence': ['product_id', 'claim_text'],
        'product_key_ingredients': ['product_id', 'key_ingredient_standardized'],
        'product_claim_categories': ['product_id', 'claim_category', 'claim_type'],
    }
    for name, fields in keys.items():
        unique_key(tables[name], fields, name)
    products = {r['product_id']: r for r in tables['products']}
    reviews = {r['review_id']: r for r in tables['reviews']}
    require(len({r['brand'] for r in products.values()}) == 3, 'Unexpected brand count')
    for name in ['reviews', 'key_ingredient_evidence', 'claim_evidence', 'product_key_ingredients', 'product_claim_categories']:
        require(all(r['product_id'] in products for r in tables[name]), f'Orphan products: {name}')
        require({r['product_id'] for r in tables[name]} == set(products), f'Missing product coverage: {name}')
    for name in ['review_themes', 'review_skin_concerns']:
        require(all(r['review_id'] in reviews for r in tables[name]), f'Orphan reviews: {name}')
    require(all(r['theme_analysis_eligible'].casefold() in ['true', 'false'] for r in reviews.values()), 'Invalid eligibility flag')
    eligible = {rid for rid, r in reviews.items() if r['theme_analysis_eligible'].casefold() == 'true'}
    require(len(eligible) == 3566, 'Eligibility count mismatch')
    require(all(r['review_id'] in eligible for r in tables['review_themes']), 'Ineligible review tagged')
    require(all(r['rating'] in ['1', '2', '3', '4', '5'] for r in reviews.values()), 'Invalid rating')
    for name in ['key_ingredient_evidence', 'claim_evidence']:
        require(all(r['source_url'].startswith('https://') and r['processed_at_utc'] for r in tables[name]), f'Missing source metadata: {name}')
    require(all(r['claim_category'].strip() and r['claim_type'].strip() for r in tables['claim_evidence']), 'Uncoded claim')
    ingredient_pairs = {(r['product_id'], r['key_ingredient_standardized']) for r in tables['key_ingredient_evidence']}
    require(ingredient_pairs == {(r['product_id'], r['key_ingredient_standardized']) for r in tables['product_key_ingredients']}, 'Ingredient membership differs from evidence')
    claim_pairs = {(r['product_id'], r['claim_category'], r['claim_type']) for r in tables['claim_evidence']}
    require(claim_pairs == {(r['product_id'], r['claim_category'], r['claim_type']) for r in tables['product_claim_categories']}, 'Claim membership differs from evidence')
    require(Counter(r['claim_type'] for r in tables['claim_evidence']) == {'Skin benefit': 36, 'Usage': 4, 'Testing statement': 4}, 'Claim type mismatch')
    ingredient_counts = Counter(r['key_ingredient_standardized'] for r in tables['product_key_ingredients'])
    require({k: v for k, v in ingredient_counts.items() if v >= 2} == {'Niacinamide': 4, 'Blue Hyaluronic Acid': 3, 'Ginseng Root Water': 2, 'Propolis Extract': 2, 'Squalane': 2}, 'Ingredient chart mismatch')
    benefit_counts = Counter(r['claim_category'] for r in tables['product_claim_categories'] if r['claim_type'] == 'Skin benefit')
    require({k: v for k, v in benefit_counts.items() if v >= 2} == {'Hydration': 7, 'Skin texture / smoothness': 5, 'Barrier support': 4, 'Oil–moisture balance': 3, 'Radiance / glow': 3, 'Soothing': 3, 'Cleansing': 2}, 'Benefit chart mismatch')
    theme_counts = Counter(r['theme'] for r in tables['review_themes'])
    require(theme_counts == {'Hydration': 1481, 'Texture / feel': 756, 'Sensitivity / breakouts': 702, 'Packaging / format': 332, 'Price / value': 103}, 'Theme count mismatch')
    hydration = {r['review_id'] for r in tables['review_themes'] if r['theme'] == 'Hydration'}
    rates = []
    for pid in products:
        ids = {rid for rid in eligible if reviews[rid]['product_id'] == pid}
        require(bool(ids), f'No eligible denominator: {pid}')
        matched = len(ids & hydration)
        rates.append({'product_id': pid, 'tagged': matched, 'eligible': len(ids), 'rate': matched / len(ids)})
    rates.sort(key=lambda r: (-r['rate'], r['product_id']))
    require([(r['product_id'], r['tagged'], r['eligible']) for r in rates[:3]] == [('LANEIGE_MOISTURIZER_01', 242, 297), ('LANEIGE_TONER_01', 183, 297), ('LANEIGE_CLEANSER_01', 166, 300)], 'Hydration ranking mismatch')
    return {'rows': expected, 'eligible_reviews': len(eligible), 'theme_counts': dict(theme_counts), 'top_hydration': rates[:3], 'validation': 'passed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.data_dir), indent=2))
