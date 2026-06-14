import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { FileText, Upload, AlertTriangle, CheckCircle, XCircle, Tag } from "lucide-react";

interface ValidationResult {
  valid: boolean;
  status: string;
  errors: string[];
  missing: string[];
}

interface OcrResult {
  filename: string;
  extracted_specs: Record<string, unknown>;
  correction_log: string[];
  validation: ValidationResult;
  category: string;
  keywords: Record<string, unknown>;
  error?: string;
}

async function runOcrAnalyze(files: File[]): Promise<{ results: OcrResult[] }> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch("/api/ocr/analyze", { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function flattenKeywords(kw: Record<string, unknown>): string[] {
  const out: string[] = [];
  for (const v of Object.values(kw)) {
    if (Array.isArray(v)) out.push(...v.map(String));
    else if (v) out.push(String(v));
  }
  return out;
}

export default function OcrPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [dragover, setDragover] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  const mutation = useMutation({ mutationFn: runOcrAnalyze });

  const handleFiles = useCallback((fl: FileList | null) => {
    if (!fl) return;
    setFiles((prev) => [...prev, ...Array.from(fl)]);
  }, []);

  const results = mutation.data?.results ?? [];

  return (
    <>
      <div className="page-header">
        <div className="page-header-icon" style={{ background: "rgba(139,92,246,0.15)", borderColor: "rgba(139,92,246,0.3)", color: "#c4b5fd" }}>
          <FileText size={18} />
        </div>
        <div className="page-header-text">
          <h1>Datasheet / OCR Analysis</h1>
          <p>Extract specs, validate IEC standards, and generate cable keywords</p>
        </div>
      </div>

      <div className="page-body">
        <div className="card mb-4">
          <p className="card-title"><Upload size={14} />Upload Datasheets</p>
          <div
            className={`upload-zone ${dragover ? "dragover" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
            onDragLeave={() => setDragover(false)}
            onDrop={(e) => { e.preventDefault(); setDragover(false); handleFiles(e.dataTransfer.files); }}
          >
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.docx"
              multiple
              onChange={(e) => handleFiles(e.target.files)}
            />
            <Upload className="upload-icon" style={{ color: "#a78bfa" }} />
            <h3>Drop datasheets here</h3>
            <p>PDF · PNG · JPG · DOCX · Multiple files supported</p>
          </div>

          {files.length > 0 && (
            <div className="mt-4">
              {files.map((f, i) => (
                <div key={i} className="flex items-center justify-between mt-2" style={{ padding: "10px 14px", background: "var(--bg-surface)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                  <span className="text-sm">{f.name}</span>
                  <button className="btn btn-sm btn-ghost" onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}>✕</button>
                </div>
              ))}
              <button
                className="btn btn-lg w-full mt-4"
                style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)", color: "#fff", boxShadow: "0 2px 12px rgba(124,58,237,0.3)" }}
                onClick={() => mutation.mutate(files)}
                disabled={mutation.isPending}
              >
                {mutation.isPending
                  ? <><span className="spinner" style={{ width: 18, height: 18 }} /> Running OCR Pipeline…</>
                  : <><FileText size={18} /> Extract & Validate All</>}
              </button>
            </div>
          )}
        </div>

        {mutation.isError && (
          <div className="alert alert-danger"><AlertTriangle size={16} /><span>{(mutation.error as Error).message}</span></div>
        )}

        {results.length > 0 && (
          <div className="result-section">
            {results.length > 1 && (
              <div className="tabs">
                {results.map((r, i) => (
                  <button key={i} className={`tab-btn ${activeTab === i ? "active" : ""}`} onClick={() => setActiveTab(i)}>
                    Doc {i + 1}: {r.filename}
                  </button>
                ))}
              </div>
            )}

            {results.map((result, i) => (
              <div key={i} style={{ display: activeTab === i || results.length === 1 ? "block" : "none" }}>
                {result.error ? (
                  <div className="alert alert-danger"><XCircle size={16} /><span>{result.error}</span></div>
                ) : (
                  <div className="flex flex-col gap-6">
                    {/* Validation banner */}
                    <div className={`alert ${result.validation.valid ? "alert-success" : result.validation.status === "NOT READY" ? "alert-danger" : "alert-warning"}`}>
                      {result.validation.valid ? <CheckCircle size={16} /> : <XCircle size={16} />}
                      <div>
                        <strong>Validation Status: {result.validation.status}</strong>
                        {result.validation.errors?.map((e, j) => <p key={j} className="mt-2">❌ {e}</p>)}
                        {result.validation.missing?.map((m, j) => <p key={j} className="mt-2">⚠️ {m}</p>)}
                      </div>
                    </div>

                    <div className="result-grid">
                      {/* Extracted specs */}
                      <div className="card">
                        <p className="card-title">Extracted Specifications</p>
                        <table className="data-table">
                          <tbody>
                            {Object.entries(result.extracted_specs).map(([k, v]) => (
                              <tr key={k}>
                                <td style={{ color: "var(--text-muted)", textTransform: "capitalize" }}>{k.replace(/_/g, " ")}</td>
                                <td className="font-mono">{v != null ? String(v) : <span className="text-muted">—</span>}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        {result.correction_log.length > 0 && (
                          <details className="mt-4">
                            <summary className="text-sm text-muted" style={{ cursor: "pointer" }}>
                              🛠 {result.correction_log.length} auto-corrections applied
                            </summary>
                            <div className="code-block mt-2">
                              {result.correction_log.map((l, j) => <div key={j}>• {l}</div>)}
                            </div>
                          </details>
                        )}
                      </div>

                      {/* Keywords & category */}
                      <div className="flex flex-col gap-4">
                        <div className="card">
                          <p className="card-title"><Tag size={14} />Category</p>
                          <span className="metric-badge badge-accent" style={{ fontSize: "0.875rem", padding: "6px 14px" }}>
                            {result.category || "Uncategorized"}
                          </span>
                        </div>

                        <div className="card">
                          <p className="card-title"><Tag size={14} />Keywords</p>
                          <div className="tag-list">
                            {flattenKeywords(result.keywords).slice(0, 24).map((tag, j) => (
                              <span key={j} className="tag">{tag}</span>
                            ))}
                          </div>
                          {Object.keys(result.keywords).length > 0 && (
                            <details className="mt-4">
                              <summary className="text-xs text-muted" style={{ cursor: "pointer" }}>View full keyword JSON</summary>
                              <pre className="code-block mt-2">{JSON.stringify(result.keywords, null, 2)}</pre>
                            </details>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
