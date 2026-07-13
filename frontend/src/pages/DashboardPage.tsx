import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { endpoints } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import { STATUS_LABEL, STATUS_STYLE, won } from "../lib/format";
import type { ExpenseReport } from "../lib/types";

export function DashboardPage() {
  const { user } = useAuth();
  const { data: reports = [] } = useQuery<ExpenseReport[]>({
    queryKey: ["reports"],
    queryFn: endpoints.reports,
  });

  const total = reports.reduce(
    (sum, r) => sum + r.items.reduce((s, i) => s + i.total_amount, 0),
    0
  );
  const byStatus = (s: string) => reports.filter((r) => r.status === s).length;

  const stats = [
    { label: "전체 신청", value: reports.length, suffix: "건" },
    { label: "합계 금액", value: won(total), suffix: "원" },
    { label: "작성중", value: byStatus("draft") + byStatus("rejected"), suffix: "건" },
    { label: "진행중", value: byStatus("submitted") + byStatus("team_approved"), suffix: "건" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">안녕하세요, {user?.name}님</h1>
        <p className="text-sm text-gray-500">경비 처리 현황을 한눈에 확인하세요.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="card">
            <p className="text-xs font-semibold text-gray-500">{s.label}</p>
            <p className="mt-1 font-mono text-2xl font-bold tabular-nums">
              {s.value}
              <span className="ml-1 text-sm font-normal text-gray-400">{s.suffix}</span>
            </p>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">최근 신청</h2>
          <Link to="/expenses" className="text-sm text-ledger hover:underline">
            전체 보기 →
          </Link>
        </div>
        {reports.length === 0 ? (
          <p className="py-6 text-center text-sm text-gray-400">
            아직 신청 내역이 없습니다.{" "}
            <Link to="/expenses/new" className="text-ledger hover:underline">
              경비 신청하기
            </Link>
          </p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {reports.slice(0, 5).map((r) => (
              <li key={r.id}>
                <Link to={`/expenses/${r.id}`} className="flex items-center justify-between py-3 hover:opacity-70">
                  <div>
                    <p className="text-sm font-medium">{r.title}</p>
                    <p className="font-mono text-xs text-gray-400">
                      {r.period} · {r.items.length}건
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm tabular-nums">
                      {won(r.items.reduce((s, i) => s + i.total_amount, 0))}원
                    </span>
                    <span className={`chip ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
