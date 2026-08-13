import { apiClient } from "./apiClient"
import type { CreateTenantRequest, TenantResponse } from "../types/api"

/**
 * /api/v1/tenants — see TenantController.
 *
 * list() returns only the tenants the caller is a member of (any authenticated
 * user may call it); create() requires TENANT_CREATE. There is no update or
 * delete endpoint on the backend.
 */
export const tenantsApi = {
  list: () => apiClient.get<TenantResponse[]>("/api/v1/tenants"),
  create: (request: CreateTenantRequest) => apiClient.post<TenantResponse>("/api/v1/tenants", request),
}
