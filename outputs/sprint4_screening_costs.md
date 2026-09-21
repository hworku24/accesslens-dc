# Sprint 4: screening cost analysis


## Operating rule

A resolved `ramp_absent` record needs field review. A `ramp_absent` model decision or
model abstention is routed to field review. A false positive wastes a field visit. A
false negative misses an absent ramp. The cost units below are illustrative ratios, not
dollar estimates.

## Screening outcomes

| Predictor | Field reviews | Review rate | True flags | Wasted visits | Missed absent ramps | Abstentions |
|---|---:|---:|---:|---:|---:|---:|
| DDOT 2016 inventory baseline | 2/9 | 22.2% | 2 | 0 | 5 | 0 |
| Project Sidewalk source-view model | 9/9 | 100.0% | 7 | 2 | 0 | 8 |
| Project Sidewalk target-centered model | 4/9 | 44.4% | 2 | 2 | 5 | 2 |

## Cost sensitivity

| Predictor | Miss cost | Weighted cost | Cost per record |
|---|---:|---:|---:|
| DDOT 2016 inventory baseline | 1x | 5 | 0.56 |
| DDOT 2016 inventory baseline | 5x | 25 | 2.78 |
| DDOT 2016 inventory baseline | 10x | 50 | 5.56 |
| Project Sidewalk source-view model | 1x | 2 | 0.22 |
| Project Sidewalk source-view model | 5x | 2 | 0.22 |
| Project Sidewalk source-view model | 10x | 2 | 0.22 |
| Project Sidewalk target-centered model | 1x | 7 | 0.78 |
| Project Sidewalk target-centered model | 5x | 27 | 3.00 |
| Project Sidewalk target-centered model | 10x | 52 | 5.78 |

## Decision

The source-view model avoids missed absent ramps only by sending every scorable record
to field review. The target-centered model reduces field visits but misses five of the
seven absent ramps. The inventory baseline also misses five. None of the tested policies
supports automated clearance on this pilot. Use the workflow to organize evidence and
human review while collecting a larger labeled sample for model selection or training.
