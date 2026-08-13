package com.vermeg.chatops.identity.controller;

import com.vermeg.chatops.identity.dto.CurrentUserResponse;
import com.vermeg.chatops.identity.dto.UserResponse;
import com.vermeg.chatops.identity.dto.UserUpdateRequest;
import com.vermeg.chatops.identity.service.UserManagementService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserManagementService userManagementService;

    public UserController(UserManagementService userManagementService) {
        this.userManagementService = userManagementService;
    }

    @GetMapping
    @PreAuthorize("hasAuthority('USER_READ')")
    public List<UserResponse> findAll() {
        return userManagementService.findAll();
    }

    /**
     * The caller's own profile, including role codes and permission codes.
     * Intentionally not gated by USER_READ: every authenticated user must be
     * able to read themselves in order for the client to build its navigation
     * and permission guards.
     */
    @GetMapping("/me")
    public CurrentUserResponse findCurrentUser(Authentication authentication) {
        return userManagementService.findCurrentUser(authentication.getName());
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('USER_READ')")
    public UserResponse findById(@PathVariable UUID id) {
        return userManagementService.findById(id);
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAuthority('USER_WRITE')")
    public UserResponse update(@PathVariable UUID id, @Valid @RequestBody UserUpdateRequest request) {
        return userManagementService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @PreAuthorize("hasAuthority('USER_WRITE')")
    public void delete(@PathVariable UUID id) {
        userManagementService.softDelete(id);
    }
}