package com.vermeg.chatops.authentication.service;

import com.vermeg.chatops.access.entity.MembershipRoleEntity;
import com.vermeg.chatops.access.entity.RoleEntity;
import com.vermeg.chatops.access.entity.TenantMembershipEntity;
import com.vermeg.chatops.access.repository.MembershipRoleRepository;
import com.vermeg.chatops.access.repository.RoleRepository;
import com.vermeg.chatops.access.repository.TenantMembershipRepository;
import com.vermeg.chatops.authentication.dto.ActivateAccountRequest;
import com.vermeg.chatops.authentication.dto.ForgotPasswordRequest;
import com.vermeg.chatops.authentication.dto.InviteUserRequest;
import com.vermeg.chatops.authentication.dto.LoginRequest;
import com.vermeg.chatops.authentication.dto.OneTimeTokenResponse;
import com.vermeg.chatops.authentication.dto.RefreshTokenRequest;
import com.vermeg.chatops.authentication.dto.ResetPasswordRequest;
import com.vermeg.chatops.authentication.dto.TokenResponse;
import com.vermeg.chatops.authentication.entity.AuthenticationTokenEntity;
import com.vermeg.chatops.authentication.entity.AuthenticationTokenType;
import com.vermeg.chatops.authentication.exception.InvalidCredentialsException;
import com.vermeg.chatops.authentication.exception.InvalidTokenException;
import com.vermeg.chatops.authentication.exception.InvitationConflictException;
import com.vermeg.chatops.authentication.repository.AuthenticationTokenRepository;
import com.vermeg.chatops.identity.entity.UserEntity;
import com.vermeg.chatops.identity.repository.UserRepository;
import com.vermeg.chatops.security.jwt.JwtTokenProvider;
import com.vermeg.chatops.tenancy.entity.TenantEntity;
import com.vermeg.chatops.tenancy.repository.TenantRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.*;

import com.vermeg.chatops.authentication.mail.AuthenticationMailService;

@Service
@Transactional(readOnly = true)
public class AuthenticationServiceImpl implements AuthenticationService {

    private static final Duration INVITATION_TOKEN_TTL = Duration.ofDays(7);
    private static final Duration PASSWORD_RESET_TOKEN_TTL = Duration.ofHours(24);
    private static final String TOKEN_TYPE_BEARER = "Bearer";
    private final AuthenticationMailService authenticationMailService;
    private final UserRepository userRepository;
    private final TenantRepository tenantRepository;
    private final RoleRepository roleRepository;
    private final TenantMembershipRepository tenantMembershipRepository;
    private final MembershipRoleRepository membershipRoleRepository;
    private final AuthenticationTokenRepository authenticationTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final long accessTokenExpirationMillis;
    private final long refreshTokenExpirationMillis;
    private final SecureRandom secureRandom = new SecureRandom();

    public AuthenticationServiceImpl(
            UserRepository userRepository,
            TenantRepository tenantRepository,
            RoleRepository roleRepository,
            TenantMembershipRepository tenantMembershipRepository,
            MembershipRoleRepository membershipRoleRepository,
            AuthenticationTokenRepository authenticationTokenRepository,
            PasswordEncoder passwordEncoder,
            JwtTokenProvider jwtTokenProvider,
            AuthenticationMailService authenticationMailService,
            @Value("${security.jwt.expiration:3600000}") long accessTokenExpirationMillis,
            @Value("${security.authentication.refresh-token-expiration:2592000000}") long refreshTokenExpirationMillis
    ) {
        this.userRepository = userRepository;
        this.tenantRepository = tenantRepository;
        this.roleRepository = roleRepository;
        this.tenantMembershipRepository = tenantMembershipRepository;
        this.membershipRoleRepository = membershipRoleRepository;
        this.authenticationTokenRepository = authenticationTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
        this.accessTokenExpirationMillis = accessTokenExpirationMillis;
        this.refreshTokenExpirationMillis = refreshTokenExpirationMillis;
        this.authenticationMailService = authenticationMailService;
    }

    @Override
    @Transactional
    public OneTimeTokenResponse invite(InviteUserRequest request) {
        String normalizedEmail = normalizeEmail(request.email());
        if (userRepository.existsByNormalizedEmail(normalizedEmail)) {
            throw new InvitationConflictException(request.email());
        }

        TenantEntity tenant = tenantRepository.findById(request.tenantId())
                .filter(TenantEntity::isActive)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Tenant not found"));

        Set<UUID> requestedRoleIds = new LinkedHashSet<>(request.roleIds());
        List<RoleEntity> roles = roleRepository.findByIdIn(requestedRoleIds).stream().toList();
        if (roles.size() != requestedRoleIds.size()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "One or more roles were not found");
        }

        UserEntity user = userRepository.save(new UserEntity(
                request.email(),
                request.displayName(),
                passwordEncoder.encode(generateTemporaryPassword())
        ));

        TenantMembershipEntity membership = tenantMembershipRepository.save(new TenantMembershipEntity(tenant, user));
        membershipRoleRepository.saveAll(roles.stream()
                .map(role -> new MembershipRoleEntity(membership, role))
                .toList());

