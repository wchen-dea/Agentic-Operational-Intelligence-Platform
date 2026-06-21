# Business Metrics to Instrument

Target status: `agentic-operational-intelligence-platform`

These metrics validate whether the platform is improving real-time decisions for store managers and executives.

## Data freshness

- kpi_event_lag_seconds
- source_topic_lag_records
- gold_table_update_latency_seconds

## AI quality

- answer_grounding_score
- recommendation_acceptance_rate
- alert_precision_rate
- persona_brief_actionability_score
- eval_conciseness_score

## Agent performance

- agent_duration_ms (per agent node, tracked by `AgentPerformanceTracker`)
- agent_executions_total
- agent_successes_total
- agent_failures_total
- agent_fallbacks_total
- agent_retries_total

## LLM usage

- llm_calls_total
- llm_call_duration_ms
- llm_input_tokens_total
- llm_output_tokens_total

## Skill execution

- skill_invocations_total (per skill name)
- skill_duration_ms
- skill_success_rate

## Orchestration

- dag_total_duration_ms
- dag_tiers_executed
- dag_aborted_total
- intent_classification_distribution (per intent type)

## Operational outcomes

- promotion_adjustment_success_rate
- work_order_backlog_reduction
- sales_recovery_after_alert
- branded_mix_uplift_after_recommendation
- underperforming_store_recovery_rate
