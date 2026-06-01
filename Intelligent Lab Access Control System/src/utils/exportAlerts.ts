// ================================================================
//  utils/exportAlerts.ts — Export security alerts as CSV or PDF
//  No external libraries — pure browser APIs
// ================================================================
import type { AlertEntry } from "../types";

// ── CSV Export ────────────────────────────────────────────────────
export function exportAlertsCSV(alerts: AlertEntry[]): void {
  const headers = [
    "ID",
    "Severity",
    "Alert Type",
    "Lab ID",
    "Description",
    "Status",
    "Created At",
  ];

  const rows = alerts.map((a) => [
    a.id,
    a.severity,
    a.alert_type,
    `LAB-${a.lab_id}`,
    // Wrap description in quotes — may contain commas
    `"${a.description.replace(/"/g, '""')}"`,
    a.is_resolved ? "Resolved" : "Active",
    new Date(a.created_at).toLocaleString(),
  ]);

  const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join(
    "\n",
  );

  // Trigger download
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `security_alerts_${formatDate()}.csv`;
  link.click();

  URL.revokeObjectURL(url);
}

// ── PDF Export ────────────────────────────────────────────────────
export function exportAlertsPDF(alerts: AlertEntry[]): void {
  const activeCount = alerts.filter((a) => !a.is_resolved).length;
  const resolvedCount = alerts.filter((a) => a.is_resolved).length;
  const criticalCount = alerts.filter((a) => a.severity === "CRITICAL").length;

  const severityColor: Record<string, string> = {
    LOW: "#2563eb",
    MEDIUM: "#d97706",
    HIGH: "#dc2626",
    CRITICAL: "#7c3aed",
  };

  const typeLabel: Record<string, string> = {
    CONSECUTIVE_DENY: "Consecutive Denials",
    HIGH_VOLUME: "High Volume Attack",
    SUSPICIOUS_MOVEMENT: "Suspicious Movement",
  };

  const rows = alerts
    .map(
      (a) => `
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:10px 12px;">
        <span style="
          padding:3px 10px;border-radius:4px;
          font-size:11px;font-weight:700;
          text-transform:uppercase;letter-spacing:.05em;
          background:${severityColor[a.severity]}18;
          color:${severityColor[a.severity]};
          border:1px solid ${severityColor[a.severity]}40;
        ">${a.severity}</span>
      </td>
      <td style="padding:10px 12px;font-size:12px;color:#374151;font-family:monospace;">
        ${new Date(a.created_at).toLocaleString()}
      </td>
      <td style="padding:10px 12px;font-size:12px;font-weight:600;color:#111827;">
        ${typeLabel[a.alert_type] ?? a.alert_type}
      </td>
      <td style="padding:10px 12px;font-size:12px;color:#374151;font-family:monospace;">
        LAB-${a.lab_id}
      </td>
      <td style="padding:10px 12px;font-size:11px;color:#4b5563;max-width:280px;">
        ${a.description}
      </td>
      <td style="padding:10px 12px;">
        <span style="
          font-size:11px;font-weight:700;
          text-transform:uppercase;letter-spacing:.05em;
          ${a.is_resolved ? "color:#059669;" : "color:#dc2626;"}
        ">
          ${a.is_resolved ? "✓ Resolved" : "● Active"}
        </span>
      </td>
    </tr>
  `,
    )
    .join("");

  const html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8"/>
      <title>Security Alerts Report — ${formatDate()}</title>
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          color: #111827;
          background: #fff;
          padding: 40px;
        }
        @media print {
          body { padding: 20px; }
          .no-print { display: none; }
        }
      </style>
    </head>
    <body>

      <!-- Print button -->
      <div class="no-print" style="margin-bottom:24px;">
        <button
          onclick="window.print()"
          style="
            padding:10px 24px;border-radius:8px;
            background:#1d4ed8;color:#fff;
            border:none;font-size:14px;font-weight:600;
            cursor:pointer;
          "
        >
          🖨️ Print / Save as PDF
        </button>
        <button
          onclick="window.close()"
          style="
            padding:10px 24px;border-radius:8px;
            background:#f3f4f6;color:#374151;
            border:1px solid #d1d5db;
            font-size:14px;font-weight:600;
            cursor:pointer;margin-left:8px;
          "
        >
          Close
        </button>
      </div>

      <!-- Report header -->
      <div style="
        border-bottom:3px solid #1d4ed8;
        padding-bottom:20px;margin-bottom:28px;
      ">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <h1 style="font-size:26px;font-weight:800;color:#111827;margin-bottom:4px;">
              Security Alerts Report
            </h1>
            <p style="font-size:13px;color:#6b7280;">
              Intelligent Laboratory Access Control System — v2.0
            </p>
          </div>
          <div style="text-align:right;">
            <p style="font-size:12px;color:#6b7280;">Generated</p>
            <p style="font-size:14px;font-weight:700;color:#111827;">
              ${new Date().toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      <!-- Summary cards -->
      <div style="
        display:grid;grid-template-columns:repeat(4,1fr);
        gap:16px;margin-bottom:32px;
      ">
        ${[
          { label: "Total Alerts", value: alerts.length, color: "#1d4ed8" },
          { label: "Active", value: activeCount, color: "#dc2626" },
          { label: "Critical", value: criticalCount, color: "#7c3aed" },
          { label: "Resolved", value: resolvedCount, color: "#059669" },
        ]
          .map(
            (c) => `
          <div style="
            border:1px solid #e5e7eb;border-radius:10px;
            padding:16px;text-align:center;
            border-top:4px solid ${c.color};
          ">
            <p style="font-size:28px;font-weight:800;color:${c.color};">
              ${c.value}
            </p>
            <p style="font-size:12px;color:#6b7280;font-weight:600;
               text-transform:uppercase;letter-spacing:.05em;margin-top:4px;">
              ${c.label}
            </p>
          </div>
        `,
          )
          .join("")}
      </div>

      <!-- Table -->
      <table style="
        width:100%;border-collapse:collapse;
        border:1px solid #e5e7eb;border-radius:10px;
        overflow:hidden;font-size:13px;
      ">
        <thead>
          <tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb;">
            <th style="padding:12px;text-align:left;font-size:11px;color:#6b7280;
               text-transform:uppercase;letter-spacing:.06em;font-weight:700;">Severity</th>
            <th style="padding:12px;text-align:left;font-size:11px;color:#6b7280;
               text-transform:uppercase;letter-spacing:.06em;font-weight:700;">Timestamp</th>
            <th style="padding:12px;text-align:left;font-size:11px;color:#6b7280;
               text-transform:uppercase;letter-spacing:.06em;font-weight:700;">Alert Type</th>
            <th style="padding:12px;text-align:left;font-size:11px;color:#6b7280;
               text-transform:uppercase;letter-spacing:.06em;font-weight:700;">Lab</th>
            <th style="padding:12px;text-align:left;font-size:11px;color:#6b7280;
               text-transform:uppercase;letter-spacing:.06em;font-weight:700;">Description</th>
            <th style="padding:12px;text-align:left;font-size:11px;color:#6b7280;
               text-transform:uppercase;letter-spacing:.06em;font-weight:700;">Status</th>
          </tr>
        </thead>
        <tbody>
          ${
            rows ||
            `
            <tr>
              <td colspan="6" style="padding:40px;text-align:center;color:#9ca3af;">
                No alerts to display
              </td>
            </tr>
          `
          }
        </tbody>
      </table>

      <!-- Footer -->
      <div style="
        margin-top:32px;padding-top:16px;
        border-top:1px solid #e5e7eb;
        display:flex;justify-content:space-between;
        font-size:11px;color:#9ca3af;
      ">
        <span>Lab Access Control System — Security Report</span>
        <span>Generated: ${new Date().toLocaleString()}</span>
      </div>

    </body>
    </html>
  `;

  // Open in new window for printing
  const printWindow = window.open("", "_blank", "width=1100,height=800");
  if (!printWindow) {
    alert("Please allow popups to export PDF.");
    return;
  }
  printWindow.document.write(html);
  printWindow.document.close();
}

// ── Helper ────────────────────────────────────────────────────────
function formatDate(): string {
  return new Date().toISOString().slice(0, 10);
}
