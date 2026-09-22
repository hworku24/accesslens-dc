# AccessLens DC Sprint 4 project walkthrough

## Headline result

DDOT's source inventory contains 34,859 curb-ramp records from a 2016 assessment. Target-centered
crops raised Project Sidewalk model coverage from 11.1 percent to 77.8 percent on the resolved
pilot set, but only one of seven answered predictions was correct. The evidence workflow remains
useful for review and provenance, while the tested model is not suitable for automated clearance.

## Disagreement review

Five current human labels disagreed with the historical inventory. Every available image for those
records was captured after 2016. The evidence supports the current image label but cannot establish
whether the difference reflects later physical change or an error in the 2016 inventory, so all five
historical causes remain unresolved.

## Image limits

PROWAG includes dimensional requirements such as slope, width, grade-break geometry, and detectable
warning criteria. A single uncalibrated street image cannot establish those measurements. AccessLens
therefore limits image-based claims to visible presence or absence, evidence sufficiency, and records
that warrant additional review.

## Model-selection implication

The free local validator transferred poorly to Mapillary imagery and missed five absent ramps under
the field-review policy. A next model comparison should use the same development and held-out records
to evaluate a target-domain classifier or another documented workflow before any deployment decision.

## Failure analysis

The first model run answered only one of nine scorable records because many downloaded views did not
center the target. Directional crops and panorama projections raised coverage to seven of nine. Accuracy
then fell to one of seven. That separated two failure modes: view eligibility and cross-source model
transfer. The failed result, thresholds, and evidence required for the next evaluation are retained.

## Next evaluation changes

The scale-up phase uses separate development and held-out records, keeps evidence failures as measured
outcomes, adds a second reviewer, and freezes preprocessing and decision settings before held-out image
access. A larger target-domain development set will support model selection or training without tuning
on the final held-out split.

## One-sentence project description

AccessLens DC is a curb-ramp inventory QA workflow that joins DDOT records with licensed Mapillary
imagery, audits image and model quality, measures abstention and transfer failure, and routes uncertain
records to documented human review.
