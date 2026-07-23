package com.vermeg.chatops.access.service;

import org.springframework.security.core.GrantedAuthority;

import java.util.Collection;

public interface AccessAuthorityService {

    boolean isActiveUser(String userEmail);

    Collection<? extends GrantedAuthority> findAuthoritiesForActiveUser(String userEmail);
}
