import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./LandingPage";
import ScanPage from "./ScanPage";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<ScanPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
