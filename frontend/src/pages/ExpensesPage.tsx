import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { endpoints } from "../lib/api";
import { STATUS_LABEL, STATUS_STYLE, won } from "../lib/format";
import type { ExpenseReport } from "../lib/types";

export function ExpensesPage() {
  const { data: reports = [], isLoading } = useQuery<ExpenseReport[]>({
    queryKey: ["reports"],
    queryFn: endpoints.reports,
  });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">경비 내역</h1>
        <Link to="/expenses/new" className="btn-primary">
          + 경비 신청
        </Link>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
              <th className="px-4 py-3 font-semibold">제목</th>
              <th className="px-4 py-3 font-semibold">귀속월</th>
              <th className="px-4 py-3 font-semibold">건수</th>
              <th className="px-4 py-3 text-right font-semibold">합계금액</th>
              <th className="px-4 py-3 font-semibold">상태</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  불러오는 중…
                </td>
              </tr>
            ) : reports.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  신청 내역이 없습니다.
                </td>
              </tr>
            ) : (
              reports.map((r) => (
                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link to={`/expenses/${r.id}`} className="font-medium text-ledger-dark hover:underline">
                      {r.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-500">{r.period}</td>
                  <td className="px-4 py-3 font-mono tabular-nums">{r.items.length}</td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums">
                    {won(r.items.reduce((s, i) => s + i.total_amount, 0))}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`chip ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
