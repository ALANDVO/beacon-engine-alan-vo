import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import type {
  User,
  ISOImage,
  BuildRecipe,
  BuildJob,
  BuildLogResponse,
  PaginatedResponse,
  HealthResponse,
  RecipeJson,
} from "@/types";

const API_BASE = "/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const healthApi = {
  check: () => api.get<HealthResponse>("/healthz"),
};

export const usersApi = {
  me: () => api.get<User>("/users/me"),
  update: (data: Partial<User>) => api.patch<User>("/users/me", data),
};

export const isosApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<PaginatedResponse<ISOImage>>("/isos", { params: { page, page_size: pageSize } }),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<ISOImage>("/isos", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  get: (id: string) => api.get<ISOImage>(`/isos/${id}`),
  delete: (id: string) => api.delete(`/isos/${id}`),
};

export const recipesApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<PaginatedResponse<BuildRecipe>>("/recipes", { params: { page, page_size: pageSize } }),
  create: (data: { name: string; description?: string; recipe_json: string }) =>
    api.post<BuildRecipe>("/recipes", data),
  get: (id: string) => api.get<BuildRecipe>(`/recipes/${id}`),
  update: (id: string, data: Partial<BuildRecipe>) =>
    api.patch<BuildRecipe>(`/recipes/${id}`, data),
  delete: (id: string) => api.delete(`/recipes/${id}`),
  clone: (id: string) => api.post<BuildRecipe>(`/recipes/${id}/clone`),
};

export const buildsApi = {
  list: (page = 1, pageSize = 20, stage?: string) =>
    api.get<PaginatedResponse<BuildJob>>("/builds", { params: { page, page_size: pageSize, stage } }),
  create: (data: { iso_id: string; recipe_id: string }) =>
    api.post<BuildJob>("/builds", data),
  get: (id: string) => api.get<BuildJob>(`/builds/${id}`),
  logs: (id: string) => api.get<BuildLogResponse>(`/builds/${id}/logs`),
  delete: (id: string) => api.delete(`/builds/${id}`),
};

export function parseRecipeJson(json: string): RecipeJson {
  try {
    const parsed = JSON.parse(json);
    return {
      components: parsed.components || [],
      removals: parsed.removals || [],
      registry_tweaks: parsed.registry_tweaks || [],
      unattend_snippets: parsed.unattend_snippets || [],
    };
  } catch {
    return { components: [], removals: [], registry_tweaks: [], unattend_snippets: [] };
  }
}

export function stringifyRecipeJson(recipe: RecipeJson): string {
  return JSON.stringify(recipe, null, 2);
}

export default api;