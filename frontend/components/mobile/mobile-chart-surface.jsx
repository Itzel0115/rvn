"use client";

import { SharedChartSurface } from "@/components/charts/chart-surface";

// Phase 5D-1: mobile chart imports now flow through the shared chart implementation.
export function MobileChartSurface(props) {
  return <SharedChartSurface {...props} variant="mobile" />;
}
