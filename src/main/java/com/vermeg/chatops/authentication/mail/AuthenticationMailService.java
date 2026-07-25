package com.vermeg.chatops.authentication.mail;

public interface AuthenticationMailService {

    void sendInvitationEmail(String recipientEmail, String displayName, String activationToken);

    void sendPasswordResetEmail(String recipientEmail, String displayName, String resetToken);
}