import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ExpensesPage } from "./pages/ExpensesPage";
import { NewReportPage } from "./pages/NewReportPage";
import { EditReportPage } from "./pages/EditReportPage";
import { ReportDetailPage } from "./pages/ReportDetailPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { ClosingsPage } from "./pages/ClosingsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/expenses" element={<ExpensesPage />} />
        <Route path="/expenses/new" element={<NewReportPage />} />
        <Route path="/expenses/:id/edit" element={<EditReportPage />} />
        <Route path="/expenses/:id" element={<ReportDetailPage />} />
        <Route
          path="/approvals"
          element={
            <ProtectedRoute roles={["manager", "admin"]}>
              <ApprovalsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/closings"
          element={
            <ProtectedRoute roles={["admin"]}>
              <ClosingsPage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
