import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import CliCommandsPage from "./CliCommandsPage";
import DefenseContextPage from "./DefenseContextPage";
import DevTestsPage from "./DevTestsPage";
import LandingPage from "./LandingPage";
import MitreDeepPage from "./MitreDeepPage";
import MitreHeatmapPage from "./MitreHeatmapPage";
import OtDashboardPage from "./OtDashboardPage";
import ScanPage from "./ScanPage";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<ScanPage />} />
        <Route path="/defense-context" element={<DefenseContextPage />} />
        <Route path="/mitre-deep" element={<MitreDeepPage />} />
        <Route path="/mitre-heatmap" element={<MitreHeatmapPage />} />
        <Route path="/ot-dashboard" element={<OtDashboardPage />} />
        <Route path="/dev-tests" element={<DevTestsPage />} />
        <Route path="/cli-commands" element={<CliCommandsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
