package com.vermeg.chatops.processing;

import com.vermeg.chatops.common.events.CanonicalEvent;
import com.vermeg.chatops.processing.dto.AgentEventResponse;
import com.vermeg.chatops.processing.dto.AgentStatusResponse;
import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import com.vermeg.chatops.processing.repository.CanonicalEventRepository;
import com.vermeg.chatops.processing.service.AgentEventQueryService;
import com.vermeg.chatops.processing.service.AgentEventScope;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * canonical_events holds every tenant's agent reports in one table, so the
 * AGENT_EVENT_READ permission alone cannot keep them apart -- the query has to
 * be scoped to the caller's tenants. These tests pin that boundary.
 *
 * <p>They exercise the query service against the real repository on the H2
 * test profile, matching how ChatopsVermegApplicationTests already boots the
 * context, rather than mocking the repository: the isolation lives in the
 * queries themselves, so a mock would assert nothing about it.
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class AgentEventTenantIsolationTest {

    @Autowired
    private AgentEventQueryService agentEventQueryService;

    @Autowired
    private CanonicalEventRepository canonicalEventRepository;

    @BeforeEach
    void seedEventsForTwoTenants() {
        canonicalEventRepository.deleteAll();
        canonicalEventRepository.saveAll(List.of(
                event("git", "MAIF", "MAIF-WINDOWS-01"),
                event("git", "NNBE", "NNBE-CENTOS-01"),
                event("jenkins", "NNBE", "NNBE-CENTOS-01"),
                // Predates V10's machine identity columns: attributable to
                // nobody, so it must never reach a tenant-scoped caller.
                event("git", null, null)
        ));
    }

    private static CanonicalEventEntity event(String agentKey, String tenant, String machineReference) {
        return new CanonicalEventEntity(new CanonicalEvent(
                agentKey,
                Instant.now(),
                "dev",
                Map.of("sample", "payload"),
                tenant,
                "STANDALONE",
                machineReference,
                null,
                null
        ));
    }

    @Test
    void aTenantScopedCallerSeesOnlyItsOwnTenantsEvents() {
        List<AgentEventResponse> events =
                agentEventQueryService.search(AgentEventScope.forTenants(List.of("MAIF")), null, null, null, 50);

        assertThat(events).isNotEmpty();
        assertThat(events).allSatisfy(event -> assertThat(event.tenant()).isEqualTo("MAIF"));
        assertThat(events).noneSatisfy(event -> assertThat(event.tenant()).isEqualTo("NNBE"));
    }

    @Test
    void aTenantScopedCallerNeverSeesEventsWithNoTenant() {
        List<AgentEventResponse> events =
                agentEventQueryService.search(AgentEventScope.forTenants(List.of("MAIF")), null, null, null, 50);

        assertThat(events).noneSatisfy(event -> assertThat(event.tenant()).isNull());
    }

    @Test
    void anExplicitTenantFilterCannotReachAnotherTenant() {
        // The tenant query parameter is a filter, not an escape hatch: asking
        // for NNBE while scoped to MAIF must return nothing, not NNBE's rows.
        List<AgentEventResponse> events =
                agentEventQueryService.search(AgentEventScope.forTenants(List.of("MAIF")), null, "NNBE", null, 50);

        assertThat(events).isEmpty();
    }

    @Test
    void aCallerBelongingToNoTenantSeesNothing() {
        List<AgentEventResponse> events =
                agentEventQueryService.search(AgentEventScope.forTenants(List.of()), null, null, null, 50);

        assertThat(events).isEmpty();
    }

    @Test
    void aPlatformWideCallerSeesEveryTenant() {
        List<AgentEventResponse> events =
                agentEventQueryService.search(AgentEventScope.allTenants(), null, null, null, 50);

        assertThat(events).hasSize(4);
        assertThat(events).anySatisfy(event -> assertThat(event.tenant()).isEqualTo("NNBE"));
        assertThat(events).anySatisfy(event -> assertThat(event.tenant()).isEqualTo("MAIF"));
    }

    @Test
    void agentStatusIsAlsoTenantScoped() {
        List<AgentStatusResponse> maifStatuses =
                agentEventQueryService.findAgentStatuses(AgentEventScope.forTenants(List.of("MAIF")));

        AgentStatusResponse jenkins = statusOf(maifStatuses, "jenkins");
        // The only jenkins report belongs to NNBE, so a MAIF-scoped caller must
        // see NO_DATA rather than NNBE's machine identity.
        assertThat(jenkins.status()).isEqualTo("NO_DATA");
        assertThat(jenkins.machineReference()).isNull();
        assertThat(jenkins.eventCount()).isZero();

        AgentStatusResponse git = statusOf(maifStatuses, "git");
        assertThat(git.status()).isEqualTo("ONLINE");
        assertThat(git.tenant()).isEqualTo("MAIF");
        // Counts must exclude the NNBE and null-tenant git rows.
        assertThat(git.eventCount()).isEqualTo(1L);
    }

    @Test
    void agentStatusForAPlatformWideCallerCountsEveryTenant() {
        List<AgentStatusResponse> statuses =
                agentEventQueryService.findAgentStatuses(AgentEventScope.allTenants());

        assertThat(statusOf(statuses, "git").eventCount()).isEqualTo(3L);
        assertThat(statusOf(statuses, "jenkins").status()).isEqualTo("ONLINE");
    }

    @Test
    void jiraIsNeverSurfacedEvenToAPlatformWideCaller() {
        canonicalEventRepository.save(event("jira", "MAIF", "MAIF-WINDOWS-01"));

        List<AgentStatusResponse> statuses =
                agentEventQueryService.findAgentStatuses(AgentEventScope.allTenants());

        assertThat(statuses).extracting(AgentStatusResponse::agentKey).doesNotContain("jira");
    }

    private static AgentStatusResponse statusOf(List<AgentStatusResponse> statuses, String agentKey) {
        return statuses.stream()
                .filter(status -> status.agentKey().equals(agentKey))
                .findFirst()
                .orElseThrow(() -> new AssertionError("No status reported for agent " + agentKey));
    }
}
