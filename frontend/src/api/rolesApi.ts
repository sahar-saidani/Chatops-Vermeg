import { apiClient } from "./apiClient"
import type { RoleCreateRequest, RoleResponse, RoleUpdateRequest } from "../types/api"

/** /api/v1/roles — see RoleController. All operations require ROLE_MANAGE. */
export const rolesApi = {
  list: () => apiClient.get<RoleResponse[]>("/api/v1/roles"),
  getById: (id: string) => apiClient.get<RoleResponse>(`/api/v1/roles/${id}`),
  create: (request: RoleCreateRequest) => apiClient.post<RoleResponse>("/api/v1/roles", request),
  update: (id: string, request: RoleUpdateRequest) =>
    apiClient.put<RoleResponse>(`/api/v1/roles/${id}`, request),
  remove: (id: string) => apiClient.delete<void>(`/api/v1/roles/${id}`),
}
