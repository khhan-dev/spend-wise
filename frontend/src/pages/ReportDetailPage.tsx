import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link, useNavigate } from "react-router-dom";
import { authedBlob, endpoints } from "../lib/api";
import { useAuth } from "../auth/AuthContext";
import {
  EVIDENCE_LABEL,
  PAY_LABEL,
  STATUS_LABEL,
  STATUS_STYLE,
  won,
} from "../lib/format";
import type { ExpenseReport, ItemValidation } from "../lib/types";

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

  const submit = useMutation({
    mutationFn: () => endpoints.submitReport(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["report", id] });
      qc.invalidateQueries({ queryKey: ["reports"] });
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
    </div>
  );
}
