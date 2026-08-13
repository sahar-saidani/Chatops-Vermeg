package com.vermeg.chatops.processing.service;

import java.util.List;

/**
 * Which tenants' agent reports a caller may see.
 *
 * <p>canonical_events stores every tenant's reports in a single table keyed by
 * a tenant <em>name</em>, so authorization cannot stop at "may read agent
 * events" -- it has to answer "whose". This carries that answer from the
 * controller, which knows the caller, down to the query.
 *
 * @param platformWide true when the caller holds AGENT_EVENT_READ_ALL and may
 *                     see every tenant, including legacy rows with no tenant.
 * @param tenantNames  the tenant names the caller is an active member of;
 *                     ignored when {@code platformWide} is true. Empty means
 *                     the caller may see nothing.
 */
public record AgentEventScope(boolean platformWide, List<String> tenantNames) {

    public AgentEventScope {
        tenantNames = tenantNames == null ? List.of() : List.copyOf(tenantNames);
    }

    /** Named allTenants() rather than platformWide() so it does not shadow the record accessor. */
    public static AgentEventScope allTenants() {
        return new AgentEventScope(true, List.of());
    }

    public static AgentEventScope forTenants(List<String> tenantNames) {
        return new AgentEventScope(false, tenantNames);
    }

    /** True when the caller is tenant-scoped and belongs to no tenant at all. */
    public boolean isEmpty() {
        return !platformWide && tenantNames.isEmpty();
    }
}
