package com.vermeg.chatops.access.repository;

import com.vermeg.chatops.access.entity.MembershipRoleEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface MembershipRoleRepository extends JpaRepository<MembershipRoleEntity, UUID> {

    boolean existsByMembership_IdAndRole_Id(UUID membershipId, UUID roleId);

    boolean existsByRole_Id(UUID roleId);
}