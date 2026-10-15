import { useEffect, useState } from "react";
import { useToast } from "@/hooks/useToast";
import { isosApi } from "@/api/client";
import { Card, Button, Input } from "@/components/ui";
import { Upload, Trash2, Search, Loader2, FileBox } from "lucide-react";
import { useDropzone } from "react-dropzone";
import clsx from "clsx";
import type { ISOImage } from "@/types";

export function ISOsPage() {
  const { addToast } = useToast();
  const [isos, setIsos] = useState<ISOImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");

  const fetchIsos = async () => {
    setLoading(true);
    try {
      const response = await isosApi.list(page, 20);
      setIsos(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch {
      addToast({ type: "error", message: "Failed to load ISOs" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIsos();
  }, [page]);

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    setUploading(true);
    try {
      const response = await isosApi.upload(acceptedFiles[0]);
      addToast({ type: "success", message: `Uploaded ${response.data.filename}` });
      fetchIsos();
    } catch {
      addToast({ type: "error", message: "Upload failed" });
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/octet-stream": [".iso"], "application/x-iso9660-image": [".iso"] },
    multiple: false,
    disabled: uploading,
  });

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this ISO?")) return;
    try {
      await isosApi.delete(id);
      addToast({ type: "success", message: "ISO deleted" });
      fetchIsos();
    } catch {
      addToast({ type: "error", message: "Delete failed" });
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">ISO Images</h1>
          <p className="text-slate-400 mt-1">Manage Windows ISO images for builds</p>
        </div>
        <div {...getRootProps()} className={clsx("dropzone", isDragActive && "active")}>
          <input {...getInputProps()} />
          <Upload className="dropzone-icon" aria-hidden="true" />
          <p className="text-slate-400">{isDragActive ? "Drop ISO here..." : "Drag & drop ISO file, or click to browse"}</p>
          <p className="text-xs text-slate-500 mt-1">.iso files only</p>
        </div>
      </div>

      <Card>
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" aria-hidden="true" />
            <Input
              placeholder="Search ISOs..."
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
        ) : isos.length === 0 ? (
          <div className="empty-state">
            <FileBox className="empty-state-icon" aria-hidden="true" />
            <h3 className="text-lg font-medium text-white mb-1">No ISOs uploaded</h3>
            <p className="text-slate-400">Upload a Windows 11 ISO to get started</p>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Version</th>
                    <th>Edition</th>
                    <th>Build</th>
                    <th>Size</th>
                    <th>SHA256</th>
                    <th>Uploaded</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {isos.map((iso) => (
                    <tr key={iso.id}>
                      <td className="font-mono text-sm">{iso.filename}</td>
                      <td>{iso.version || "-"}</td>
                      <td>{iso.edition || "-"}</td>
                      <td>{iso.build_number?.toString() || "-"}</td>
                      <td className="font-mono text-sm">{formatBytes(iso.size_bytes)}</td>
                      <td className="font-mono text-xs max-w-[200px] truncate">{iso.sha256}</td>
                      <td className="text-slate-400">{new Date(iso.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(iso.id)} aria-label={`Delete ${iso.filename}`}>
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