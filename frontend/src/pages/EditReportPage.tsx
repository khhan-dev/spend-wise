import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { endpoints } from "../lib/api";
import { ReportForm, type Row } from "../components/ReportForm";
import type { ExpenseReport } from "../lib/types";

export function EditReportPage() {
  const { id = "" } = useParams();
  const { data: report, isLoading } = useQuery<ExpenseReport>({
    queryKey: ["report", id],
    queryFn: () => endpoints.report(id),
  });

  if (isLoading || !report) return <p className="text-gray-400">불러오는 중…</p>;

  if (report.status !== "draft" && report.status !== "rejected") {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">경비 신청서 수정</h1>
        <div className="card text-sm text-gray-500">
          제출 이후에는 수정할 수 없습니다.{" "}
          <Link to={`/expenses/${id}`} className="text-ledger hover:underline">
            상세로 돌아가기
          </Link>
        </div>
      </div>
    );
  }

  const rows: Row[] = report.items.map((it) => ({
    tx_date: it.tx_date,
    total_amount: it.total_amount,
    account_id: it.account_id ?? "",
    vendor_name: it.vendor_name ?? "",
    evidence_type: it.evidence_type,
    pay_method: it.pay_method,
    memo: it.memo ?? "",
    image_key: it.image_key,
  }));

  return (
    <div className="space-y-5">
      <Link to={`/expenses/${id}`} className="text-sm text-gray-400 hover:underline">
        ← 상세로
      </Link>
      <h1 className="text-2xl font-bold">경비 신청서 수정</h1>
      <ReportForm
        reportId={id}
        initialTitle={report.title}
        initialPeriod={report.period}
        initialRows={rows.length > 0 ? rows : undefined}
      />
    </div>
  );
}
