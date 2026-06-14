import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { Eye, Upload, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

interface CableResult {
  diameter_mm: number;
  status: string;
  voltage_class: string;
  cable_type: string;
  details: Record<string, string>;
}

interface ImageResult {
  filename: string;
  cables: CableResult[];
  annotated_image: string | null;
  error?: string;
}

async function runVisionInspect(files: File[]): Promise<{ results: ImageResult[] }> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch("/api/vision/inspect", { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function VisionPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [dragover, setDragover] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  const mutation = useMutation({ mutationFn: runVisionInspect });

  const handleFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return;
    const valid = Array.from(incoming).filter((f) =>
      ["image/jpeg", "image/png", "image/jpg"].includes(f.type)
    );
    setFiles((prev) => [...prev, ...valid]);
  }, []);

  const removeFile = (i: number) =>
    setFiles((prev) => prev.filter((_, idx) => idx !== i));

  const handleSubmit = () => {
    if (!files.length) return;
    mutation.mutate(files);
  };

  const results = mutation.data?.results ?? [];

  return (
    <>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-icon">
          <Eye size={18} />
        </div>
        <div className="page-header-text">
          <h1>Vision Inspection</h1>
          <p>YOLOv8-seg cable cross-section analysis & defect detection</p>
        </div>
      </div>

      <div className="page-body">
        {/* Upload */}
        <div className="card mb-4">
          <p className="card-title">
            <Upload size={14} />
            Upload Cable Images
          </p>

          <div
            className={`upload-zone ${dragover ? "dragover" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
            onDragLeave={() => setDragover(false)}
            onDrop={(e) => { e.preventDefault(); setDragover(false); handleFiles(e.dataTransfer.files); }}
          >
            <input
              type="file"
              accept="image/jpeg,image/png,image/jpg"
              multiple
              onChange={(e) => handleFiles(e.target.files)}
            />
            <Upload className="upload-icon" />
            <h3>Drop cable images here</h3>
            <p>JPG or PNG · Multiple files supported</p>
          </div>

          {files.length > 0 && (
            <div className="mt-4 flex flex-col gap-2">
              {files.map((f, i) => (
                <div key={i} className="flex items-center justify-between" style={{ padding: "10px 14px", background: "var(--bg-surface)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                  <span className="text-sm">{f.name}</span>
                  <button className="btn btn-sm btn-ghost" onClick={() => removeFile(i)} style={{ padding: "4px 10px" }}>✕</button>
                </div>
              ))}

              <button
                className="btn btn-primary btn-lg mt-4 w-full"
                onClick={handleSubmit}
                disabled={mutation.isPending}
              >
                {mutation.isPending ? (
                  <><span className="spinner" style={{ width: 18, height: 18 }} /> Analyzing with YOLOv8-seg…</>
                ) : (
                  <><Eye size={18} /> Start AI Segmentation Analysis</>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Results */}
        {mutation.isError && (
          <div className="alert alert-danger mt-4">
            <AlertTriangle size={16} />
            <span>Error: {(mutation.error as Error).message}</span>
          </div>
        )}

        {results.length > 0 && (
          <div className="result-section">
            {/* Tabs */}
            {results.length > 1 && (
              <div className="tabs">
                {results.map((r, i) => (
                  <button
                    key={i}
                    className={`tab-btn ${activeTab === i ? "active" : ""}`}
                    onClick={() => setActiveTab(i)}
                  >
                    Image {i + 1}: {r.filename}
                  </button>
                ))}
              </div>
            )}

            {results.map((result, i) => (
              <div key={i} style={{ display: activeTab === i || results.length === 1 ? "block" : "none" }}>
                {result.error ? (
                  <div className="alert alert-danger">
                    <XCircle size={16} />
                    <span>{result.error}</span>
                  </div>
                ) : result.cables.length === 0 ? (
                  <div className="alert alert-warning">
                    <AlertTriangle size={16} />
                    <span>No cables detected in this image.</span>
                  </div>
                ) : (
                  <>
                    <div className="result-grid">
                      {/* Annotated image */}
                      {result.annotated_image && (
                        <div>
                          <p className="card-title" style={{ marginBottom: 12 }}>Segmentation Output</p>
                          <div className="image-preview">
                            <img
                              src={`data:image/jpeg;base64,${result.annotated_image}`}
                              alt="Annotated cable"
                            />
                          </div>
                        </div>
                      )}

                      {/* Metrics */}
                      <div className="flex flex-col gap-4">
                        <p className="card-title">Inspection Report</p>
                        {result.cables.map((cable, ci) => (
                          <div key={ci} className="card" style={{ padding: 16 }}>
                            <div className="metrics-grid" style={{ marginBottom: 16 }}>
                              <div className="metric-card">
                                <p className="metric-label">Diameter</p>
                                <p className="metric-value">{cable.diameter_mm}</p>
                                <p className="metric-sub">mm</p>
                              </div>
                              <div className="metric-card">
                                <p className="metric-label">QC Status</p>
                                <p className="metric-value" style={{ fontSize: "1rem" }}>
                                  {cable.status.includes("PASS")
                                    ? <CheckCircle size={24} color="var(--success)" />
                                    : <XCircle size={24} color="var(--danger)" />}
                                </p>
                                <span className={`metric-badge ${cable.status.includes("PASS") ? "badge-success" : "badge-danger"}`}>
                                  {cable.status}
                                </span>
                              </div>
                            </div>

                            <div className="metrics-grid">
                              <div className="metric-card">
                                <p className="metric-label">Voltage Class</p>
                                <p className="metric-value" style={{ fontSize: "0.85rem", fontFamily: "inherit" }}>{cable.voltage_class.split("(")[0].trim()}</p>
                              </div>
                              <div className="metric-card">
                                <p className="metric-label">Cable Type</p>
                                <p className="metric-value" style={{ fontSize: "0.85rem", fontFamily: "inherit" }}>{cable.cable_type}</p>
                              </div>
                            </div>

                            <div className="divider" />
                            <p className="card-title">Full Technical Details</p>
                            <table className="data-table">
                              <tbody>
                                {Object.entries(cable.details).map(([k, v]) => (
                                  <tr key={k}>
                                    <td style={{ color: "var(--text-muted)", width: "40%" }}>{k}</td>
                                    <td>{v}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
