# Sprint 5: scale-up dataset


## Task 5.1: Freeze the split

Status: complete.

- Exclude all 12 pilot records.
- Select six development and two held-out records per area-by-condition stratum.
- Use a fixed seed and sorted source rows.
- Record source hashes and the held-out file hash.
- Keep held-out imagery outside labeling and threshold work.

**Done when:** 72 development and 24 held-out records are disjoint, balanced, and reproducible.

## Task 5.2: Check free imagery coverage

Status: complete.

- Query Mapillary coverage for both splits.
- Record pano and non-pano counts plus capture-date ranges.
- Do not open held-out imagery during development.
- Report coverage by area, condition, and split.

**Done when:** coverage files contain one row per candidate and no API credential is stored.

## Task 5.3: Build the development labeling batch

Status: complete. Blind labeling remains.

- Collect up to two ranked images per covered development record.
- Run the OpenCV quality audit.
- Build target-centered crops with retained hashes.
- Generate a blind labeling interface for development records only.

**Done when:** at least 50 usable development records are ready for labeling.

## Task 5.4: Hold-out gate

Status: pending development labels and settings freeze.

- Freeze preprocessing and model thresholds using development records only.
- Record the development decision and code revision.
- Open held-out imagery after the gate is committed.

**Done when:** the held-out gate records the code commit and frozen settings.
