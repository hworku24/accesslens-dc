# Proposed architecture

```text
Municipal inventory       Street imagery       Human labels
        |                       |                    |
        +-----------------------+--------------------+
                                |
                         Data validation
                                |
                 Detector / vision-language model
                                |
                    Structured prediction records
                                |
               Geospatial matching and evaluation
                     /                     \
              Metrics report          QA review queue
                     \                     /
                      Stakeholder decision
```

## AWS mapping

- S3 stores imagery, source inventories, labels, and model outputs.
- Lambda validates metadata and starts batch jobs for small workloads.
- A container task or managed model endpoint handles inference.
- A relational database with spatial support stores assets and review state.
- CloudWatch captures latency, failures, throughput, and model-health signals.

The local implementation keeps the interfaces explicit so each component can be moved
to a managed service without changing the evaluation policy.
