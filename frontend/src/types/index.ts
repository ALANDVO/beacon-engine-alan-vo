export type UserRole = "viewer" | "operator" | "admin";

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  roles: UserRole[];
  created_at: string;
  updated_at: string;
}

export interface ISOImage {
  id: string;
  owner_id: string;
  filename: string;
  sha256: string;
  size_bytes: number;
  version: string | null;
  edition: string | null;
  build_number: number | null;
  architecture: string | null;
  language: string | null;
  storage_path: string;
  created_at: string;
}

export interface BuildRecipe {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  version: number;
  recipe_json: string;
  created_at: string;
  updated_at: string;
}

export type BuildStage =
  | "pending"
  | "mounting"
  | "inventory"
  | "component_cleanup"
  | "registry_tweaks"
  | "unmounting"
  | "iso_creation"
  | "completed"
  | "failed";

export interface BuildJob {
  id: string;
  owner_id: string;
  iso_id: string;
  recipe_id: string;
  stage: BuildStage;
  progress: number;
  status_message: string | null;
  error_message: string | null;
  log_path: string | null;
  output_iso_path: string | null;
  output_iso_sha256: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface BuildLogEntry {
  id: string;
  job_id: string;
  stage: BuildStage;
  timestamp: string;
  level: string;
  message: string;
}

export interface BuildLogResponse {
  logs: BuildLogEntry[];
  total: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface RecipeJson {
  components: string[];
  removals: string[];
  registry_tweaks: RegistryTweak[];
  unattend_snippets: string[];
}

export interface RegistryTweak {
  path: string;
  name: string;
  type: "STRING" | "DWORD" | "QWORD" | "BINARY" | "EXPAND_SZ" | "MULTI_SZ";
  data: string | number;
}