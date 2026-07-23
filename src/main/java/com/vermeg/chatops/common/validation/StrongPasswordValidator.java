package com.vermeg.chatops.common.validation;

import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

public class StrongPasswordValidator implements ConstraintValidator<StrongPassword, String> {

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.length() < 12) {
            return false;
        }
        boolean upperCase = false;
        boolean lowerCase = false;
        boolean digit = false;
        boolean symbol = false;
        for (int index = 0; index < value.length(); index++) {
            char character = value.charAt(index);
            upperCase |= Character.isUpperCase(character);
            lowerCase |= Character.isLowerCase(character);
            digit |= Character.isDigit(character);
            symbol |= !Character.isLetterOrDigit(character) && !Character.isWhitespace(character);
        }
        return upperCase && lowerCase && digit && symbol;
    }
}
