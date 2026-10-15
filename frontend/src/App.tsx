import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Dashboard } from "@/pages/Dashboard";
import { ISOsPage } from "@/pages/ISOsPage";
import { RecipesPage } from "@/pages/RecipesPage";
import { BuildsPage } from "@/pages/BuildsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { Toaster } from "@/components/Toaster";
import { useAuth } from "@/hooks/useAuth";

export function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="loading-spinner" data-testid="loading-spinner" />
      </div>
    );
  }

  return (
    <>
      {user && <Layout />}
      <Routes>
        {user ? (
          <>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/isos" element={<ISOsPage />} />
            <Route path="/recipes" element={<RecipesPage />} />
            <Route path="/builds" element={<BuildsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </>
        ) : (
          <Route path="*" element={<Navigate to="/login" replace />} />
        )}
      </Routes>
      <Toaster />
    </>
  );
}