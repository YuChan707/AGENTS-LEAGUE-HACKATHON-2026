# OnLooker — Workflow del pipeline de audiencia sintetica

Flujo de extremo a extremo: de la data real del Census (NY) a grupos de
audiencia sintetica con scores, anclados en evidencia real (Foundry IQ) y
generados por un Llama 3B dockerizado via Dapr.

## 1. Vista general

```mermaid
flowchart TD
    subgraph INGEST["data_ingestor (data CRUDA real)"]
        CSV["nyc_zip_codes.csv<br/>(zip codes NY)"]
        CENSUS["US Census ACS5 API<br/>(CENSUS_DATA_API)"]
        BUILD["build_location_metadata<br/>+ Marshmallow Location.load()"]
        PERSIST_LOC["persist_locations()"]
        LOCJSON[("data_ingestor/data/locations/<br/>&lt;zip&gt;.json + _index.json")]
        CSV --> BUILD
        CENSUS --> BUILD
        BUILD --> PERSIST_LOC --> LOCJSON
    end

    subgraph PROC["data_processor (data SINTETICA $$)"]
        LOAD["load_locations()"]
        P1["1. Modelo estadistico<br/>BEHAVIOR_MODEL_PROMPT<br/>-> list[BehaviorFormula]"]
        P2["2. Grupos por campo/tema<br/>FIELD_GROUPS_PROMPT<br/>-> list[FieldBehaviorGroup]"]
        P3["3. Grupos variados (automatico)<br/>build_varied_group_definitions<br/>+ GROUP_PROFILE_PROMPT<br/>-> GroupBehaviorProfile"]
        P4["4. summarize_scores()<br/>spec consolidada + audience_scores"]
        SAVE["save_processor_output / save_audience_specs"]
        OUTJSON[("data_processor/output/<br/>behavior_model / field_groups /<br/>group_profiles / audience_specs")]
        LOAD --> P1 --> P2 --> P3 --> P4 --> SAVE --> OUTJSON
    end

    subgraph LLM["Acceso al modelo + grounding"]
        FIQ["FoundryIQ.ground()<br/>evidencia real (Census) /<br/>retrieval remoto"]
        CLIENT["LlamaClient<br/>auto: dapr -> http -> mock"]
        DAPR["Dapr Conversation API<br/>component: llama"]
        LLAMA["Llama 3B dockerizado<br/>(OpenAI-compatible)"]
        FIQ --> CLIENT
        CLIENT --> DAPR --> LLAMA
    end

    LOCJSON --> LOAD
    P1 -.usa.-> CLIENT
    P2 -.usa.-> CLIENT
    P3 -.usa.-> CLIENT
    OUTJSON --> UI["UI OnLooker /<br/>backend (reacciones a un asset)"]
```

## 2. Generacion validada (un PromptSpec)

Cada paso de generacion pasa por el mismo ciclo, con validacion dura contra el
schema y degradacion a mock si no hay modelo.

```mermaid
flowchart TD
    START["generate(PromptSpec)"]
    GROUND["FoundryIQ.ground(query, stats)<br/>anexa evidencia real al prompt"]
    BUILDP["spec.build() -> {model, system, user}"]
    ISMOCK{"transport == mock<br/>o LLM no disponible?"}
    CALL["LlamaClient.complete()"]
    JSON["extract_json(respuesta)"]
    VALID{"spec.validate()<br/>(Marshmallow .load)"}
    RETRY{"reintento &lt; 2?"}
    MOCK["spec.mock() -> fixture valido"]
    OK["entidad validada"]

    START --> GROUND --> BUILDP --> ISMOCK
    ISMOCK -- no --> CALL --> JSON --> VALID
    VALID -- ok --> OK
    VALID -- falla --> RETRY
    RETRY -- si --> CALL
    RETRY -- no --> MOCK
    ISMOCK -- si --> MOCK
    MOCK --> VALID2["spec.validate() del mock"] --> OK
```

## 3. Modelo de datos (entidades clave)

```mermaid
flowchart LR
    LOC["Location<br/>(+ LocationStatistics)"]
    BF["BehaviorFormula<br/>(baseline + FactorModifier[])"]
    FG["FieldBehaviorGroup<br/>(tech/edu/entret/salud...)"]
    GP["GroupBehaviorProfile<br/>(behavior_ranges = MetricRange[])"]
    SPEC["audience_spec<br/>(audience_scores agregados)"]
    RP["ReactionProfile<br/>(scores ante un asset)"]

    LOC --> BF
    LOC --> FG
    LOC --> GP
    BF --> GP
    BF --> FG
    GP --> SPEC
    FG --> SPEC
    GP --> RP
    SPEC --> RP
```

## Como correr

```bash
# 1) Data cruda real -> persistida por zip_code
python -m data_ingestor.main                 # requiere CENSUS_DATA_API en .env

# 2) Audiencia sintetica (auto: dapr -> http -> mock)
python -m data_processor

# Camino "Llama via Dapr agents"
dapr run --app-id data-processor \
         --resources-path data_processor/components \
         -- python -m data_processor --transport dapr

# Demo offline (sin modelo)
python -m data_processor --transport mock
```
