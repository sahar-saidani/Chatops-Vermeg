import { apiClient } from "./apiClient"
import type { CurrentUserResponse, UserResponse, UserUpdateRequest } from "../types/api"

/**
 * /api/v1/users — see UserController.
 *
 * There is deliberately no create(): the backend has no create-user endpoint,
 * users come into existence through POST /api/v1/auth/invitations.
 */
export const usersApi = {
  list: () => apiClient.get<UserResponse[]>("/api/v1/users"),
  getById: (id: string) => apiClient.get<UserResponse>(`/api/v1/users/${id}`),
  me: () => apiClient.get<CurrentUserResponse>("/api/v1/users/me"),
  update: (id: string, request: UserUpdateRequest) =>
    apiClient.put<UserResponse>(`/api/v1/users/${id}`, request),
  /** Soft delete — the backend disables the user rather than removing the row. */
  remove: (id: string) => apiClient.delete<void>(`/api/v1/users/${id}`),
}
