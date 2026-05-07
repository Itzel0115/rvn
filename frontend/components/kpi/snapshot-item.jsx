"use client";

export function SnapshotItem({ label, value, helper, variant = "desktop" }) {
  if (variant === "mobile") {
    return (
      <div className="mobile-exec-snapshot-item">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{helper}</small>
      </div>
    );
  }

  return (
    <div className="snapshot-item">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{helper}</small>
    </div>
  );
}
