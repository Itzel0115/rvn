"use client";

import clsx from "clsx";

export function KpiCard({ label, value, helper, variant = "desktop", tone = "neutral" }) {
  if (variant === "mobile") {
    return (
      <div className={clsx("mobile-exec-metric-tile", tone)}>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{helper}</small>
      </div>
    );
  }

  return (
    <article className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-helper">{helper}</div>
    </article>
  );
}
