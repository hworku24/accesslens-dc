# Curb-ramp image labeling guide

Label the visible corner using the image evidence only. Keep the 2016 DDOT condition
hidden while making the first judgment when practical.

## Truth label

- `ramp_present`: a curb ramp or blended transition is clearly visible at the target corner.
- `ramp_absent`: the target corner is visible enough to judge and no ramp is present.
- `cannot_determine`: the target corner is outside the view, too distant, blocked, blurred,
  too dark, or geometrically ambiguous.

If multiple images show the same inventory point, use `ramp_present` when any usable image
clearly shows a ramp. Use `cannot_determine` when none of the images supports a reliable
presence or absence decision.

## Supporting fields

`image_quality`:

- `good`
- `usable`
- `poor`
- `unusable`

`occlusion`:

- `none`
- `partial`
- `severe`
- `unknown`

`detectable_warning`:

- `visible`
- `not_visible`
- `cannot_determine`

The detectable-warning field is descriptive. It is not a compliance finding.

## Relabel check

After the first pass, select 25 records using the frozen random seed, wait at least one
hour, and label them again without viewing the first labels. Retain both passes and record
the final resolved label for any disagreement.

