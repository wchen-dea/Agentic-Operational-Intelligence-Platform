# Business Metrics

This document distinguishes between:

- Implemented now: metrics currently emitted by code and available at `GET /metrics`.
- Planned: target metrics not yet emitted in code.

## Implemented now

These are emitted via `observability.evaluation.MetricsCollector` and tracked by `AgentPerformanceTracker` / `LLMEvaluator`.

### Agent performance

- `agent_duration_ms`
- `agent_executions_total`
- `agent_successes_total`
- `agent_failures_total`
- `agent_fallbacks_total`
- `agent_retries_total`

### LLM usage

- `llm_calls_total`
- `llm_call_duration_ms`
- `llm_input_tokens_total`
- `llm_output_tokens_total`

### Evaluation quality

- `eval_score`
- `eval_passed_total`
- `eval_failed_total`

## Planned metrics backlog

The following metrics are goals and require implementation in emitters/trackers before they appear in `/metrics`.

## Data freshness

- `kpi_event_lag_seconds`
- `source_topic_lag_records`
- `gold_table_update_latency_seconds`

## AI quality

- `answer_grounding_score` — via `LLMEvaluator._eval_groundedness()`
- `eval_relevance_score` — via `LLMEvaluator._eval_relevance()`
- `eval_persona_fit_score` — via `LLMEvaluator._eval_persona_fit()`
- `eval_conciseness_score` — via `LLMEvaluator._eval_conciseness()`
- `eval_actionability_score` — via `LLMEvaluator._eval_actionability()`
- `recommendation_acceptance_rate`
- `alert_precision_rate`
- `llm_judge_score` — via `LLMEvaluator.evaluate_with_llm()` (LLM-as-judge)

## Agent performance

- `agent_duration_ms` (per agent node, tracked by `AgentPerformanceTracker`)
- `agent_executions_total`
- `agent_successes_total`
- `agent_failures_total`
- `agent_fallbacks_total`
- `agent_retries_total`

## LLM usage

- `llm_calls_total`
- `llm_call_duration_ms`
- `llm_input_tokens_total`
- `llm_output_tokens_total`
- `llm_cache_hits_total`
- `llm_estimated_cost_usd`
- `llm_model_selected` (per model via `ModelRouter`)

## Skill execution

- `skill_invocations_total` (per skill name)
- `skill_duration_ms`
- `skill_success_rate`

## Orchestration

- `dag_total_duration_ms`
- `dag_tiers_executed`
- `dag_aborted_total`
- `intent_classification_distribution` (per intent type)
- `context_assembly_duration_ms`

## Guardrails

- `guardrail_input_blocked_total` (prompt injection detections)
- `guardrail_pii_scrubbed_total`
- `guardrail_output_blocked_total`

## Authentication and rate limiting

- `auth_requests_total` (per role)
- `auth_rejected_total` (401/403)
- `rate_limit_exceeded_total` (429)

## A/B experimentation

- `experiment_impressions_total` (per prompt × variant)
- `experiment_mean_score` (per variant)
- `experiment_significance_p_value`

## Operational outcomes

- `promotion_adjustment_success_rate`
- `work_order_backlog_reduction`
- `sales_recovery_after_alert`
- `branded_mix_uplift_after_recommendation`
- `underperforming_store_recovery_rate`

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](../../docs/terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](../../docs/markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
