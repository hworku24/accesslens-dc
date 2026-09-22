# Sprint 5 development readiness


## Development batch

- Candidates: 72
- Records with Mapillary API coverage: 65
- Records with downloaded images: 61
- Downloaded source images: 121
- Source images passing the provisional source gate: 115
- Target crops built: 95
- Target crops passing the frozen crop gate: 88
- Records with at least one eligible target crop: 55

The Sprint 5 target of at least 50 usable development records is met.

## Evidence outcomes

| Outcome | Records |
| --- | ---: |
| At least one eligible target crop | 55 |
| No Mapillary API coverage | 7 |
| Coverage metadata but no saved thumbnail | 4 |
| Saved image but no crop passed the gate | 6 |

All 72 records remain in the blind labeling batch. Records without eligible evidence
receive `cannot_determine`; they are included in coverage and abstention reporting.

## Usable records by study area

| Study area | Usable | Selected |
| --- | ---: | ---: |
| anacostia fairlawn | 18 | 24 |
| columbia heights petworth | 18 | 24 |
| navy yard capitol riverfront | 19 | 24 |

## Usable records by inventory condition

| Inventory condition | Usable | Selected |
| --- | ---: | ---: |
| Fair | 14 | 18 |
| Good | 16 | 18 |
| Missing | 11 | 18 |
| Non-Compliant | 14 | 18 |

## Separation rule

- Development imagery was collected and processed.
- Held-out coverage metadata was queried.
- Held-out thumbnails were not downloaded or opened.
- Preprocessing and decision settings must be committed before held-out image access.

## Labeling artifact

Open `outputs/scaleup_development_labeling_app.html` through the local server.
The interface hides the historical inventory condition and saves progress in browser storage.
Export is blocked until every record has a truth label and evidence-quality fields.
