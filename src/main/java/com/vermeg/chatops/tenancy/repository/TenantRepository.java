package com.vermeg.chatops.tenancy.repository;

import com.vermeg.chatops.tenancy.entity.TenantEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface TenantRepository extends JpaRepository<TenantEntity, UUID> {

    boolean existsByNameIgnoreCase(String name);

    Optional<TenantEntity> findByIdAndActiveTrue(UUID id);

    List<TenantEntity> findByActiveTrueOrderByNameAsc();
}