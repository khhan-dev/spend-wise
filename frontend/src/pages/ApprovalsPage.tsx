import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { endpoints } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import { STATUS_LABEL, STATUS_STYLE, won } from "../lib/format";
import type { ExpenseReport } from "../lib/types";

export function ApprovalsPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const { data: reports = [] } = useQuery<ExpenseReport[]>({
    queryKey: ["reports"],
    queryFn: endpoints.reports,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["reports"] });
  };

  const approve = useMutation({ mutationFn: (id: string) => endpoints.approve(id), onSuccess: invalidate });
  const review = useMutation({ mutationFn: (id: string) => endpoints.review(id), onSuccess: invalidate });
  const reject = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) => endpoints.reject(id, comment),
    onSuccess: invalidate,
  });

  // 팀장: 제출(submitted) 승인 대상 / 관리자: 팀장승인(team_approved) 검토 대상
  const pending = reports.filter((r) =>
    user?.role === "admin"
      ? r.status === "submitted" || r.status === "team_approved"
      : r.status === "submitted"
  );

  function onReject(id: string) {
    const comment = window.prompt("반려 사유를 입력하세요.");
    if (comment) reject.mutate({ id, comment });
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">승인함</h1>
        <p className="text-sm text-gray-500">
          {user?.role === "admin" ? "제출·팀장승인 건을 검토하세요." : "소속 팀의 제출 건을 승인하세요."}
        </p>
      </div>

      {pending.length === 0 ? (
        <div className="card py-10 text-center text-sm text-gray-400">처리할 승인 건이 없습니다.</div>
      ) : (
        <div className="space-y-3">
          {pending.map((r) => {
            const total = r.items.reduce((s, i) => s + i.total_amount, 0);
            const isSubmitted = r.status === "submitted";
            return (
              <div key={r.id} className="card flex flex-wrap items-center justify-between gap-3">
                <div>
                  <Link to={`/expenses/${r.id}`} className="font-medium text-ledger-dark hover:underline">
                    {r.title}
                  </Link>
                  <p className="font-mono text-xs text-gray-400">
                    {r.period} · {r.items.length}건 · {won(total)}원
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`chip ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>
                  {isSubmitted && (user?.role === "manager" || user?.role === "admin") && (
                    <button className="btn-primary" onClick={() => approve.mutate(r.id)}>
                      승인
                    </button>
                  )}
                  {r.status === "team_approved" && user?.role === "admin" && (
                    <button className="btn-primary" onClick={() => review.mutate(r.id)}>
                      검토완료
                    </button>
                  )}
                  <button className="btn-danger" onClick={() => onReject(r.id)}>
                    반려
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
