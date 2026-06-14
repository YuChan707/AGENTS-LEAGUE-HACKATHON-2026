# dtos

Domain entities as **Marshmallow schemas** — the shared contract between
`data_ingestor`, `data_processor` and `backend`. Validate with `.load()` and
serialize with `.dump()`; do not pass loose dicts around the code.

## Modules

| File | Entities |
|---|---|
| `data_ingestors.py` | RAW data + behavior model: `Location`, `LocationStatistics`, `DemographicGroup`, `BehaviorFormula`, `FactorModifier`, `FieldBehaviorGroup`, `GroupBehaviorProfile`, `MetricRange` + vocabularies (`GENDERS`, `INCOME_BRACKETS`, `FIELD_DOMAINS`, `BEHAVIOR_METRICS`, …) |
| `data_processors.py` | Output: `AudienceSegment`, `ProjectAsset`, `ReactionProfile` |
| `audience.py`, `analytics.py`, `reports.py` | Audience, analytics and reports |
| `ENTIDADES.txt` | Readable dictionary of all entities |

## Important note

There is a **divergent copy** in [`../data_ingestor/dtos/`](../data_ingestor/dtos/):
the `data_ingestor` is self-contained and uses its own; `data_processor` and `backend`
use **this** one (root), which is the source of truth for behavior modeling.
If a change must apply to both, it has to be reflected in the two copies.
