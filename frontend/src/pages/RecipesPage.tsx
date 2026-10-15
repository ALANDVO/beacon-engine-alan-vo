import { useEffect, useState } from "react";
import { useToast } from "@/hooks/useToast";
import { recipesApi, parseRecipeJson, stringifyRecipeJson } from "@/api/client";
import { Card, Button, Badge, Input, Textarea, Label } from "@/components/ui";
import { Plus, Trash2, Edit, Copy, Save, X, Loader2, FileCode, Search } from "lucide-react";
import type { BuildRecipe, RecipeJson } from "@/types";

export function RecipesPage() {
  const { addToast } = useToast();
  const [recipes, setRecipes] = useState<BuildRecipe[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");

  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<BuildRecipe> & { recipe_json_obj?: RecipeJson }>({
    name: "",
    description: "",
    recipe_json: "",
    recipe_json_obj: { components: [], removals: [], registry_tweaks: [], unattend_snippets: [] },
  });

  const fetchRecipes = async () => {
    setLoading(true);
    try {
      const response = await recipesApi.list(page, 20);
      setRecipes(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch {
      addToast({ type: "error", message: "Failed to load recipes" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, [page]);

  const handleEdit = (recipe: BuildRecipe) => {
    setEditingId(recipe.id);
    setFormData({
      name: recipe.name,
      description: recipe.description || "",
      recipe_json: recipe.recipe_json,
      recipe_json_obj: parseRecipeJson(recipe.recipe_json),
    });
  };

  const handleClone = async (id: string) => {
    try {
      await recipesApi.clone(id);
      addToast({ type: "success", message: "Recipe cloned" });
      fetchRecipes();
    } catch {
      addToast({ type: "error", message: "Clone failed" });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this recipe?")) return;
    try {
      await recipesApi.delete(id);
      addToast({ type: "success", message: "Recipe deleted" });
      fetchRecipes();
    } catch {
      addToast({ type: "error", message: "Delete failed" });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const json = stringifyRecipeJson(formData.recipe_json_obj!);
      const payload = {
        name: formData.name!,
        description: formData.description ?? undefined,
        recipe_json: json,
      };
      if (editingId) {
        await recipesApi.update(editingId, payload);
        addToast({ type: "success", message: "Recipe updated" });
      } else {
        await recipesApi.create(payload);
        addToast({ type: "success", message: "Recipe created" });
      }
      setEditingId(null);
      resetForm();
      fetchRecipes();
    } catch {
      addToast({ type: "error", message: editingId ? "Update failed" : "Create failed" });
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      recipe_json: "",
      recipe_json_obj: { components: [], removals: [], registry_tweaks: [], unattend_snippets: [] },
    });
  };

  const handleJsonChange = (field: keyof RecipeJson, value: unknown) => {
    setFormData((prev) => ({
      ...prev,
      recipe_json_obj: { ...prev.recipe_json_obj!, [field]: value },
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Build Recipes</h1>
          <p className="text-slate-400 mt-1">Define component removals, registry tweaks, and unattend settings</p>
        </div>
        <Button onClick={() => { setEditingId("new"); resetForm(); }}><Plus className="w-4 h-4" /> New Recipe</Button>
      </div>

      {editingId && (
        <Card className="mb-6">
          <h2 className="text-lg font-semibold mb-4">{editingId === "new" ? "Create Recipe" : "Edit Recipe"}</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input id="name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" value={formData.description || ""} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={2} />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Components to Keep</Label>
                <Textarea
                  value={formData.recipe_json_obj?.components.join("\n") || ""}
                  onChange={(e) => handleJsonChange("components", e.target.value.split("\n").filter(Boolean))}
                  rows={6}
                  placeholder="Notepad&#10;Calculator&#10;Paint"
                />
              </div>
              <div>
                <Label>Components to Remove</Label>
                <Textarea
                  value={formData.recipe_json_obj?.removals.join("\n") || ""}
                  onChange={(e) => handleJsonChange("removals", e.target.value.split("\n").filter(Boolean))}
                  rows={6}
                  placeholder="Cortana&#10;OneDrive&#10;Edge"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Registry Tweaks (JSON)</Label>
                <Textarea
                  value={JSON.stringify(formData.recipe_json_obj?.registry_tweaks || [], null, 2)}
                  onChange={(e) => {
                    try {
                      handleJsonChange("registry_tweaks", JSON.parse(e.target.value));
                    } catch { }
                  }}
                  rows={6}
                  placeholder='[{"path": "HKCU\\\\Software\\\\Test", "name": "Value", "type": "DWORD", "data": 1}]'
                />
              </div>
              <div>
                <Label>Unattend Snippets (XML)</Label>
                <Textarea
                  value={formData.recipe_json_obj?.unattend_snippets.join("\n\n") || ""}
                  onChange={(e) => handleJsonChange("unattend_snippets", e.target.value.split("\n\n").filter(Boolean))}
                  rows={6}
                  placeholder="<Settings pass='specialize'>...</Settings>"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
              <Button type="button" variant="secondary" onClick={() => { setEditingId(null); resetForm(); }}>
                <X className="w-4 h-4" /> Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {editingId === "new" ? "Create" : "Save"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" aria-hidden="true" />
            <Input
              placeholder="Search recipes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" aria-hidden="true" />
            <span className="ml-2 text-slate-400">Loading...</span>
          </div>
        ) : recipes.length === 0 ? (
          <div className="empty-state">
            <FileCode className="empty-state-icon" aria-hidden="true" />
            <h3 className="text-lg font-medium text-white mb-1">No recipes created</h3>
            <p className="text-slate-400">Create your first build recipe to define customizations</p>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Version</th>
                    <th>Components</th>
                    <th>Removals</th>
                    <th>Updated</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {recipes
                    .filter((r) => r.name.toLowerCase().includes(search.toLowerCase()) || r.description?.toLowerCase().includes(search.toLowerCase()))
                    .map((recipe) => {
                      const parsed = parseRecipeJson(recipe.recipe_json);
                      return (
                        <tr key={recipe.id}>
                          <td className="font-medium">{recipe.name}</td>
                          <td className="text-slate-400 max-w-[200px] truncate">{recipe.description || "-"}</td>
                          <td><Badge variant="pending">{recipe.version}</Badge></td>
                          <td className="text-sm">{parsed.components.length}</td>
                          <td className="text-sm">{parsed.removals.length}</td>
                          <td className="text-slate-400">{new Date(recipe.updated_at).toLocaleDateString()}</td>
                          <td>
                            <div className="flex items-center gap-1">
                              <Button variant="ghost" size="sm" onClick={() => handleEdit(recipe)} aria-label={`Edit ${recipe.name}`}>
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleClone(recipe.id)} aria-label={`Clone ${recipe.name}`}>
                                <Copy className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(recipe.id)} aria-label={`Delete ${recipe.name}`}>
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
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