        Instant now = Instant.now();
        String invitationToken = generatePlainToken();
        authenticationTokenRepository.save(new AuthenticationTokenEntity(
                user,
                hashToken(invitationToken),
                AuthenticationTokenType.INVITATION,
                null,
                now.plus(INVITATION_TOKEN_TTL)
        ));
        authenticationMailService.sendInvitationEmail(user.getEmail(), user.getDisplayName(), invitationToken);

        return new OneTimeTokenResponse(invitationToken, AuthenticationTokenType.INVITATION.name(), INVITATION_TOKEN_TTL.toSeconds());
    }

    @Override
    @Transactional
    public TokenResponse activate(ActivateAccountRequest request) {
        return completePasswordSetup(request.token(), request.password(), AuthenticationTokenType.INVITATION);
    }

    @Override
    @Transactional
    public TokenResponse login(LoginRequest request) {
        UserEntity user = userRepository.findByNormalizedEmail(normalizeEmail(request.email()))
                .filter(UserEntity::isActive)
                .orElseThrow(InvalidCredentialsException::new);

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new InvalidCredentialsException();
        }

        return issueSessionTokens(user, UUID.randomUUID());
    }

    @Override
    @Transactional
    public TokenResponse refresh(RefreshTokenRequest request) {
        Instant now = Instant.now();
        AuthenticationTokenEntity refreshToken = findUsableToken(request.refreshToken(), AuthenticationTokenType.REFRESH, now);
        UserEntity user = refreshToken.getUser();
        if (!user.isActive()) {
            throw new InvalidCredentialsException();
        }

        refreshToken.markUsed(now);
        UUID familyId = refreshToken.getFamilyId() != null ? refreshToken.getFamilyId() : UUID.randomUUID();
        return issueSessionTokens(user, familyId);
    }

    @Override
    @Transactional
    public OneTimeTokenResponse forgotPassword(ForgotPasswordRequest request) {
        UserEntity user = userRepository.findByNormalizedEmail(normalizeEmail(request.email()))
                .filter(UserEntity::isActive)
                .orElseThrow(InvalidCredentialsException::new);

        Instant now = Instant.now();
        authenticationTokenRepository.revokeUnusedTokensForUser(user.getId(), AuthenticationTokenType.PASSWORD_RESET, now);

        String resetToken = generatePlainToken();
        authenticationTokenRepository.save(new AuthenticationTokenEntity(
                user,
                hashToken(resetToken),
                AuthenticationTokenType.PASSWORD_RESET,
                null,
                now.plus(PASSWORD_RESET_TOKEN_TTL)
        ));
        authenticationMailService.sendPasswordResetEmail(user.getEmail(), user.getDisplayName(), resetToken);

        return new OneTimeTokenResponse(resetToken, AuthenticationTokenType.PASSWORD_RESET.name(), PASSWORD_RESET_TOKEN_TTL.toSeconds());
    }

    @Override
    @Transactional
    public TokenResponse resetPassword(ResetPasswordRequest request) {
        return completePasswordSetup(request.token(), request.password(), AuthenticationTokenType.PASSWORD_RESET);
    }

    private TokenResponse completePasswordSetup(String rawToken, String password, AuthenticationTokenType tokenType) {
        Instant now = Instant.now();
        AuthenticationTokenEntity authenticationToken = findUsableToken(rawToken, tokenType, now);
        UserEntity user = authenticationToken.getUser();
        if (tokenType == AuthenticationTokenType.PASSWORD_RESET && !user.isActive()) {
            throw new InvalidTokenException("Invalid or expired token");
        }

        user.activate();
        user.changePassword(passwordEncoder.encode(password));
        authenticationToken.markUsed(now);
        authenticationTokenRepository.revokeUnusedTokensForUser(user.getId(), tokenType, now);
        authenticationTokenRepository.revokeUnusedTokensForUser(user.getId(), AuthenticationTokenType.REFRESH, now);

        return issueSessionTokens(user, UUID.randomUUID());
    }

    private TokenResponse issueSessionTokens(UserEntity user, UUID familyId) {
        String accessToken = jwtTokenProvider.generateToken(user.getNormalizedEmail());
        String refreshToken = generatePlainToken();
        authenticationTokenRepository.save(new AuthenticationTokenEntity(
                user,
                hashToken(refreshToken),
                AuthenticationTokenType.REFRESH,
                familyId,
                Instant.now().plusMillis(refreshTokenExpirationMillis)
        ));
        return new TokenResponse(accessToken, refreshToken, TOKEN_TYPE_BEARER, Duration.ofMillis(accessTokenExpirationMillis).toSeconds());
    }

    private AuthenticationTokenEntity findUsableToken(String rawToken, AuthenticationTokenType tokenType, Instant instant) {
        AuthenticationTokenEntity token = authenticationTokenRepository
                .findByTokenHashAndTokenType(hashToken(rawToken), tokenType)
                .orElseThrow(() -> new InvalidTokenException("Invalid or expired token"));
        if (!token.isUsableAt(instant)) {
            throw new InvalidTokenException("Invalid or expired token");
        }
        return token;
    }

    private String generatePlainToken() {
        byte[] buffer = new byte[48];
        secureRandom.nextBytes(buffer);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(buffer);
    }

    private String generateTemporaryPassword() {
        return generatePlainToken();
    }

    private String hashToken(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(token.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is required", exception);
        }
    }

    private static String normalizeEmail(String value) {
        return value.strip().toLowerCase(Locale.ROOT);
    }
}