import { apiClient } from "./apiClient"
import type {
  ActivateAccountRequest,
  ForgotPasswordRequest,
  InviteUserRequest,
  LoginRequest,
  OneTimeTokenResponse,
  RefreshTokenRequest,
  ResetPasswordRequest,
  TokenResponse,
} from "../types/api"

/** POST /api/v1/auth/* — see AuthenticationController. */
export const authApi = {
  login: (request: LoginRequest) =>
    apiClient.post<TokenResponse>("/api/v1/auth/login", request, { anonymous: true }),

  refresh: (request: RefreshTokenRequest) =>
    apiClient.post<TokenResponse>("/api/v1/auth/refresh", request, { anonymous: true }),

  activate: (request: ActivateAccountRequest) =>
    apiClient.post<TokenResponse>("/api/v1/auth/activate", request, { anonymous: true }),

  forgotPassword: (request: ForgotPasswordRequest) =>
    apiClient.post<OneTimeTokenResponse>("/api/v1/auth/forgot-password", request, { anonymous: true }),

  resetPassword: (request: ResetPasswordRequest) =>
    apiClient.post<TokenResponse>("/api/v1/auth/reset-password", request, { anonymous: true }),

  /** Requires authentication; creates the user and returns its activation token. */
  invite: (request: InviteUserRequest) =>
    apiClient.post<OneTimeTokenResponse>("/api/v1/auth/invitations", request),
}
