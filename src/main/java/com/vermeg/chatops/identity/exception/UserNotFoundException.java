package com.vermeg.chatops.identity.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;

public class UserNotFoundException extends ResponseStatusException {

  public UserNotFoundException(UUID id) {
    super(HttpStatus.NOT_FOUND, "User '%s' was not found".formatted(id));
  }

  private UserNotFoundException(String message) {
    super(HttpStatus.NOT_FOUND, message);
  }

  /**
   * The email is deliberately left out of the message: this is reachable only
   * with a valid token whose subject no longer resolves to a user, and echoing
   * the address back would leak it into logs and client-side error toasts.
   */
  public static UserNotFoundException forAuthenticatedPrincipal() {
    return new UserNotFoundException("The authenticated user no longer exists");
  }
}