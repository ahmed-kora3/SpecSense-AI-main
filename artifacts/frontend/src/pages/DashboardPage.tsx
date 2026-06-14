import { useState } from "react";
import { Link } from "wouter";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Eye,
  FileText,
  Cpu,
  Zap,
  Activity,
  CheckCircle,
  Server,
  TrendingUp,
  ArrowRight,
  Info
} from "lucide-react";

async function apiCalculateFeeder(body: object) {
  const res = await fetch("/api/assistant/calculate-feeder", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function fetchStats() {
  const res = await fetch("/api/stats");
  if (!res.ok) throw new Error("Failed to fetch dashboard stats");
  return res.json();
}

export default function DashboardPage() {
  const [form, setForm] = useState({
    total_power_w: 12000,
    system_type: "three",
    voltage: 380,
    distance_m: 45,
  });

  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: fetchStats,
    refetchInterval: 3000,
  });

  const mutation = useMutation({ mutationFn: apiCalculateFeeder });
  const res = mutation.data;

  return (
    <>
      <div className="page-header">
        <div className="page-header-icon" style={{ background: "rgba(59,130,246,0.12)", borderColor: "rgba(59,130,246,0.3)", color: "var(--accent-light)" }}>
          <LayoutDashboard size={18} />
        </div>
        <div className="page-header-text">
          <h1>Project Dashboard</h1>
          <p>Real-time engineering metrics, system diagnostics, and quick design tools</p>
        </div>
      </div>

      <div className="page-body flex flex-col gap-6">
        {/* Welcome Glass Banner */}
        <div 
          style={{ 
            background: "linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.08))",
            border: "1px solid var(--border-bright)",
            borderRadius: "var(--radius-lg)",
            padding: "28px",
            boxShadow: "var(--shadow-glow)"
          }}
        >
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "8px", color: "var(--text-primary)" }}>
            Welcome to SpecSense AI Hub
          </h2>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", maxWidth: "800px", lineHeight: 1.6 }}>
            Automate cable specification parsing, layout engineering drawings using computer vision, and compute 
            feeder ratings and circuit distributions instantly. Switch between core modules on the sidebar to get started.
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="metrics-grid">
          <div className="metric-card">
            <p className="metric-label">Cable Inspections</p>
            <div className="flex items-baseline gap-2">
              <p className="metric-value">{stats?.total_inspections ?? 0}</p>
            </div>
            <p className="metric-sub">Cable images analyzed (Vision)</p>
          </div>
          <div className="metric-card">
            <p className="metric-label">Datasheet Analyses</p>
            <div className="flex items-baseline gap-2">
              <p className="metric-value">{stats?.total_analyses ?? 0}</p>
            </div>
            <p className="metric-sub">Documents parsed (OCR)</p>
          </div>
          <div className="metric-card">
            <p className="metric-label">Engineering Projects</p>
            <div className="flex items-baseline gap-2">
              <p className="metric-value">{stats?.total_projects ?? 0}</p>
            </div>
            <p className="metric-sub">Wiring calculations saved</p>
          </div>
          <div className="metric-card">
            <p className="metric-label">Database Health</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="status-dot" style={{ display: "inline-block", position: "relative" }} />
              <span className="font-bold text-success text-sm" style={{ fontFamily: "inherit" }}>Connected</span>
            </div>
            <p className="metric-sub">PostgreSQL operational</p>
          </div>
        </div>

        {/* Two Columns Section */}
        <div className="result-grid" style={{ gridTemplateColumns: "1.7fr 1.3fr" }}>
          {/* Left: Quick Access Modules */}
          <div className="flex flex-col gap-4">
            <p className="card-title" style={{ margin: 0 }}><Activity size={14} />Available Engineering Modules</p>
            
            <div className="flex flex-col gap-3">
              {[
                {
                  title: "Vision Inspection",
                  desc: "Analyze cross-section scans of multi-core cable segments to calculate layer dimensions, core diameters, and validate structures against international designs.",
                  icon: Eye,
                  color: "#3b82f6",
                  href: "/vision"
                },
                {
                  title: "Datasheet / OCR",
                  desc: "Upload technical cable datasheets in PDF or image format to scan, validate key metrics, log spelling corrections, and auto-generate SEO keywords.",
                  icon: FileText,
                  color: "#8b5cf6",
                  href: "/ocr"
                },
                {
                  title: "Technical Assistant",
                  desc: "Size feeder cables according to target capacity/distance or design optimal wiring configurations with full circuit-breaker distributions.",
                  icon: Cpu,
                  color: "#22c55e",
                  href: "/assistant"
                }
              ].map((m) => {
                const Icon = m.icon;
                return (
                  <div key={m.title} className="card flex gap-4 items-start" style={{ transition: "transform 0.2s, border-color 0.2s" }}>
                    <div 
                      style={{ 
                        background: `rgba(${m.color === "#3b82f6" ? "59,130,246" : m.color === "#8b5cf6" ? "139,92,246" : "34,197,150"}, 0.12)`, 
                        border: `1px solid rgba(${m.color === "#3b82f6" ? "59,130,246" : m.color === "#8b5cf6" ? "139,92,246" : "34,197,150"}, 0.3)`, 
                        color: m.color,
                        padding: "10px",
                        borderRadius: "var(--radius-md)"
                      }}
                    >
                      <Icon size={20} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>{m.title}</h3>
                      <p className="text-xs text-secondary mt-1" style={{ lineHeight: 1.5 }}>{m.desc}</p>
                      <Link href={m.href}>
                        <a className="text-xs font-bold text-accent flex items-center gap-1 mt-3 hover:underline">
                          Open Module <ArrowRight size={12} />
                        </a>
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Live Interactive Quick Calculator & Hardware Status */}
          <div className="flex flex-col gap-4">
            <p className="card-title" style={{ margin: 0 }}><Zap size={14} />Interactive Utilities</p>

            {/* Quick Sizer Card */}
            <div className="card">
              <p className="card-title" style={{ fontSize: "0.8rem", marginBottom: "8px" }}><Zap size={12} />Quick Cable Sizer</p>
              <p className="text-xs text-secondary mb-4" style={{ lineHeight: 1.4 }}>
                Compute recommended feeder cable cross-section size and estimate percentage voltage drops.
              </p>
              
              <div className="flex flex-col gap-3">
                <div className="form-group">
                  <label className="form-label" style={{ fontSize: "0.75rem" }}>Total Load (Watts)</label>
                  <input
                    className="form-control"
                    type="number"
                    style={{ padding: "8px 12px" }}
                    value={form.total_power_w}
                    onChange={(e) => setForm(p => ({ ...p, total_power_w: +e.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ fontSize: "0.75rem" }}>Distance (meters)</label>
                  <input
                    className="form-control"
                    type="number"
                    style={{ padding: "8px 12px" }}
                    value={form.distance_m}
                    onChange={(e) => setForm(p => ({ ...p, distance_m: +e.target.value }))}
                  />
                </div>
                <div className="flex gap-2">
                  <div className="form-group" style={{ flex: 1 }}>
                    <label className="form-label" style={{ fontSize: "0.75rem" }}>Phase</label>
                    <select
                      className="form-control"
                      style={{ padding: "8px 12px" }}
                      value={form.system_type}
                      onChange={(e) => setForm(p => ({
                        ...p,
                        system_type: e.target.value,
                        voltage: e.target.value === "three" ? 380 : 220
                      }))}
                    >
                      <option value="single">Single (220V)</option>
                      <option value="three">Three (380V)</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ flex: 1 }}>
                    <label className="form-label" style={{ fontSize: "0.75rem" }}>Voltage (V)</label>
                    <input
                      className="form-control"
                      type="number"
                      style={{ padding: "8px 12px" }}
                      value={form.voltage}
                      onChange={(e) => setForm(p => ({ ...p, voltage: +e.target.value }))}
                    />
                  </div>
                </div>
                
                <button
                  className="btn btn-primary mt-2"
                  style={{ padding: "10px 14px" }}
                  onClick={() => mutation.mutate(form)}
                  disabled={mutation.isPending}
                >
                  {mutation.isPending ? "Calculating..." : "Calculate Feeder"}
                </button>
              </div>

              {mutation.isError && (
                <div className="alert alert-danger mt-3" style={{ padding: "8px 12px", fontSize: "0.75rem" }}>
                  <span>{(mutation.error as Error).message}</span>
                </div>
              )}

              {res && (
                <div className="mt-4 p-3" style={{ background: "var(--bg-surface)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                  <p className="text-xs font-bold text-accent-light mb-2">Calculation Result:</p>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-muted">Recommended Cable:</span>
                      <strong className="font-mono text-success">{res.recommended_cable_mm2} mm²</strong>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-muted">Calculated Current:</span>
                      <strong className="font-mono">{res.current_a?.toFixed(1)} A</strong>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-muted">Voltage Drop %:</span>
                      <strong className={`font-mono ${res.voltage_drop_status?.includes("WARNING") ? "text-danger" : "text-success"}`}>
                        {res.voltage_drop_pct?.toFixed(1)}%
                      </strong>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Hardware / Engine status */}
            <div className="card">
              <p className="card-title" style={{ fontSize: "0.8rem", marginBottom: "8px" }}><Server size={12} />System Environment</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div className="flex justify-between text-xs">
                  <span className="text-muted">ML Model Engine:</span>
                  <span className="font-mono text-success">CUDA (PyTorch 2.5)</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted">OCR Decoder:</span>
                  <span className="font-mono text-accent">EasyOCR (CPU Enabled)</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted">NLP Parser:</span>
                  <span className="font-mono">SpaCy Pipelines</span>
                </div>
              </div>
            </div>

            {/* AI Engineering Tips */}
            <div className="alert alert-info flex gap-2" style={{ padding: "12px", border: "1px solid rgba(6,182,212,0.15)" }}>
              <Info size={14} className="text-info" style={{ flexShrink: 0, marginTop: "2px" }} />
              <p style={{ fontSize: "0.75rem", lineHeight: 1.4, margin: 0 }}>
                <strong>Engineering Tip:</strong> Maintain cable voltage drops under 5.0% for distribution networks, and 3.0% for critical branches to avoid efficiency losses.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
