# Target-crop adjudication protocol

Version: 1.0  
Frozen: 2026-09-01, before the second-pass labels were collected

## Purpose

Target-centered crops materially change the evidence shown to the human reviewer. The
first pass used full source images, some of which placed the inventory point near the
edge of the frame or outside the useful view. The second pass therefore measures whether
the human truth label changes when the target location is centered.

## Blind-review controls

- The second-pass interface shows only target-centered crops.
- The historical DDOT condition and first-pass label remain hidden.
- A separate browser storage key prevents first-pass answers from appearing.
- All 12 records remain in the pass, including records with no valid crop.
- A record with no valid crop must be labeled `cannot_determine`.
- The raw export is preserved before any reconciliation.

## Reconciliation rule

Before comparison, a presence or absence label supported by no image or by evidence
marked `unusable` becomes `cannot_determine`.

1. If both passes agree, retain the shared label.
2. If one pass is scorable and the other is `cannot_determine`, provisionally retain the
   scorable label and record which evidence pass supported it.
3. If both passes are `cannot_determine`, retain `cannot_determine`.
4. If one pass says `ramp_present` and the other says `ramp_absent`, leave the record
   unresolved. Review both evidence sets and write a record-specific adjudication reason.

Direct label conflicts cannot be resolved from model output, historical inventory
condition, or whichever choice produces the higher score.

## Reporting

Report first-pass and second-pass label counts, pass agreement, the number of direct
conflicts, every adjudication reason, and final metrics against the resolved truth set.
The 12-record pilot remains a workflow demonstration with wide uncertainty, not a
general performance estimate.
