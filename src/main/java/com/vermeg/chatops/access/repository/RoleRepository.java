package com.vermeg.chatops.access.repository;

import com.vermeg.chatops.access.entity.RoleEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.Collection;
import java.util.UUID;

public interface RoleRepository extends JpaRepository<RoleEntity, UUID> {

    Optional<RoleEntity> findByCode(String code);

    Collection<RoleEntity> findByIdIn(Collection<UUID> ids);
}
