package com.vermeg.chatops.identity.service;

import com.vermeg.chatops.access.entity.TenantMembershipEntity;
import com.vermeg.chatops.access.repository.TenantMembershipRepository;
import com.vermeg.chatops.identity.dto.UserMembershipSummary;
import com.vermeg.chatops.identity.dto.UserResponse;
import com.vermeg.chatops.identity.dto.UserUpdateRequest;
import com.vermeg.chatops.identity.entity.UserEntity;
import com.vermeg.chatops.identity.exception.UserNotFoundException;
import com.vermeg.chatops.identity.mapper.UserMapper;
import com.vermeg.chatops.identity.repository.UserRepository;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class UserManagementServiceImpl implements UserManagementService {

    private final UserRepository userRepository;
    private final TenantMembershipRepository tenantMembershipRepository;
    private final UserMapper userMapper;

    public UserManagementServiceImpl(
            UserRepository userRepository,
            TenantMembershipRepository tenantMembershipRepository,
            UserMapper userMapper
    ) {
        this.userRepository = userRepository;
        this.tenantMembershipRepository = tenantMembershipRepository;
        this.userMapper = userMapper;
    }

    @Override
    public List<UserResponse> findAll() {
        List<UserEntity> users = userRepository.findAll(Sort.by(Sort.Direction.ASC, "displayName"));
        Map<UUID, List<UserMembershipSummary>> membershipsByUser = loadMemberships(
                users.stream().map(UserEntity::getId).toList()
        );
        return users.stream()
                .map(user -> userMapper.toResponse(user, membershipsByUser.getOrDefault(user.getId(), List.of())))
                .toList();
    }

    @Override
    public UserResponse findById(UUID id) {
        UserEntity user = getUserOrThrow(id);
        List<UserMembershipSummary> memberships = loadMemberships(List.of(id)).getOrDefault(id, List.of());
        return userMapper.toResponse(user, memberships);
    }

    @Override
    @Transactional
    public UserResponse update(UUID id, UserUpdateRequest request) {
        UserEntity user = getUserOrThrow(id);
        if (request.displayName() != null) {
            user.rename(request.displayName());
        }
        if (request.active() != null) {
            if (request.active()) {
                user.activate();
            } else {
                user.disable();
            }
        }
        List<UserMembershipSummary> memberships = loadMemberships(List.of(id)).getOrDefault(id, List.of());
        return userMapper.toResponse(user, memberships);
    }

    @Override
    @Transactional
    public void softDelete(UUID id) {
        UserEntity user = getUserOrThrow(id);
        user.disable();
    }

    private UserEntity getUserOrThrow(UUID id) {
        return userRepository.findById(id).orElseThrow(() -> new UserNotFoundException(id));
    }

    private Map<UUID, List<UserMembershipSummary>> loadMemberships(List<UUID> userIds) {
        List<TenantMembershipEntity> memberships = tenantMembershipRepository.findByUser_IdIn(userIds);
        return memberships.stream()
                .collect(Collectors.groupingBy(
                        m -> m.getUser().getId(),
                        Collectors.mapping(userMapper::toMembershipSummary, Collectors.toList())
                ));
    }
}