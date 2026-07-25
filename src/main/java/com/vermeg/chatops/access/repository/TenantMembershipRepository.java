package com.vermeg.chatops.access.repository;

import com.vermeg.chatops.access.entity.TenantMembershipEntity;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface TenantMembershipRepository extends JpaRepository<TenantMembershipEntity, UUID> {

    @EntityGraph(attributePaths = "tenant")
    List<TenantMembershipEntity> findByUser_NormalizedEmailAndActiveTrueOrderByTenant_NameAsc(String normalizedEmail);
    @EntityGraph(attributePaths = "tenant")
    List<TenantMembershipEntity> findByUser_IdIn(Collection<UUID> userIds);
    Optional<TenantMembershipEntity> findByTenant_IdAndUser_Id(UUID tenantId, UUID userId);

    @Query("""
            select distinct rolePermission.permission.code
            from TenantMembershipEntity membership
            join MembershipRoleEntity membershipRole on membershipRole.membership = membership
            join RolePermissionEntity rolePermission on rolePermission.role = membershipRole.role
            where membership.user.normalizedEmail = :normalizedEmail
              and membership.active = true
              and membership.tenant.active = true
            """)
    List<String> findActivePermissionCodesByUserEmail(@Param("normalizedEmail") String normalizedEmail);

    @Query("""
            select distinct rolePermission.permission.code
            from TenantMembershipEntity membership
            join MembershipRoleEntity membershipRole on membershipRole.membership = membership
            join RolePermissionEntity rolePermission on rolePermission.role = membershipRole.role
            where membership.user.normalizedEmail = :normalizedEmail
              and membership.tenant.id = :tenantId
              and membership.active = true
              and membership.tenant.active = true
            """)
    List<String> findActivePermissionCodesByUserEmailAndTenantId(
            @Param("normalizedEmail") String normalizedEmail,
            @Param("tenantId") UUID tenantId
    );
}
