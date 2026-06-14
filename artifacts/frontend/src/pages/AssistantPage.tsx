import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Cpu, Zap, AlertTriangle, CheckCircle, XCircle, Home } from "lucide-react";

/* ── API helpers ── */
async function apiCalculateFeeder(body: object) {
  const res = await fetch("/api/assistant/calculate-feeder", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiDesignWiring(body: object) {
  const res = await fetch("/api/assistant/design-wiring", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

/* ── Feeder Tab ── */
function FeederTab() {
  const [form, setForm] = useState({
    total_power_w: 5000,
    system_type: "single",
    voltage: 220,
    distance_m: 20,
  });

  const mutation = useMutation({ mutationFn: apiCalculateFeeder });
  const res = mutation.data;

  const set = (k: string, v: number | string) =>
    setForm((p) => ({ ...p, [k]: v }));

  const isThree = form.system_type === "three";

  return (
    <div className="flex flex-col gap-6">
      {/* Inputs */}
      <div className="card">
        <p className="card-title"><Zap size={14} />Input Requirements</p>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Total Power (Watts)</label>
            <input
              className="form-control"
              type="number"
              min={0}
              step={100}
              value={form.total_power_w}
              onChange={(e) => set("total_power_w", +e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">System Type</label>
            <select
              className="form-control"
              value={form.system_type}
              onChange={(e) => {
                set("system_type", e.target.value);
                set("voltage", e.target.value === "three" ? 380 : 220);
              }}
            >
              <option value="single">Single Phase (220 V)</option>
              <option value="three">Three Phase (380 V)</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Supply Voltage (V)</label>
            <input
              className="form-control"
              type="number"
              min={1}
              value={form.voltage}
              onChange={(e) => set("voltage", +e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Cable Distance (m)</label>
            <input
              className="form-control"
              type="number"
              min={1}
              step={1}
              value={form.distance_m}
              onChange={(e) => set("distance_m", +e.target.value)}
            />
          </div>
        </div>

        <button
          className="btn btn-primary btn-lg w-full mt-4"
          onClick={() => mutation.mutate(form)}
          disabled={mutation.isPending}
        >
          {mutation.isPending
            ? <><span className="spinner" style={{ width: 18, height: 18 }} /> Calculating…</>
            : <><Zap size={18} /> Calculate & Get AI Insight</>}
        </button>
      </div>

      {mutation.isError && (
        <div className="alert alert-danger">
          <AlertTriangle size={16} />
          <span>{(mutation.error as Error).message}</span>
        </div>
      )}

      {res && (
        <div className="result-section">
          {/* Metrics */}
          <div className="metrics-grid">
            <div className="metric-card">
              <p className="metric-label">Total Load</p>
              <p className="metric-value">{res.total_power_w}</p>
              <p className="metric-sub">Watts</p>
            </div>
            <div className="metric-card">
              <p className="metric-label">Current</p>
              <p className="metric-value">{res.current_a?.toFixed(2)}</p>
              <p className="metric-sub">Amperes</p>
            </div>
            <div className="metric-card">
              <p className="metric-label">Safe Current</p>
              <p className="metric-value">{res.safe_current_a?.toFixed(2)}</p>
              <p className="metric-sub">A (×1.25 margin)</p>
            </div>
            <div className="metric-card">
              <p className="metric-label">Recommended Cable</p>
              <p className="metric-value">{res.recommended_cable_mm2 ?? "—"}</p>
              <p className="metric-sub">mm²</p>
              {res.initial_cable_mm2 && res.initial_cable_mm2 !== res.recommended_cable_mm2 && (
                <span className="metric-badge badge-warning">Upsized from {res.initial_cable_mm2} mm²</span>
              )}
            </div>
          </div>

          {/* Voltage drop */}
          <div className={`alert ${res.voltage_drop_status?.includes("WARNING") ? "alert-danger" : "alert-success"}`}>
            {res.voltage_drop_status?.includes("WARNING") ? <XCircle size={16} /> : <CheckCircle size={16} />}
            <span>
              Voltage Drop: <strong>{res.voltage_drop_v?.toFixed(2)} V ({res.voltage_drop_pct?.toFixed(2)}%)</strong>
              &nbsp;— {res.voltage_drop_status}
            </span>
          </div>

          {res.validation_warnings?.map((w: string, i: number) => (
            <div key={i} className="alert alert-warning"><AlertTriangle size={16} /><span>{w}</span></div>
          ))}

          {/* AI explanation */}
          {res.ai_explanation && (
            <div className="card">
              <p className="card-title">🤖 AI Engineering Insight</p>
              <p className="text-sm" style={{ lineHeight: 1.8, color: "var(--text-secondary)" }}>{res.ai_explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Wiring Tab ── */
function WiringTab() {
  const [form, setForm] = useState({
    num_rooms: 3, num_acs: 2, num_lights: 10, num_sockets: 12,
    has_kitchen: true,
    light_w: 20, socket_w: 300, ac_w: 1500, kitchen_w: 3000,
    lighting_df: 0.8, socket_df: 0.6,
  });

  const [inputMode, setInputMode] = useState<"manual" | "ai">("manual");
  const [description, setDescription] = useState("");
  const [buildingType, setBuildingType] = useState<string | null>(null);
  const [parseStatus, setParseStatus] = useState<{
    success?: boolean;
    message?: string;
  } | null>(null);

  const mutation = useMutation({ mutationFn: apiDesignWiring });
  const res = mutation.data;

  const parseMutation = useMutation({
    mutationFn: async (desc: string) => {
      const res = await fetch("/api/assistant/parse-project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: desc }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: (data) => {
      setForm((prev) => ({
        ...prev,
        num_rooms: data.rooms !== null && data.rooms !== undefined ? data.rooms : prev.num_rooms,
        num_acs: data.ac_units !== null && data.ac_units !== undefined ? data.ac_units : prev.num_acs,
        num_lights: data.lighting_points !== null && data.lighting_points !== undefined ? data.lighting_points : prev.num_lights,
        num_sockets: data.socket_outlets !== null && data.socket_outlets !== undefined ? data.socket_outlets : prev.num_sockets,
        has_kitchen: data.kitchen !== null && data.kitchen !== undefined ? !!data.kitchen : prev.has_kitchen,
      }));
      setBuildingType(data.building_type);
      setParseStatus({
        success: true,
        message: `Successfully extracted parameters: ${data.rooms ?? 0} Rooms, ${data.ac_units ?? 0} ACs, ${data.lighting_points ?? 0} Lights, ${data.socket_outlets ?? 0} Sockets.`,
      });
    },
    onError: (err: any) => {
      setParseStatus({
        success: false,
        message: err.message || "Failed to extract parameters.",
      });
    }
  });

  const set = (k: string, v: number | boolean) => setForm((p) => ({ ...p, [k]: v }));

  return (
    <div className="flex flex-col gap-6">
      <div className="card">
        <p className="card-title"><Home size={14} />Internal Wiring Input Parameters</p>

        {/* Input Mode Selector */}
        <div className="form-group mb-4">
          <label className="form-label" style={{ fontWeight: 600 }}>Select Input Mode:</label>
          <div className="flex gap-4 items-center mt-1">
            <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-secondary)" }}>
              <input
                type="radio"
                name="inputMode"
                value="manual"
                checked={inputMode === "manual"}
                onChange={() => {
                  setInputMode("manual");
                  setParseStatus(null);
                  setBuildingType(null);
                }}
                style={{ width: 16, height: 16, accentColor: "var(--warning)" }}
              />
              Manual Entry
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-secondary)" }}>
              <input
                type="radio"
                name="inputMode"
                value="ai"
                checked={inputMode === "ai"}
                onChange={() => {
                  setInputMode("ai");
                  setParseStatus(null);
                  setBuildingType(null);
                }}
                style={{ width: 16, height: 16, accentColor: "var(--warning)" }}
              />
              AI Project Description
            </label>
          </div>
        </div>

        <div className="divider" style={{ margin: "16px 0" }} />

        {inputMode === "ai" && (
          <>
            <p className="card-title" style={{ fontSize: "0.8rem", marginBottom: 12 }}>AI Project Description</p>
            <div className="form-group">
              <label className="form-label">Describe your project (English or Arabic):</label>
              <textarea
                className="form-control"
                rows={4}
                placeholder="E.g., I want to design wiring for an apartment with 3 rooms, 2 AC units, 10 lighting points, and a kitchen..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>
            
            <button
              className="btn btn-ghost w-full mt-3"
              onClick={() => parseMutation.mutate(description)}
              disabled={parseMutation.isPending || !description.trim()}
              style={{ display: "flex", gap: "8px", alignItems: "center", justifyContent: "center" }}
            >
              {parseMutation.isPending ? (
                <><span className="spinner" style={{ width: 16, height: 16 }} /> Extracting Parameters…</>
              ) : (
                <>🤖 Extract Parameters with AI</>
              )}
            </button>

            {parseStatus && (
              <div className={`alert ${parseStatus.success ? "alert-success" : "alert-danger"} mt-4`}>
                {parseStatus.success ? <CheckCircle size={16} /> : <XCircle size={16} />}
                <span>{parseStatus.message}</span>
              </div>
            )}

            {buildingType && (
              <div className="alert alert-info mt-3" style={{ background: "rgba(59,130,246,0.12)", borderColor: "rgba(59,130,246,0.3)", color: "#93c5fd" }}>
                <Home size={16} />
                <span>Detected Building Type: <strong>{buildingType.charAt(0).toUpperCase() + buildingType.slice(1)}</strong></span>
              </div>
            )}

            <div className="divider" style={{ margin: "24px 0" }} />
          </>
        )}

        <p className="card-title" style={{ fontSize: "0.8rem", marginBottom: 12 }}>Apartment/Building Details</p>
        <div className="form-grid">
          {[
            { key: "num_rooms",   label: "Number of Rooms" },
            { key: "num_acs",     label: "Number of AC Units" },
            { key: "num_lights",  label: "Number of Lighting Points" },
            { key: "num_sockets", label: "Number of Socket Outlets" },
          ].map(({ key, label }) => (
            <div className="form-group" key={key}>
              <label className="form-label">{label}</label>
              <input
                className="form-control"
                type="number" min={0} step={1}
                value={(form as any)[key]}
                onChange={(e) => set(key, +e.target.value)}
              />
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 mt-4" style={{ padding: "12px", background: "var(--bg-surface)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
          <input
            type="checkbox"
            id="kitchen"
            checked={form.has_kitchen}
            onChange={(e) => set("has_kitchen", e.target.checked)}
            style={{ width: 16, height: 16, accentColor: "var(--accent)" }}
          />
          <label htmlFor="kitchen" className="text-sm" style={{ cursor: "pointer" }}>Include dedicated kitchen circuit</label>
        </div>

        <div className="divider" />
        <p className="card-title" style={{ marginBottom: 12 }}>Load Heuristics</p>
        <div className="form-grid">
          {[
            { key: "light_w",   label: "Lighting Point (W)" },
            { key: "socket_w",  label: "Socket Outlet (W)" },
            { key: "ac_w",      label: "AC Unit (W)" },
            { key: "kitchen_w", label: "Kitchen Load (W)" },
          ].map(({ key, label }) => (
            <div className="form-group" key={key}>
              <label className="form-label">{label}</label>
              <input
                className="form-control"
                type="number" min={1}
                value={(form as any)[key]}
                onChange={(e) => set(key, +e.target.value)}
              />
            </div>
          ))}
        </div>

        <div className="divider" />
        <p className="card-title" style={{ marginBottom: 12 }}>Diversity Factors</p>
        <div className="form-grid">
          {[
            { key: "lighting_df", label: "Lighting" },
            { key: "socket_df",   label: "Sockets" },
          ].map(({ key, label }) => (
            <div className="form-group" key={key}>
              <label className="form-label">{label} — {((form as any)[key] * 100).toFixed(0)}%</label>
              <input
                type="range" min={0.1} max={1.0} step={0.1}
                value={(form as any)[key]}
                onChange={(e) => set(key, +e.target.value)}
              />
            </div>
          ))}
        </div>

        <button
          className="btn btn-primary btn-lg w-full mt-4"
          onClick={() => mutation.mutate(form)}
          disabled={mutation.isPending}
        >
          {mutation.isPending
            ? <><span className="spinner" style={{ width: 18, height: 18 }} /> Designing circuits…</>
            : <><Home size={18} /> Design Internal Circuits</>}
        </button>
      </div>

      {mutation.isError && (
        <div className="alert alert-danger"><AlertTriangle size={16} /><span>{(mutation.error as Error).message}</span></div>
      )}

      {res && (
        <div className="result-section">
          {/* Circuit table */}
          <div className="card">
            <p className="card-title">🔌 Circuit Distribution</p>
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    {["ID", "Type", "Power (W)", "Current (A)", "Cable (mm²)", "MCB (A)", "Length (m)"].map((h) => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {res.circuits?.map((c: any, i: number) => (
                    <tr key={i}>
                      <td>{c.id}</td>
                      <td><span className="metric-badge badge-info">{c.type}</span></td>
                      <td>{c.power_w}</td>
                      <td>{c.current_a?.toFixed(2)}</td>
                      <td>{c.cable_size_mm2}</td>
                      <td>{c.mcb_a}</td>
                      <td>{c.length_m?.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Summary */}
          <div className="result-grid">
            <div className="card">
              <p className="card-title">📦 Load Summary</p>
              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Raw Connected Load</span>
                  <strong className="font-mono">{res.summary?.total_power_w?.toFixed(0)} W</strong>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">Diversified Load</span>
                  <strong className="font-mono">{res.summary?.total_power_diversified_w?.toFixed(0)} W</strong>
                </div>
              </div>
            </div>
            <div className="card">
              <p className="card-title">🔗 Cable Totals</p>
              {Object.entries(res.summary?.cable_totals ?? {}).map(([size, len]) => (
                size !== "-1" && (
                  <div key={size} className="flex justify-between text-sm mt-2">
                    <span className="text-muted">{size} mm²</span>
                    <strong className="font-mono">{(len as number).toFixed(1)} m</strong>
                  </div>
                )
              ))}
            </div>
          </div>

          {res.ai_explanation && (
            <div className="card">
              <p className="card-title">🤖 AI Wiring Insight</p>
              <p className="text-sm" style={{ lineHeight: 1.8, color: "var(--text-secondary)" }}>{res.ai_explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Page ── */
export default function AssistantPage() {
  const [tab, setTab] = useState<"feeder" | "wiring">("feeder");

  return (
    <>
      <div className="page-header">
        <div className="page-header-icon" style={{ background: "rgba(34,197,94,0.12)", borderColor: "rgba(34,197,94,0.3)", color: "#86efac" }}>
          <Cpu size={18} />
        </div>
        <div className="page-header-text">
          <h1>Intelligent Technical Assistant</h1>
          <p>Calculate electrical loads, select cables, and get AI-powered engineering insights</p>
        </div>
      </div>

      <div className="page-body">
        <div className="tabs">
          <button className={`tab-btn ${tab === "feeder" ? "active" : ""}`} onClick={() => setTab("feeder")}>
            ⚡ External Feeder Cable
          </button>
          <button className={`tab-btn ${tab === "wiring" ? "active" : ""}`} onClick={() => setTab("wiring")}>
            🏠 Internal Wiring Design
          </button>
        </div>

        {tab === "feeder" ? <FeederTab /> : <WiringTab />}
      </div>
    </>
  );
}
