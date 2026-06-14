# data_processor

Converts the real RAW data (Census, by `zip_code`) into **synthetic online
behavior audience groups**, using a **dockerized Llama 3B** via Dapr and
grounding from **Foundry IQ**. The outputs are **scores in ranges**
(min / expected / max) of reaction.

## Pipeline (per location)

1. **Statistical model** -> `list[BehaviorFormula]`: how each behavior metric
   changes by gender, age, income/class, ethnicity and education.
2. **Field/topic groups** -> `list[FieldBehaviorGroup]`: technology,
   entertainment, education, health, finance, politics, family.
3. **Varied groups (automated prompt)** -> `GroupBehaviorProfile`: combines
   factors and delivers the levels as ranges = the audience scores.
4. **Consolidated spec + aggregated scores** -> persisted per zip.

## Contents

| Path | What it is |
|---|---|
| `__init__.py` | Pipeline orchestration (`run`, `process_location`, `generate`, varied groups, score aggregation) |
| `__main__.py` | CLI (`python -m data_processor`) |
| `prompts.py` | Prompts as **entities** `PromptSpec` (`details`, `description_input`, `expected_output`, validator schema, mock) |
| `llm_client.py` | `LlamaClient`: Dapr transport -> HTTP (OpenAI-compatible) -> mock |
| `foundry_iq.py` | Grounding layer: remote Foundry IQ retrieval or local evidence (real Census) |
| `persistence.py` | JSON persistence (seam for Postgres/Chroma/Dapr state) |
| `build_profiles.py`, `fetch_data_commons.py` | Profile / Data Commons utilities |
| `components/` | Dapr: `conversation-llama.yaml` (model) + `statestore.yaml` (Postgres) |

## How to run

```bash
python -m data_processor                 # auto: dapr -> http -> mock
python -m data_processor --transport mock --groups 6   # offline demo
# "Llama via Dapr agents" path:
dapr run --app-id data-processor --resources-path data_processor/components -- \
  python -m data_processor --transport dapr
```

Variables: `LLM_TRANSPORT`, `LLAMA_MODEL`, `LLAMA_BASE_URL`, `DAPR_LLM_COMPONENT`,
`FOUNDRY_IQ_*`. See the diagram in [`../docs/workflow.md`](../docs/workflow.md).
