import { apiClient } from "./apiClient"
import type { EnvironmentResponse, EnvironmentWriteRequest } from "../types/api"

/**
 * /api/v1/tenants/{tenantId}/environments — see EnvironmentController.
 * Environments are always scoped to a tenant; there is no global list endpoint.
 */
export const environmentsApi = {
  list: (tenantId: string) =>
    apiClient.get<EnvironmentResponse[]>(`/api/v1/tenants/${tenantId}/environments`),

  getById: (tenantId: string, environmentId: string) =>
    apiClient.get<EnvironmentResponse>(`/api/v1/tenants/${tenantId}/environments/${environmentId}`),

  create: (tenantId: string, request: EnvironmentWriteRequest) =>
    apiClient.post<EnvironmentResponse>(`/api/v1/tenants/${tenantId}/environments`, request),

  update: (tenantId: string, environmentId: string, request: EnvironmentWriteRequest) =>
    apiClient.put<EnvironmentResponse>(
      `/api/v1/tenants/${tenantId}/environments/${environmentId}`,
      request,
    ),

  remove: (tenantId: string, environmentId: string) =>
    apiClient.delete<void>(`/api/v1/tenants/${tenantId}/environments/${environmentId}`),
}
