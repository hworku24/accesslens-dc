# Sprint 4: QA/QC deliverables


## Task 4.1: Disagreement adjudication

- Build the five-case inventory disagreement review.
- Show source views, target-centered crops, and capture dates.
- Keep model errors separate from inventory history questions.
- Require a category and written reason for every inventory case.
- Preserve unresolved historical cause when current imagery is the only evidence.

**Done when:** the exported adjudication file validates and the final split table regenerates.

## Task 4.2: Screening cost analysis

- Treat `ramp_absent` as the field-review target.
- Count wasted visits as false positives.
- Count missed absent ramps as false negatives.
- Report 1x, 5x, and 10x false-negative cost scenarios.
- Keep abstentions visible and state how they are routed.

**Done when:** one script writes the cost table from resolved labels and cached predictions.

## Task 4.3: Memo and project walkthrough

- Add the adjudication split and cost table.
- Add build, buy, and data-collection options.
- Add licensing, limits, and a clear ship decision.
- Write five short stakeholder bullets and two failure-analysis answers.
- Check every external citation in a browser.

**Done when:** the memo stays under six pages, the project walkthrough is ready, and all tests pass.
