import { apiClient } from "./apiClient"
import type {
  PermissionCreateRequest,
  PermissionResponse,
  PermissionUpdateRequest,
} from "../types/api"

/**
 * /api/v1/permissions — see PermissionController. All operations require
 * PERMISSION_MANAGE. There is no delete endpoint on the backend, so none here.
 */
export const permissionsApi = {
  list: () => apiClient.get<PermissionResponse[]>("/api/v1/permissions"),
  getById: (id: string) => apiClient.get<PermissionResponse>(`/api/v1/permissions/${id}`),
  create: (request: PermissionCreateRequest) =>
    apiClient.post<PermissionResponse>("/api/v1/permissions", request),
  update: (id: string, request: PermissionUpdateRequest) =>
    apiClient.put<PermissionResponse>(`/api/v1/permissions/${id}`, request),
}
