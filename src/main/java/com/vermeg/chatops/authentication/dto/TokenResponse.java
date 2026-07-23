package com.vermeg.chatops.authentication.dto;

public record TokenResponse(String accessToken, String refreshToken, String tokenType, long expiresInSeconds) {
}
