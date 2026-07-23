package com.vermeg.chatops.identity.repository;

import com.vermeg.chatops.identity.entity.UserEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<UserEntity, UUID> {

    Optional<UserEntity> findByNormalizedEmail(String normalizedEmail);

    boolean existsByNormalizedEmail(String normalizedEmail);
}
