/**
 * Types mirroring the real backend DTOs.
 *
 * Every shape here was transcribed from the actual Java records under
 * src/main/java/com/vermeg/chatops/**\/dto/ and the Pydantic models in
 * llm-orchestrator/api.py. Do not add fields the backend does not send.
 */

/* ------------------------------------------------------------------ auth */

/** com.vermeg.chatops.authentication.dto.LoginRequest */
export interface LoginRequest {
  email: string
  password: string
}

/** com.vermeg.chatops.authentication.dto.TokenResponse */
export interface TokenResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresInSeconds: number
}

/** com.vermeg.chatops.authentication.dto.RefreshTokenRequest */
export interface RefreshTokenRequest {
  refreshToken: string
}

/** com.vermeg.chatops.authentication.dto.InviteUserRequest */
export interface InviteUserRequest {
  email: string
  displayName: string
  tenantId: string
  roleIds: string[]
}

/** com.vermeg.chatops.authentication.dto.OneTimeTokenResponse */
export interface OneTimeTokenResponse {
  token: string
  tokenType: string
  expiresInSeconds: number
}

/** com.vermeg.chatops.authentication.dto.ActivateAccountRequest */
export interface ActivateAccountRequest {
  token: string
  password: string
}

/** com.vermeg.chatops.authentication.dto.ForgotPasswordRequest */
export interface ForgotPasswordRequest {
  email: string
}

/** com.vermeg.chatops.authentication.dto.ResetPasswordRequest */
export interface ResetPasswordRequest {
  token: string
  password: string
}

/* ------------------------------------------------------------- identity */

/** com.vermeg.chatops.identity.entity.UserStatus */
export type UserStatus = "PENDING_ACTIVATION" | "ACTIVE" | "LOCKED" | "DISABLED"

/** com.vermeg.chatops.identity.dto.UserMembershipSummary */
export interface UserMembershipSummary {
  tenantId: string
  /** Mapped from the tenant only when present; V8 dropped the tenants.code column. */
  tenantCode: string | null
  tenantName: string
  active: boolean
}

/** com.vermeg.chatops.identity.dto.UserResponse */
export interface UserResponse {
  id: string
  email: string
  displayName: string
  status: UserStatus
  createdAt: string
  memberships: UserMembershipSummary[]
}

/** com.vermeg.chatops.identity.dto.CurrentUserResponse */
export interface CurrentUserResponse extends UserResponse {
  roles: string[]
  permissions: string[]
}

/** com.vermeg.chatops.identity.dto.UserUpdateRequest */
export interface UserUpdateRequest {
  displayName?: string
  active?: boolean
}

/* --------------------------------------------------------------- access */

/** com.vermeg.chatops.access.dto.RoleResponse */
export interface RoleResponse {
  id: string
  code: string
  name: string
  description: string | null
  system: boolean
  createdAt: string
  updatedAt: string
}

/** com.vermeg.chatops.access.dto.RoleCreateRequest */
export interface RoleCreateRequest {
  code: string
  name: string
  description?: string
}

/** com.vermeg.chatops.access.dto.RoleUpdateRequest */
export interface RoleUpdateRequest {
  name: string
  description?: string
}

/** com.vermeg.chatops.access.dto.PermissionResponse */
export interface PermissionResponse {
  id: string
  code: string
  name: string
  description: string | null
  createdAt: string
  updatedAt: string
}

/** com.vermeg.chatops.access.dto.PermissionMatrixResponse.RolePermissions */
export interface RolePermissionsRow {
  id: string
  code: string
  name: string
  system: boolean
  permissionCodes: string[]
}

/** com.vermeg.chatops.access.dto.PermissionMatrixResponse */
export interface PermissionMatrixResponse {
  permissions: PermissionResponse[]
  roles: RolePermissionsRow[]
}

/** com.vermeg.chatops.access.dto.PermissionCreateRequest */
export interface PermissionCreateRequest {
  code: string
  name: string
  description?: string
}

/** com.vermeg.chatops.access.dto.PermissionUpdateRequest */
export interface PermissionUpdateRequest {
  name: string
  description?: string
}

/* -------------------------------------------------------------- tenancy */

/** com.vermeg.chatops.tenancy.dto.TenantResponse */
export interface TenantResponse {
  id: string
  name: string
  active: boolean
  createdAt: string
  updatedAt: string
}

/** com.vermeg.chatops.tenancy.dto.CreateTenantRequest */
export interface CreateTenantRequest {
  name: string
}

/** com.vermeg.chatops.tenancy.entity.EnvironmentType */
export type EnvironmentType = "STANDALONE" | "CLUSTER"

/** com.vermeg.chatops.tenancy.dto.TenantSummaryResponse */
export interface TenantSummaryResponse {
  id: string
  name: string
}

/** com.vermeg.chatops.tenancy.dto.EnvironmentResponse */
export interface EnvironmentResponse {
  id: string
  name: string
  type: EnvironmentType
  tenant: TenantSummaryResponse
  createdAt: string
  updatedAt: string
}

/** com.vermeg.chatops.tenancy.dto.CreateEnvironmentRequest / UpdateEnvironmentRequest */
export interface EnvironmentWriteRequest {
  name: string
  type: EnvironmentType
}

/* --------------------------------------------------------------- errors */

/** com.vermeg.chatops.common.dto.ApiErrorResponse */
export interface ApiErrorResponse {
  timestamp: string
  status: number
  error: string
  message: string
  path: string
  validationErrors: Record<string, string>
}
