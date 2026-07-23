package com.vermeg.chatops.authentication.dto;

import com.vermeg.chatops.common.validation.StrongPassword;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ResetPasswordRequest(
        @NotBlank(message = "Password reset token is required") @Size(max = 512, message = "Password reset token is invalid") String token,
        @StrongPassword String password
) {
}
