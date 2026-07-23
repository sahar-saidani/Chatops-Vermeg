package com.vermeg.chatops.authentication.dto;

public record OneTimeTokenResponse(String token, String tokenType, long expiresInSeconds) {
}