import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link, useNavigate } from "react-router-dom";
import { authedBlob, endpoints } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import {
  ACTION_LABEL,
  ACTION_STYLE,
  EVIDENCE_LABEL,
  PAY_LABEL,
  STATUS_LABEL,
  STATUS_STYLE,
  formatDateTime,
  won,
} from "../lib/format";
import type { ApprovalLog, ExpenseReport, ItemValidation } from "../lib/types";

export function ReportDetailPage() {
  const { id = "" } = useParams();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const { user } = useAuth();

  const { data: report } = useQuery<ExpenseReport>({
    queryKey: ["report", id],
    queryFn: () => endpoints.report(id),
  });
  const { data: validations = [] } = useQuery<ItemValidation[]>({
    queryKey: ["validate", id],
    queryFn: () => endpoints.validate(id),
    enabled: !!report,
  });
  const { data: history = [] } = useQuery<ApprovalLog[]>({
    queryKey: ["history", id],
    queryFn: () => endpoints.history(id),
    enabled: !!report,
  });

  const submit = useMutation({
    mutationFn: () => endpoints.submitReport(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report", id] });
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["history", id] });
    },
  });

  const remove = useMutation({
    mutationFn: () => endpoints.deleteReport(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      navigate("/expenses");
    },
  });

  if (!report) return <p className="text-gray-400">불러오는 중…</p>;

  const valById = Object.fromEntries(validations.map((v) => [v.item_id, v]));
  const total = report.items.reduce((s, i) => s + i.total_amount, 0);
  const editable = report.status === "draft" || report.status === "rejected";
  const isOwner = user?.id === report.user_id;
  const canEdit = editable && isOwner;
  const rejectComment = [...history].reverse().find((h) => h.action === "reject")?.comment ?? null;
  const warningCount = validations.filter((v) => v.evidence_warning || !v.amount_ok).length;

  function onDelete() {
    if (window.confirm("이 신청서를 삭제할까요? 되돌릴 수 없습니다.")) remove.mutate();
  }

  async function openReceipt(itemId: string) {
    const blob = await authedBlob(endpoints.receiptImageUrl(itemId));
    if (blob) window.open(URL.createObjectURL(blob), "_blank");
  }

  return (
    <div className="space-y-5">
      <Link to="/expenses" className="text-sm text-gray-400 hover:underline">
        ← 경비 내역
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{report.title}</h1>
          <p className="font-mono text-sm text-gray-500">
            {report.period} · {report.items.length}건 · 합계 {won(total)}원
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`chip ${STATUS_STYLE[report.status]}`}>{STATUS_LABEL[report.status]}</span>
          {canEdit && (
            <>
              <Link to={`/expenses/${id}/edit`} className="btn-ghost">
                수정
              </Link>
              <button className="btn-danger" disabled={remove.isPending} onClick={onDelete}>
                삭제
              </button>
              <button className="btn-primary" disabled={submit.isPending} onClick={() => submit.mutate()}>
                {submit.isPending ? "제출 중…" : "제출하기"}
              </button>
            </>
          )}
        </div>
      </div>

      {report.status === "rejected" && (
        <div className="rounded-lg border border-seal/30 bg-seal/10 px-4 py-3 text-sm text-seal">
          <b>반려되었습니다.</b>
          {rejectComment ? ` 사유: ${rejectComment}` : ""} 수정 후 다시 제출해 주세요.
        </div>
      )}
      {warningCount > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          ⚠ 검증 경고 <b>{warningCount}건</b> — 3만원 초과 비적격 증빙 또는 금액 불일치 항목이 있습니다. 아래 표의 ‘검증’
          열을 확인하세요.
        </div>
      )}

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
              <th className="px-3 py-3 font-semibold">사용일자</th>
              <th className="px-3 py-3 font-semibold">부서/팀</th>
              <th className="px-3 py-3 text-right font-semibold">공급가액</th>
              <th className="px-3 py-3 text-right font-semibold">부가세</th>
              <th className="px-3 py-3 text-right font-semibold">합계</th>
              <th className="px-3 py-3 font-semibold">증빙유형</th>
              <th className="px-3 py-3 font-semibold">공제</th>
              <th className="px-3 py-3 font-semibold">영수증</th>
              <th className="px-3 py-3 font-semibold">검증</th>
            </tr>
          </thead>
          <tbody>
            {report.items.map((it) => {
              const v = valById[it.id];
              return (
                <tr key={it.id} className="border-b border-gray-50">
                  <td className="px-3 py-3 font-mono">{it.tx_date}</td>
                  <td className="px-3 py-3 text-gray-600">
                    {it.dept_snapshot ?? "-"}
                    {it.team_snapshot ? ` / ${it.team_snapshot}` : ""}
                  </td>
                  <td className="px-3 py-3 text-right font-mono tabular-nums">{won(it.supply_amount)}</td>
                  <td className="px-3 py-3 text-right font-mono tabular-nums">{won(it.vat_amount)}</td>
                  <td className="px-3 py-3 text-right font-mono tabular-nums font-semibold">
                    {won(it.total_amount)}
                  </td>
                  <td className="px-3 py-3">{EVIDENCE_LABEL[it.evidence_type]}</td>
                  <td className="px-3 py-3">
                    <span className={`chip ${it.vat_deductible ? "bg-ledger-soft text-ledger-dark" : "bg-gray-100 text-gray-500"}`}>
                      {it.vat_deductible ? "공제" : "불공제"}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    {it.image_key ? (
                      <button className="text-ledger hover:underline" onClick={() => openReceipt(it.id)}>
                        📎 보기
                      </button>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-xs">
                    {v?.evidence_warning ? (
                      <span className="chip bg-amber-100 text-amber-700">경고</span>
                    ) : v && !v.amount_ok ? (
                      <span className="chip bg-seal/10 text-seal">금액불일치</span>
                    ) : (
                      <span className="chip bg-ledger-soft text-ledger-dark">OK</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-400">
        결제수단 예시: {report.items[0] ? PAY_LABEL[report.items[0].pay_method] : "-"} · 증빙 유형과 계정에 따라 공제 여부가
        자동 판정됩니다.
      </p>

      <div className="card">
        <h2 className="mb-4 font-semibold">승인 이력</h2>
        {history.length === 0 ? (
          <p className="text-sm text-gray-400">아직 이력이 없습니다. 제출하면 승인 흐름이 기록됩니다.</p>
        ) : (
          <ol className="relative ml-2 space-y-4 border-l border-gray-200 pl-5">
            {history.map((h) => (
              <li key={h.id} className="relative">
                <span className="absolute -left-[26px] top-1 h-3 w-3 rounded-full border-2 border-white bg-ledger" />
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className={`chip ${ACTION_STYLE[h.action]}`}>{ACTION_LABEL[h.action]}</span>
                  <span className="text-sm font-medium">{h.actor_name}</span>
                  <span className="font-mono text-xs text-gray-400">{formatDateTime(h.created_at)}</span>
                </div>
                {h.comment && <p className="mt-1 text-sm text-gray-600">“{h.comment}”</p>}
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
