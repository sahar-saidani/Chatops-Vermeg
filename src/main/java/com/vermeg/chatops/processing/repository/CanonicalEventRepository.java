package com.vermeg.chatops.processing.repository;

import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

public interface CanonicalEventRepository extends JpaRepository<CanonicalEventEntity, UUID> {

    /**
     * Agent reports, newest first, with every filter optional. Null parameters
     * are ignored rather than matching null rows, so the same query serves the
     * per-agent pages and the unfiltered feed.
     *
     * <p><strong>Unscoped.</strong> canonical_events holds every tenant's data
     * in one table, so this returns other tenants' reports too. Only callers
     * holding the platform-wide scope may use it; everything else must go
     * through {@link #searchForTenants}.
     */
    @Query("""
            select event from CanonicalEventEntity event
            where (:agentKey is null or event.agentKey = :agentKey)
              and (:tenant is null or event.tenant = :tenant)
              and (:environment is null or event.environment = :environment)
            order by event.messageTimestamp desc
            """)
    List<CanonicalEventEntity> search(
            @Param("agentKey") String agentKey,
            @Param("tenant") String tenant,
            @Param("environment") String environment,
            Pageable pageable
    );

    /**
     * Tenant-scoped variant. Rows whose tenant is null are excluded on
     * purpose: they predate machine identity (see V10) and cannot be attributed
     * to anyone, so showing them to a tenant-scoped caller would leak another
     * tenant's data on the strength of a missing column.
     */
    @Query("""
            select event from CanonicalEventEntity event
            where event.tenant in :tenants
              and (:agentKey is null or event.agentKey = :agentKey)
              and (:tenant is null or event.tenant = :tenant)
              and (:environment is null or event.environment = :environment)
            order by event.messageTimestamp desc
            """)
    List<CanonicalEventEntity> searchForTenants(
            @Param("tenants") Collection<String> tenants,
            @Param("agentKey") String agentKey,
            @Param("tenant") String tenant,
            @Param("environment") String environment,
            Pageable pageable
    );

    List<CanonicalEventEntity> findByAgentKeyOrderByMessageTimestampDesc(String agentKey, Pageable pageable);

    List<CanonicalEventEntity> findByAgentKeyAndTenantInOrderByMessageTimestampDesc(
            String agentKey,
            Collection<String> tenants,
            Pageable pageable
    );

    long countByAgentKey(String agentKey);

    long countByAgentKeyAndTenantIn(String agentKey, Collection<String> tenants);

    @Query("select distinct event.tenant from CanonicalEventEntity event where event.tenant is not null order by event.tenant")
    List<String> findDistinctTenants();
}
