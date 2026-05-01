import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./LandingPage";
import MitreHeatmapPage from "./MitreHeatmapPage";
import OtDashboardPage from "./OtDashboardPage";
import ScanPage from "./ScanPage";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<ScanPage />} />
        <Route path="/mitre-heatmap" element={<MitreHeatmapPage />} />
        <Route path="/ot-dashboard" element={<OtDashboardPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
