# DDOT ADA curb-ramp inventory audit

Audit timestamp: `2026-09-01T18:32:15.365592+00:00`  
Source file: `data/raw/ddot_ada_curb_ramps.geojson`  
Source URL: <https://opendata.arcgis.com/api/v3/datasets/f94e9628f2604e6e9a25fd8c496b4c6c_3/downloads/data?format=geojson&spatialRefId=4326>  
SHA256: `f107d0b87656c73559235b23a21951c6811de5744ffe9b0428bca36bb998819b`

## Headline findings

- Feature count: 34,859
- Geometry types: {'Point': 34859}
- Coordinate dimensions: {'3': 34859}
- Inspection years: {'2016': 34859}
- Conditions: {'Non-Compliant': 16139, 'Good': 11020, 'Missing': 3885, 'Fair': 3638, '<null>': 177}
- Status codes: {'1': 34348, '5': 353, '2': 82, '<null>': 40, '3': 26, '4': 7, '6': 3}

## Field-quality findings

- `GIS_ID` nulls: 0
- `GIS_ID` duplicate non-null values: 0
- `INTERSECTION_ID` nulls: 34,859
- `INTERSECTION_ID` cannot support intersection grouping in this download.
- Estimated improvement years: {'2030': 34859}
- The improvement-year field has one value across the dataset and cannot verify individual construction dates.
- Last-edited dates: {'2024-06-27T20:35:19Z': 34859}
- A file edit date does not establish a new field inspection date.
- `STATUS` is retained as an undocumented code and excluded from semantic claims.

## Bounds

```json
{
  "min_longitude": -77.11437732957404,
  "min_latitude": 38.806962838280626,
  "max_longitude": -76.91026192702377,
  "max_latitude": 38.99224750124994
}
```

## Interpretation

All records report a 2016 inspection year. The dataset is suitable as a historical inventory baseline. Current presence and condition must be established from newer evidence. The project will score the inventory as one predictor against hand-labeled current imagery.
