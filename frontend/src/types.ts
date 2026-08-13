/**
 * Application-level view types.
 *
 * The old `Role = 'admin' | 'devops' | 'nondevops'` union is gone: roles are
 * rows in the `roles` table (ADMIN, TENANT_ADMIN, USER, OPERATOR as seeded by
 * V3, plus whatever an administrator creates), so nothing in the UI may assume
 * a fixed set. Navigation and guards key off permission codes instead.
 */

export type Page =
  | "dashboard"
  | "chat"
  | "users"
  | "roles"
  | "permissions"
  | "tenants"
  | "environments"
  | "git"
  | "jenkins"
  | "installation"
  | "logs"
  | "infrastructure"
  | "history"
  | "settings"

/** Permission codes seeded in db/migration (V3, V4, V5, V9). */
export const PERMISSIONS = {
  tenantCreate: "TENANT_CREATE",
  roleManage: "ROLE_MANAGE",
  permissionManage: "PERMISSION_MANAGE",
  userRead: "USER_READ",
  userWrite: "USER_WRITE",
  environmentCreate: "ENVIRONMENT_CREATE",
  environmentRead: "ENVIRONMENT_READ",
  environmentUpdate: "ENVIRONMENT_UPDATE",
  environmentDelete: "ENVIRONMENT_DELETE",
} as const

/** The five agents surfaced in this UI. jira-agent exists server-side but is deliberately not exposed. */
export const AGENT_KEYS = ["git", "jenkins", "installation", "log", "infrastructure"] as const
export type AgentKey = (typeof AGENT_KEYS)[number]

export const AGENT_LABELS: Record<AgentKey, string> = {
  git: "Git",
  jenkins: "Jenkins",
  installation: "Installation",
  log: "Logs",
  infrastructure: "Infrastructure",
}
