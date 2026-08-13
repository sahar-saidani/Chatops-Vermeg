import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import type { ReactNode } from "react"
import { ApiError, configureApiClient } from "../api/apiClient"
import { authApi } from "../api/authApi"
import { usersApi } from "../api/usersApi"
import type { CurrentUserResponse } from "../types/api"

const ACCESS_TOKEN_KEY = "chatops.accessToken"
const REFRESH_TOKEN_KEY = "chatops.refreshToken"

interface StoredTokens {
  accessToken: string
  refreshToken: string
}

/**
 * "Remember me" picks the storage: localStorage survives a browser restart,
 * sessionStorage dies with the tab. Reads check both so a rehydrate does not
 * need to know which one was used at login time.
 */
function readStoredTokens(): StoredTokens | null {
  const accessToken =
    window.localStorage.getItem(ACCESS_TOKEN_KEY) ?? window.sessionStorage.getItem(ACCESS_TOKEN_KEY)
  const refreshToken =
    window.localStorage.getItem(REFRESH_TOKEN_KEY) ?? window.sessionStorage.getItem(REFRESH_TOKEN_KEY)
  if (!accessToken) return null
  return { accessToken, refreshToken: refreshToken ?? "" }
}

function writeStoredTokens(tokens: StoredTokens, remember: boolean): void {
  const store = remember ? window.localStorage : window.sessionStorage
  const other = remember ? window.sessionStorage : window.localStorage
  other.removeItem(ACCESS_TOKEN_KEY)
  other.removeItem(REFRESH_TOKEN_KEY)
  store.setItem(ACCESS_TOKEN_KEY, tokens.accessToken)
  store.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken)
}

function clearStoredTokens(): void {
  for (const store of [window.localStorage, window.sessionStorage]) {
    store.removeItem(ACCESS_TOKEN_KEY)
    store.removeItem(REFRESH_TOKEN_KEY)
  }
}

export interface AuthContextValue {
  user: CurrentUserResponse | null
  token: string | null
  roles: string[]
  permissions: string[]
  isAuthenticated: boolean
  /** True while the stored token is being exchanged for a profile on first load. */
  isInitializing: boolean
  login: (email: string, password: string, remember: boolean) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  hasRole: (...codes: string[]) => boolean
  hasPermission: (...codes: string[]) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<CurrentUserResponse | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)

  // The API client reads the token through a ref so a token change never has
  // to re-run configureApiClient, and so requests fired during a render always
  // see the newest value.
  const tokenRef = useRef<string | null>(null)
  tokenRef.current = token

  const logout = useCallback(() => {
    clearStoredTokens()
    tokenRef.current = null
    setToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    configureApiClient({
      getToken: () => tokenRef.current,
      onUnauthorized: () => {
        clearStoredTokens()
        tokenRef.current = null
        setToken(null)
        setUser(null)
      },
    })
  }, [])

  // Rehydrate: a stored token is only trusted once /users/me confirms it.
  useEffect(() => {
    const stored = readStoredTokens()
    if (!stored) {
      setIsInitializing(false)
      return
    }
    tokenRef.current = stored.accessToken
    setToken(stored.accessToken)

    let cancelled = false
    usersApi
      .me()
      .then((profile) => {
        if (!cancelled) setUser(profile)
      })
      .catch((error: unknown) => {
        if (cancelled) return
        // A rejected token is not an app error, it just means "sign in again".
        if (error instanceof ApiError && error.kind === "unauthorized") return
        clearStoredTokens()
        tokenRef.current = null
        setToken(null)
      })
      .finally(() => {
        if (!cancelled) setIsInitializing(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string, remember: boolean) => {
    const tokens = await authApi.login({ email, password })
    writeStoredTokens({ accessToken: tokens.accessToken, refreshToken: tokens.refreshToken }, remember)
    tokenRef.current = tokens.accessToken
    setToken(tokens.accessToken)
    try {
      setUser(await usersApi.me())
    } catch (error) {
      // Leaving a half-authenticated state around would strand the user on a
      // dashboard with no roles, so unwind the whole login instead.
      clearStoredTokens()
      tokenRef.current = null
      setToken(null)
      throw error
    }
  }, [])

  const refreshUser = useCallback(async () => {
    if (!tokenRef.current) return
    setUser(await usersApi.me())
  }, [])

  const roles = user?.roles ?? []
  const permissions = user?.permissions ?? []

  const hasRole = useCallback(
    (...codes: string[]) => codes.some((code) => (user?.roles ?? []).includes(code)),
    [user],
  )

  const hasPermission = useCallback(
    (...codes: string[]) => codes.some((code) => (user?.permissions ?? []).includes(code)),
    [user],
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      roles,
      permissions,
      isAuthenticated: Boolean(token && user),
      isInitializing,
      login,
      logout,
      refreshUser,
      hasRole,
      hasPermission,
    }),
    [user, token, roles, permissions, isInitializing, login, logout, refreshUser, hasRole, hasPermission],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used inside an AuthProvider")
  return context
}

export default AuthProvider
