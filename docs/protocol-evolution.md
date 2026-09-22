# Protocol evolution

`eval_protocol.md` is the frozen version 1.0 design written before real model scoring. It is
retained unchanged so the original evaluation intent remains auditable.

The implementation evolved in three stages:

1. **Coverage candidate pool.** The repository generated 144 seeded candidates across three
   study areas and four inventory conditions. This was a coverage-exploration pool, not the
   final labeled evaluation set. The frozen protocol's 120-point, two-area target therefore
   should not be read as the size of the later coverage-candidate pool.
2. **Initial pilot.** A balanced 12-record pilot, one record per area-by-condition stratum,
   was used to test imagery collection, labeling, abstention, and cross-source model transfer.
   The pilot remained intentionally small and its uncertainty is reported explicitly.
3. **Scale-up evaluation.** After the pilot, the project froze a separate 72-record
   development split and 24-record held-out split. All 12 pilot records were excluded from
   both. Development imagery and preprocessing can be inspected before settings are frozen;
   held-out thumbnails remain sealed until the development decision is committed.

The original protocol is not rewritten after results. Later sampling and evaluation choices
are documented here and in `PROJECT_STATUS.md`, `docs/sprint5-plan.md`, and the split manifest
under `data/processed/`.
