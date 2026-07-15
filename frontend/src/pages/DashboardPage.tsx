import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { endpoints } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import { STATUS_LABEL, STATUS_STYLE, won } from "../lib/format";
import { AreaChart, BarList, SplitBar } from "../components/Charts";
import type { DashboardStats, ExpenseReport, ReportStatus } from "../lib/types";

const STATUS_ORDER: ReportStatus[] = ["draft", "submitted", "team_approved", "reviewed", "closed", "rejected"];

const THIS_MONTH = new Date().toISOString().slice(0, 7);
function shiftMonth(base: string, delta: number): string {
  const [y, m] = base.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function DashboardPage() {
  const { user } = useAuth();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ["dashboard", from, to],
    queryFn: () => endpoints.dashboard({ period_from: from || undefined, period_to: to || undefined }),
  });
  const { data: reports = [] } = useQuery<ExpenseReport[]>({ queryKey: ["reports"], queryFn: endpoints.reports });

  const s = stats;
  const inProgress = (s?.status_counts["submitted"] ?? 0) + (s?.status_counts["team_approved"] ?? 0);

  const kpis = [
    { label: "합계 금액", value: won(s?.total_amount ?? 0), suffix: "원" },
    { label: "경비 항목", value: s?.item_count ?? 0, suffix: "건" },
    { label: "진행중", value: inProgress, suffix: "건" },
    { label: "검증 경고", value: s?.warning_count ?? 0, suffix: "건", warn: (s?.warning_count ?? 0) > 0 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">안녕하세요, {user?.name}님</h1>
        <p className="text-sm text-gray-500">경비 처리 현황을 한눈에 확인하세요.</p>
      </div>

      {/* 기간 필터 */}
      <div className="card flex flex-wrap items-end gap-3">
        <div>
          <label className="label">시작 월</label>
          <input className="input" type="month" value={from} max={to || undefined} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div>
          <label className="label">종료 월</label>
          <input className="input" type="month" value={to} min={from || undefined} onChange={(e) => setTo(e.target.value)} />
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => { setFrom(shiftMonth(THIS_MONTH, -5)); setTo(THIS_MONTH); }}>
            최근 6개월
          </button>
          <button className="btn-ghost" onClick={() => { setFrom(`${THIS_MONTH.slice(0, 4)}-01`); setTo(THIS_MONTH); }}>
            올해
          </button>
          <button className="btn-ghost" onClick={() => { setFrom(""); setTo(""); }}>
            전체
          </button>
        </div>
        <span className="ml-auto text-xs text-gray-400">
          {from || to ? `기간: ${from || "처음"} ~ ${to || "현재"}` : "전체 기간"}
        </span>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className={`card ${k.warn ? "border-amber-300 bg-amber-50" : ""}`}>
            <p className={`text-xs font-semibold ${k.warn ? "text-amber-700" : "text-gray-500"}`}>{k.label}</p>
            <p className={`mt-1 font-mono text-2xl font-bold tabular-nums ${k.warn ? "text-amber-800" : ""}`}>
              {k.value}
              <span className="ml-1 text-sm font-normal text-gray-400">{k.suffix}</span>
            </p>
          </div>
        ))}
      </div>

      {/* 월별 추이 */}
      <div className="card">
        <h2 className="mb-3 font-semibold">월별 경비 추이</h2>
        <AreaChart points={s?.by_month ?? []} />
      </div>

      {/* 계정 / 부서 집계 */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 font-semibold">계정과목별 집계</h2>
          <BarList data={s?.by_account ?? []} />
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">부서별 집계</h2>
          <BarList data={s?.by_dept ?? []} />
        </div>
      </div>

      {/* 공제 / 상태 */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-4 font-semibold">부가세 공제 / 불공제</h2>
          <SplitBar deductible={s?.deductible_amount ?? 0} nonDeductible={s?.non_deductible_amount ?? 0} />
        </div>
        <div className="card">
          <h2 className="mb-4 font-semibold">상태 분포</h2>
          <div className="flex flex-wrap gap-2">
            {STATUS_ORDER.filter((st) => (s?.status_counts[st] ?? 0) > 0).map((st) => (
              <span key={st} className={`chip ${STATUS_STYLE[st]}`}>
                {STATUS_LABEL[st]} {s?.status_counts[st]}
              </span>
            ))}
            {Object.keys(s?.status_counts ?? {}).length === 0 && (
              <p className="text-sm text-gray-400">신청 내역이 없습니다.</p>
            )}
          </div>
        </div>
      </div>

      {/* 최근 신청 */}
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
                      {won(r.items.reduce((sum, i) => sum + i.total_amount, 0))}원
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
