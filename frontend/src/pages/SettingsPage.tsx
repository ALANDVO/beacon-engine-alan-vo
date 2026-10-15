import { useEffect, useState } from "react";
import { useToast } from "@/hooks/useToast";
import { usersApi, healthApi } from "@/api/client";
import { Card, Button, Input, Label, Badge } from "@/components/ui";
import { User, Server, Database, Save, Loader2, Key, Shield } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import clsx from "clsx";

export function SettingsPage() {
  const { addToast } = useToast();
  const { user, setUser } = useAuth();
  const [saving, setSaving] = useState(false);
  const [health, setHealth] = useState<{ status: string; version: string; environment: string } | null>(null);

  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
  });

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await healthApi.check();
        setHealth(response.data);
      } catch { }
    }
    fetchHealth();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await usersApi.update({ name: formData.name });
      setUser(response.data);
      addToast({ type: "success", message: "Settings saved" });
    } catch {
      addToast({ type: "error", message: "Failed to save settings" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Configure your account and view system information</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
              <User className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-semibold">Account</h2>
          </div>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label htmlFor="name">Display Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={formData.email} disabled />
            </div>
            <div>
              <Label>Roles</Label>
              <div className="flex flex-wrap gap-2">
                {user?.roles.map((role) => (
                  <Badge key={role} variant="pending">{role}</Badge>
                ))}
              </div>
            </div>
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Save Changes
            </Button>
          </form>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400">
              <Server className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-semibold">System Information</h2>
          </div>
          <dl className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <dt className="text-slate-400">API Version</dt>
              <dd className="font-mono text-white">{health?.version || "Unknown"}</dd>
              <dt className="text-slate-400">Environment</dt>
              <dd className="capitalize text-white">{health?.environment || "Unknown"}</dd>
              <dt className="text-slate-400">Status</dt>
              <dd className={clsx("font-medium", health?.status === "ok" ? "text-green-400" : "text-red-400")}>
                {health?.status || "Unknown"}
              </dd>
            </div>
          </dl>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-green-500/20 text-green-400">
              <Database className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-semibold">Database</h2>
          </div>
          <dl className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <dt className="text-slate-400">Type</dt>
              <dd className="text-white">SQLite</dd>
              <dt className="text-slate-400">Location</dt>
              <dd className="font-mono text-white">./data/beacon.db</dd>
            </div>
          </dl>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-orange-500/20 text-orange-400">
              <Shield className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-semibold">Authentication</h2>
          </div>
          <dl className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <dt className="text-slate-400">Mode</dt>
              <dd className="text-white">Demo Mode (Local)</dd>
              <dt className="text-slate-400">OIDC Provider</dt>
              <dd className="text-slate-400">Not configured</dd>
            </div>
            <p className="text-slate-400 text-sm">
              Demo mode is enabled for local development. Configure OIDC settings in the backend .env
              to enable production authentication with Keycloak.
            </p>
          </dl>
        </Card>

        <Card>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
              <Key className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-semibold">LLM Configuration</h2>
          </div>
          <dl className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <dt className="text-slate-400">Provider</dt>
              <dd className="text-white">OpenAI-compatible</dd>
              <dt className="text-slate-400">Model</dt>
              <dd className="text-slate-400">Not configured</dd>
              <dt className="text-slate-400">Base URL</dt>
              <dd className="text-slate-400">Not configured</dd>
            </div>
            <p className="text-slate-400 text-sm">
              LLM features are optional. Configure LLM_API_KEY, LLM_PROVIDER, LLM_MODEL, and LLM_BASE_URL
              in the backend .env to enable AI-assisted build recipe generation and analysis.
            </p>
          </dl>
        </Card>
      </div>
    </div>
  );
}
