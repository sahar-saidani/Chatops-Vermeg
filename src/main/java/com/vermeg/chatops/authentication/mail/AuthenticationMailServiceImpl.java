package com.vermeg.chatops.authentication.mail;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

@Service
public class AuthenticationMailServiceImpl implements AuthenticationMailService {

    private final JavaMailSender mailSender;
    private final String mailFrom;
    private final String frontendBaseUrl;

    public AuthenticationMailServiceImpl(
            JavaMailSender mailSender,
            @Value("${chatops.authentication.mail-from}") String mailFrom,
            @Value("${chatops.authentication.frontend-base-url}") String frontendBaseUrl
    ) {
        this.mailSender = mailSender;
        this.mailFrom = mailFrom;
        this.frontendBaseUrl = frontendBaseUrl;
    }

    @Override
    public void sendInvitationEmail(String recipientEmail, String displayName, String activationToken) {
        String activationLink = frontendBaseUrl + "/activate?token=" + activationToken;
        send(recipientEmail, "You're invited to ChatOps SOLIFE",
                "Hello " + displayName + ",\n\n"
                        + "You have been invited to join ChatOps SOLIFE.\n"
                        + "Activate your account using the link below (valid for 7 days):\n"
                        + activationLink + "\n\n"
                        + "If you did not expect this invitation, you can safely ignore this email.");
    }

    @Override
    public void sendPasswordResetEmail(String recipientEmail, String displayName, String resetToken) {
        String resetLink = frontendBaseUrl + "/reset-password?token=" + resetToken;
        send(recipientEmail, "Reset your ChatOps SOLIFE password",
                "Hello " + displayName + ",\n\n"
                        + "A password reset was requested for your account.\n"
                        + "Reset your password using the link below (valid for 24 hours):\n"
                        + resetLink + "\n\n"
                        + "If you did not request this, you can safely ignore this email.");
    }

    private void send(String to, String subject, String body) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(mailFrom);
        message.setTo(to);
        message.setSubject(subject);
        message.setText(body);
        mailSender.send(message);
    }
}