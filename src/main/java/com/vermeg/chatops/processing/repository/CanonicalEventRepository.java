package com.vermeg.chatops.processing.repository;

import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface CanonicalEventRepository extends JpaRepository<CanonicalEventEntity, UUID> {

    /**
     * Agent reports, newest first, with every filter optional. Null parameters
     * are ignored rather than matching null rows, so the same query serves the
     * per-agent pages and the unfiltered feed.
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

    List<CanonicalEventEntity> findByAgentKeyOrderByMessageTimestampDesc(String agentKey, Pageable pageable);

    long countByAgentKey(String agentKey);

    @Query("select distinct event.tenant from CanonicalEventEntity event where event.tenant is not null order by event.tenant")
    List<String> findDistinctTenants();
}
