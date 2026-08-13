/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Spring Boot REST API base URL. Falls back to http://localhost:8080. */
  readonly VITE_API_URL?: string
  /** FastAPI LLM orchestrator base URL. Falls back to http://localhost:8100. */
  readonly VITE_ORCHESTRATOR_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
