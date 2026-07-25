package com.vermeg.chatops.identity.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.UUID;

public class UserNotFoundException extends ResponseStatusException {

  public UserNotFoundException(UUID id) {
    super(HttpStatus.NOT_FOUND, "User '%s' was not found".formatted(id));
  }
}