package com.vermeg.chatops.tenancy.dto;

import com.vermeg.chatops.tenancy.entity.EnvironmentType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record UpdateEnvironmentRequest(
        @NotBlank
        @Size(max = 50)
        String name,

        @NotNull
        EnvironmentType type
) {
}
