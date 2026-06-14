import { useLocation, Link } from "wouter";
import {
  Eye,
  FileText,
  Cpu,
  Zap,
  Activity,
  LayoutDashboard
} from "lucide-react";

const NAV = [
  {
    section: "Overview",
    items: [
      { label: "Dashboard",               icon: LayoutDashboard, href: "/dashboard" },
    ],
  },
  {
    section: "Modules",
    items: [
      { label: "Vision Inspection",       icon: Eye,      href: "/vision"    },
      { label: "Datasheet / OCR",         icon: FileText, href: "/ocr"       },
      { label: "Technical Assistant",     icon: Cpu,      href: "/assistant" },
    ],
  },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  const activeHref =
    location === "/" ? "/dashboard" : location;

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img src="/logo.png" alt="SpecSense AI logo" />
          <div className="sidebar-logo-text">
            <span>SpecSense AI</span>
            <span>v1.0 · Graduation Project</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV.map((group) => (
            <div key={group.section}>
              <p className="nav-section-label">{group.section}</p>
              {group.items.map(({ label, icon: Icon, href }) => (
                <Link key={href} href={href}>
                  <a className={`nav-item ${activeHref === href ? "active" : ""}`}>
                    <Icon className="nav-item-icon" />
                    {label}
                  </a>
                </Link>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-badge">
            <span className="status-dot" />
            <span>All systems operational</span>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
