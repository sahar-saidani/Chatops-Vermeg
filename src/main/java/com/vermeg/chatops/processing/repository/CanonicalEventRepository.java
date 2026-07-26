package com.vermeg.chatops.processing.repository;

import com.vermeg.chatops.processing.entity.CanonicalEventEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface CanonicalEventRepository extends JpaRepository<CanonicalEventEntity, UUID> {
}