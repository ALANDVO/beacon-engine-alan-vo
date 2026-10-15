import { useEffect, useState } from "react";
import { useToast } from "@/hooks/useToast";
import { buildsApi, isosApi, recipesApi } from "@/api/client";
import { Card, Button, Badge, ProgressBar, Input, Label } from "@/components/ui";
import { Plus, Trash2, Loader2, Search, Hammer, RefreshCw, X } from "lucide-react";
import clsx from "clsx";
import type { BuildJob, BuildStage, ISOImage, BuildRecipe } from "@/types";

const stageOrder: BuildStage[] = [
  "pending",
  "mounting",
  "inventory",
  "component_cleanup",
  "registry_tweaks",
  "unmounting",
  "iso_creation",
  "completed",
  "failed",
];

const stageLabels: Record<BuildStage, string> = {
  pending: "Pending",
  mounting: "Mounting",
  inventory: "Inventory",
  component_cleanup: "Component Cleanup",
  registry_tweaks: "Registry Tweaks",
  unmounting: "Unmounting",
  iso_creation: "ISO Creation",
  completed: "Completed",
  failed: "Failed",
};

export function BuildsPage() {
  const { addToast } = useToast();
  const [builds, setBuilds] = useState<BuildJob[]>([]);
  const [isos, setIsos] = useState<ISOImage[]>([]);
  const [recipes, setRecipes] = useState<BuildRecipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stageFilter, setStageFilter] = useState<string>("");

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({ iso_id: "", recipe_id: "" });

  const fetchBuilds = async () => {
    setLoading(true);
    try {
      const response = await buildsApi.list(page, 20, stageFilter || undefined);
      setBuilds(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch {
      addToast({ type: "error", message: "Failed to load builds" });
    } finally {
      setLoading(false);
    }
  };

  const fetchIsosAndRecipes = async () => {
    try {
      const [isoRes, recipeRes] = await Promise.all([
        isosApi.list(1, 100),
        recipesApi.list(1, 100),
      ]);
      setIsos(isoRes.data.items);
      setRecipes(recipeRes.data.items);
    } catch {
      addToast({ type: "error", message: "Failed to load ISOs/Recipes" });
    }
  };

  useEffect(() => {
    fetchBuilds();
    fetchIsosAndRecipes();
  }, [page, stageFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.iso_id || !formData.recipe_id) return;
    setCreating(true);
    try {
      await buildsApi.create({ iso_id: formData.iso_id, recipe_id: formData.recipe_id });
      addToast({ type: "success", message: "Build started" });
      setShowCreateModal(false);
      setFormData({ iso_id: "", recipe_id: "" });
      fetchBuilds();
    } catch {
      addToast({ type: "error", message: "Failed to start build" });
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this build job?")) return;
    try {
      await buildsApi.delete(id);
      addToast({ type: "success", message: "Build deleted" });
      fetchBuilds();
    } catch {
      addToast({ type: "error", message: "Delete failed" });
    }
  };


  const formatStage = (stage: BuildStage) => stageLabels[stage] || stage;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Build Jobs</h1>
          <p className="text-slate-400 mt-1">Orchestrate and monitor Windows image builds</p>
        </div>
        <Button onClick={() => { setShowCreateModal(true); fetchIsosAndRecipes(); }}>
          <Plus className="w-4 h-4" /> New Build
        </Button>
      </div>

      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" aria-hidden="true" />
            <Input
              placeholder="Filter by stage..."
              value={stageFilter}
              onChange={(e) => { setStageFilter(e.target.value); setPage(1); }}
              className="pl-10"
              list="stages"
            />
            <datalist id="stages">
              {stageOrder.map((s) => <option key={s} value={s} />)}
            </datalist>
          </div>
          <Button variant="secondary" onClick={fetchBuilds} disabled={loading}>
            <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </Card>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="text-lg font-semibold">Start New Build</h2>
              <Button variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
            <form onSubmit={handleCreate} className="modal-body space-y-4">
              <div>
                <Label htmlFor="iso_id">ISO Image *</Label>
                <select
                  id="iso_id"
                  className="input"
                  value={formData.iso_id}
                  onChange={(e) => setFormData({ ...formData, iso_id: e.target.value })}
                  required
                >
                  <option value="">Select ISO...</option>
                  {isos.map((iso) => (
                    <option key={iso.id} value={iso.id}>{iso.filename} ({iso.version || "unknown"})</option>
                  ))}
                </select>
              </div>
              <div>
                <Label htmlFor="recipe_id">Build Recipe *</Label>
                <select
                  id="recipe_id"
                  className="input"
                  value={formData.recipe_id}
                  onChange={(e) => setFormData({ ...formData, recipe_id: e.target.value })}
                  required
                >
                  <option value="">Select Recipe...</option>
                  {recipes.map((recipe) => (
                    <option key={recipe.id} value={recipe.id}>{recipe.name} (v{recipe.version})</option>
                  ))}
                </select>
              </div>
              <div className="modal-footer">
                <Button type="button" variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button type="submit" disabled={creating}>
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Hammer className="w-4 h-4" />}
                  Start Build
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" aria-hidden="true" />
            <span className="ml-2 text-slate-400">Loading...</span>
          </div>
        ) : builds.length === 0 ? (
          <div className="empty-state">
            <Hammer className="empty-state-icon" aria-hidden="true" />
            <h3 className="text-lg font-medium text-white mb-1">No build jobs</h3>
            <p className="text-slate-400">Create a build job to start customizing your Windows image</p>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>ISO</th>
                    <th>Recipe</th>
                    <th>Stage</th>
                    <th>Progress</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {builds.map((build) => (
                    <tr key={build.id}>
                      <td className="font-mono text-xs">{build.id.slice(0, 8)}...</td>
                      <td className="text-sm max-w-[150px] truncate">{build.iso_id.slice(0, 8)}...</td>
                      <td className="text-sm max-w-[150px] truncate">{build.recipe_id.slice(0, 8)}...</td>
                      <td><Badge variant={build.stage}>{formatStage(build.stage)}</Badge></td>
                      <td className="w-32">
                        <ProgressBar value={build.progress} />
                        <span className="text-xs text-slate-400 ml-1">{build.progress}%</span>
                      </td>
                      <td className="text-sm text-slate-400 max-w-[200px] truncate">{build.status_message || "-"}</td>
                      <td className="text-slate-400">{new Date(build.created_at).toLocaleString()}</td>
                      <td>
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(build.id)} aria-label={`Delete build ${build.id.slice(0, 8)}`}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <Button variant="secondary" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                  Previous
                </Button>
                <span className="text-sm text-slate-400">Page {page} of {totalPages}</span>
                <Button variant="secondary" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}