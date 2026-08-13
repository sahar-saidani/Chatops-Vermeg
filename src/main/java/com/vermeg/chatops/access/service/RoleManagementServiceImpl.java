package com.vermeg.chatops.access.service;

import com.vermeg.chatops.access.dto.PermissionMatrixResponse;
import com.vermeg.chatops.access.dto.RoleCreateRequest;
import com.vermeg.chatops.access.dto.RoleResponse;
import com.vermeg.chatops.access.dto.RoleUpdateRequest;
import com.vermeg.chatops.access.entity.RoleEntity;
import com.vermeg.chatops.access.exception.RoleCodeAlreadyExistsException;
import com.vermeg.chatops.access.exception.RoleInUseException;
import com.vermeg.chatops.access.exception.RoleNotFoundException;
import com.vermeg.chatops.access.exception.SystemRoleProtectedException;
import com.vermeg.chatops.access.mapper.PermissionMapper;
import com.vermeg.chatops.access.mapper.RoleMapper;
import com.vermeg.chatops.access.repository.MembershipRoleRepository;
import com.vermeg.chatops.access.repository.PermissionRepository;
import com.vermeg.chatops.access.repository.RolePermissionRepository;
import com.vermeg.chatops.access.repository.RoleRepository;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.UUID;

@Service
@Transactional(readOnly = true)
public class RoleManagementServiceImpl implements RoleManagementService {

    private final RoleRepository roleRepository;
    private final MembershipRoleRepository membershipRoleRepository;
    private final RolePermissionRepository rolePermissionRepository;
    private final PermissionRepository permissionRepository;
    private final RoleMapper roleMapper;
    private final PermissionMapper permissionMapper;

    public RoleManagementServiceImpl(
            RoleRepository roleRepository,
            MembershipRoleRepository membershipRoleRepository,
            RolePermissionRepository rolePermissionRepository,
            PermissionRepository permissionRepository,
            RoleMapper roleMapper,
            PermissionMapper permissionMapper
    ) {
        this.roleRepository = roleRepository;
        this.membershipRoleRepository = membershipRoleRepository;
        this.rolePermissionRepository = rolePermissionRepository;
        this.permissionRepository = permissionRepository;
        this.roleMapper = roleMapper;
        this.permissionMapper = permissionMapper;
    }

    @Override
    public PermissionMatrixResponse findPermissionMatrix() {
        // One pass over role_permissions instead of a query per role: the table
        // is small (one row per grant) and this keeps the endpoint O(1) queries.
        Map<UUID, List<String>> codesByRole = rolePermissionRepository.findAll().stream()
                .collect(Collectors.groupingBy(
                        grant -> grant.getRole().getId(),
                        Collectors.mapping(grant -> grant.getPermission().getCode(), Collectors.toList())
                ));

        List<PermissionMatrixResponse.RolePermissions> roles =
                roleRepository.findAll(Sort.by(Sort.Direction.ASC, "name")).stream()
                        .map(role -> new PermissionMatrixResponse.RolePermissions(
                                role.getId(),
                                role.getCode(),
                                role.getName(),
                                role.isSystem(),
                                codesByRole.getOrDefault(role.getId(), List.of()).stream().sorted().toList()
                        ))
                        .toList();

        return new PermissionMatrixResponse(
                permissionRepository.findAll().stream()
                        .sorted(Comparator.comparing(permission -> permission.getCode()))
                        .map(permissionMapper::toResponse)
                        .toList(),
                roles
        );
    }

    @Override
    public List<RoleResponse> findAll() {
        return roleRepository.findAll(Sort.by(Sort.Direction.ASC, "name")).stream()
                .map(roleMapper::toResponse)
                .toList();
    }

    @Override
    public RoleResponse findById(UUID id) {
        return roleMapper.toResponse(getRoleOrThrow(id));
    }

    @Override
    @Transactional
    public RoleResponse create(RoleCreateRequest request) {
        String normalizedCode = request.code().strip().toUpperCase(Locale.ROOT);
        if (roleRepository.findByCode(normalizedCode).isPresent()) {
            throw new RoleCodeAlreadyExistsException(normalizedCode);
        }
        RoleEntity role = roleRepository.save(new RoleEntity(normalizedCode, request.name(), request.description()));
        return roleMapper.toResponse(role);
    }

    @Override
    @Transactional
    public RoleResponse update(UUID id, RoleUpdateRequest request) {
        RoleEntity role = getRoleOrThrow(id);
        role.updateDetails(request.name(), request.description());
        return roleMapper.toResponse(role);
    }

    @Override
    @Transactional
    public void delete(UUID id) {
        RoleEntity role = getRoleOrThrow(id);
        if (role.isSystem()) {
            throw new SystemRoleProtectedException(role.getCode());
        }
        if (membershipRoleRepository.existsByRole_Id(id)) {
            throw new RoleInUseException(role.getCode());
        }
        roleRepository.delete(role);
    }

    private RoleEntity getRoleOrThrow(UUID id) {
        return roleRepository.findById(id).orElseThrow(() -> new RoleNotFoundException(id));
    }
}
