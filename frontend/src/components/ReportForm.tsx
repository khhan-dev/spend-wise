import { useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, endpoints } from "../lib/api";
import {
  EVIDENCE_LABEL,
  PAY_LABEL,
  evidenceWarning,
  splitAmount,
  won,
} from "../lib/format";
import type { Account, EvidenceType, PayMethod } from "../lib/types";

export interface Row {
  tx_date: string;
  total_amount: number;
  account_id: string;
  vendor_name: string;
  evidence_type: EvidenceType;
  pay_method: PayMethod;
  memo: string;
}

export const emptyRow = (): Row => ({
  tx_date: new Date().toISOString().slice(0, 10),
  total_amount: 0,
  account_id: "",
  vendor_name: "",
  evidence_type: "card",
  pay_method: "corporate_card",
  memo: "",
});

interface Props {
  reportId?: string; // 있으면 수정(PUT), 없으면 생성(POST)
  initialTitle?: string;
  initialPeriod?: string;
  initialRows?: Row[];
}

export function ReportForm({ reportId, initialTitle, initialPeriod, initialRows }: Props) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const { data: accounts = [] } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: endpoints.accounts,
  });

  const [title, setTitle] = useState(initialTitle ?? "");
  const [period, setPeriod] = useState(initialPeriod ?? new Date().toISOString().slice(0, 7));
  const [rows, setRows] = useState<Row[]>(initialRows ?? [emptyRow()]);
  const [ocrNote, setOcrNote] = useState<string | null>(null);

  const update = (i: number, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  const save = useMutation({
    mutationFn: () => {
      const payload = {
        title,
        period,
        items: rows.map((r) => ({
          tx_date: r.tx_date,
          total_amount: r.total_amount,
          account_id: r.account_id || null,
          vendor_name: r.vendor_name || undefined,
          evidence_type: r.evidence_type,
          pay_method: r.pay_method,
          memo: r.memo || undefined,
        })),
      };
      return reportId
        ? endpoints.updateReport(reportId, payload)
        : endpoints.createReport(payload);
    },
    onSuccess: (report) => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      if (reportId) qc.invalidateQueries({ queryKey: ["report", reportId] });
      navigate(`/expenses/${report.id}`);
    },
  });

  async function onOcr(file: File) {
    setOcrNote("영수증 인식 중…");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await api.post("/api/v1/receipts/ocr", form);
      if (res.data.manual_input_required) {
        setRows((rs) => [...rs, emptyRow()]);
        setOcrNote("자동 인식이 어려워 빈 항목을 추가했습니다. 직접 입력해 주세요.");
      } else {
        setOcrNote("인식 완료 — 항목에 반영되었습니다.");
      }
    } catch {
      setOcrNote("OCR 처리 중 오류가 발생했습니다.");
    }
  }

  const grandTotal = rows.reduce((s, r) => s + (r.total_amount || 0), 0);
  const canSubmit = title.trim() !== "" && rows.length > 0 && rows.every((r) => r.total_amount > 0);

  return (
    <div className="space-y-5">
      <div className="card space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label">제목</label>
            <input
              className="input"
              placeholder="예) 7월 팀 경비"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="label">귀속월</label>
            <input className="input" type="month" value={period} onChange={(e) => setPeriod(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="font-semibold">경비 항목</h2>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => fileRef.current?.click()}>
            📷 영수증 OCR
          </button>
          <button className="btn-ghost" onClick={() => setRows((rs) => [...rs, emptyRow()])}>
            + 항목 추가
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => e.target.files?.[0] && onOcr(e.target.files[0])}
          />
        </div>
      </div>

      {ocrNote && (
        <div className="rounded-lg bg-ledger-soft px-4 py-2 text-sm text-ledger-dark">{ocrNote}</div>
      )}

      <div className="space-y-3">
        {rows.map((r, i) => {
          const [supply, vat] = splitAmount(r.total_amount || 0, r.evidence_type);
          const warn = evidenceWarning(r.total_amount || 0, r.evidence_type);
          return (
            <div key={i} className="card space-y-3">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <label className="label">사용일자</label>
                  <input
                    className="input"
                    type="date"
                    value={r.tx_date}
                    onChange={(e) => update(i, { tx_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">합계금액 (원)</label>
                  <input
                    className="input text-right font-mono"
                    type="number"
                    min={0}
                    value={r.total_amount || ""}
                    onChange={(e) => update(i, { total_amount: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="label">계정과목</label>
                  <select
                    className="input"
                    value={r.account_id}
                    onChange={(e) => update(i, { account_id: e.target.value })}
                  >
                    <option value="">선택</option>
                    {accounts.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">거래처</label>
                  <input
                    className="input"
                    value={r.vendor_name}
                    onChange={(e) => update(i, { vendor_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="label">증빙유형</label>
                  <select
                    className="input"
                    value={r.evidence_type}
                    onChange={(e) => update(i, { evidence_type: e.target.value as EvidenceType })}
                  >
                    {Object.entries(EVIDENCE_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">결제수단</label>
                  <select
                    className="input"
                    value={r.pay_method}
                    onChange={(e) => update(i, { pay_method: e.target.value as PayMethod })}
                  >
                    {Object.entries(PAY_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="lg:col-span-2">
                  <label className="label">적요</label>
                  <input
                    className="input"
                    value={r.memo}
                    onChange={(e) => update(i, { memo: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                <span>
                  공급가액 <b className="font-mono text-ink">{won(supply)}</b>
                </span>
                <span>
                  부가세 <b className="font-mono text-ink">{won(vat)}</b>
                </span>
                {warn && <span className="chip bg-amber-100 text-amber-700">{warn}</span>}
                {rows.length > 1 && (
                  <button
                    className="ml-auto text-seal hover:underline"
                    onClick={() => setRows((rs) => rs.filter((_, idx) => idx !== i))}
                  >
                    삭제
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="card flex items-center justify-between">
        <div>
          <span className="text-sm text-gray-500">합계 </span>
          <span className="font-mono text-xl font-bold tabular-nums">{won(grandTotal)}원</span>
        </div>
        <button className="btn-primary" disabled={!canSubmit || save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? "저장 중…" : reportId ? "수정 저장" : "신청서 저장"}
        </button>
      </div>
      {save.isError && <p className="text-sm text-seal">저장에 실패했습니다. 입력값을 확인해 주세요.</p>}
    </div>
  );
}
