import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABEL } from "../lib/format";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const nav = [
    { to: "/", label: "대시보드", roles: ["employee", "manager", "admin"] },
    { to: "/expenses", label: "경비 내역", roles: ["employee", "manager", "admin"] },
    { to: "/expenses/new", label: "경비 신청", roles: ["employee", "manager", "admin"] },
    { to: "/approvals", label: "승인함", roles: ["manager", "admin"] },
    { to: "/closings", label: "월 마감", roles: ["admin"] },
  ].filter((n) => user && n.roles.includes(user.role));

  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
          <div className="flex items-center gap-2">
            <div className="grid h-7 w-7 place-items-center rounded-md bg-ledger font-mono text-sm font-bold text-white">
              ₩
            </div>
            <span className="text-sm font-bold">경비처리</span>
          </div>
          <nav className="flex flex-1 gap-1">
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    isActive ? "bg-ledger-soft text-ledger-dark" : "text-gray-600 hover:bg-gray-100"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">
              {user?.name}{" "}
              <span className="chip bg-gray-100 text-gray-600">
                {user ? ROLE_LABEL[user.role] : ""}
              </span>
            </span>
            <button
              className="text-sm text-gray-400 hover:text-seal"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
