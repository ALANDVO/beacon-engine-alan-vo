import { useEffect, useState } from "react";
import { healthApi } from "@/api/client";
import { Card, Badge } from "@/components/ui";
import { Server, Database, CheckCircle, Loader2 } from "lucide-react";
import clsx from "clsx";

export function Dashboard() {
  const [health, setHealth] = useState<{ status: string; version: string; environment: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await healthApi.check();
        setHealth(response.data);
      } catch (err) {
        // Error handled by setting health to null
      } finally {
        setLoading(false);
      }
    }
    fetchHealth();
  }, []);

  const statusItems = [
    { name: "API Server", status: health?.status === "ok" ? "healthy" : "unhealthy", icon: Server },
    { name: "Database", status: health?.status === "ok" ? "healthy" : "unhealthy", icon: Database },
    { name: "Authentication", status: "configured", icon: CheckCircle },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1">System overview and health status</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {statusItems.map((item) => {
          const Icon = item.icon;
          const isHealthy = item.status === "healthy" || item.status === "configured";
          return (
            <Card key={item.name}>
              <div className="flex items-start gap-3">
                <div className={clsx("p-2 rounded-lg", isHealthy ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400")}>
                  <Icon className="w-5 h-5" aria-hidden="true" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-white">{item.name}</h3>
                  <Badge className={isHealthy ? "badge-completed" : "badge-failed"}>{item.status}</Badge>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <Card>
        <h2 className="text-lg font-semibold mb-4">System Information</h2>
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <dt className="text-slate-400">Version</dt>
            <dd className="font-mono text-white">{health?.version || (loading ? <Loader2 className="w-4 h-4 animate-spin inline" /> : "Unknown")}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Environment</dt>
            <dd className="capitalize text-white">{health?.environment || "Unknown"}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Status</dt>
            <dd className={clsx("font-medium", health?.status === "ok" ? "text-green-400" : "text-red-400")}>
              {health?.status || (loading ? "Checking..." : "Unknown")}
            </dd>
          </div>
        </dl>
      </Card>

      <Card>
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <a href="/isos" className="btn btn-secondary">Upload ISO</a>
          <a href="/recipes" className="btn btn-secondary">Create Recipe</a>
          <a href="/builds" className="btn btn-primary">Start Build</a>
          <a href="/settings" className="btn btn-secondary">Settings</a>
        </div>
      </Card>
    </div>
  );
}