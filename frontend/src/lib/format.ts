import type { ApprovalAction, EvidenceType, PayMethod, ReportStatus, Role } from "./types";

export const won = (n: number) => n.toLocaleString("ko-KR");

export const EVIDENCE_LABEL: Record<EvidenceType, string> = {
  tax_invoice: "세금계산서",
  invoice: "계산서",
  card: "신용카드",
  cash_receipt: "현금영수증",
  simple_receipt: "간이영수증",
  etc: "기타",
};

export const PAY_LABEL: Record<PayMethod, string> = {
  corporate_card: "법인카드",
  personal_card: "개인카드",
  cash: "현금",
};

export const STATUS_LABEL: Record<ReportStatus, string> = {
  draft: "작성중",
  submitted: "제출",
  team_approved: "팀장승인",
  reviewed: "검토완료",
  closed: "마감",
  rejected: "반려",
};

export const STATUS_STYLE: Record<ReportStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  submitted: "bg-blue-100 text-blue-700",
  team_approved: "bg-indigo-100 text-indigo-700",
  reviewed: "bg-ledger-soft text-ledger-dark",
  closed: "bg-ledger text-white",
  rejected: "bg-seal/10 text-seal",
};

export const ROLE_LABEL: Record<Role, string> = {
  employee: "일반 직원",
  manager: "팀장",
  admin: "경영지원실",
};

export const ACTION_LABEL: Record<ApprovalAction, string> = {
  submit: "제출",
  approve: "팀장 승인",
  reject: "반려",
  review: "검토 완료",
  close: "마감",
};

export const ACTION_STYLE: Record<ApprovalAction, string> = {
  submit: "bg-blue-100 text-blue-700",
  approve: "bg-indigo-100 text-indigo-700",
  reject: "bg-seal/10 text-seal",
  review: "bg-ledger-soft text-ledger-dark",
  close: "bg-ledger text-white",
};

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// 백엔드 규칙 미러 — 입력 폼 실시간 미리보기용
const VAT_BEARING: EvidenceType[] = ["tax_invoice", "card", "cash_receipt"];

export function splitAmount(total: number, evidence: EvidenceType): [number, number] {
  if (VAT_BEARING.includes(evidence)) {
    const supply = Math.round(total / 1.1);
    return [supply, total - supply];
  }
  return [total, 0];
}

export function isQualified(evidence: EvidenceType): boolean {
  return ["tax_invoice", "invoice", "card", "cash_receipt"].includes(evidence);
}

export function evidenceWarning(total: number, evidence: EvidenceType): string | null {
  if (total > 30000 && !isQualified(evidence)) {
    return "⚠ 3만원 초과 비적격 증빙 — 증빙불비가산세 대상";
  }
  return null;
}
