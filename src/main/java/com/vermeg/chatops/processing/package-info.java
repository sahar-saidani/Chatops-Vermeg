/**
 * Data Processing Agent: turns heterogeneous, agent-specific payloads
 * consumed from RabbitMQ into the canonical event shape declared in
 * {@code common.events}, then persists them.
 *
 * <p>Scope of this module: validation + normalization + minimal enrichment
 * (environment, persistence timestamps) + persistence. Correlation,
 * deduplication, KPI computation and anomaly detection are explicitly out
 * of scope here and are separate future modules.
 */
package com.vermeg.chatops.processing;