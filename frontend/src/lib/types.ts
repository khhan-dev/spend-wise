export type Role = "employee" | "manager" | "admin";

export type EvidenceType =
  | "tax_invoice"
  | "invoice"
  | "card"
  | "cash_receipt"
  | "simple_receipt"
  | "etc";

export type PayMethod = "corporate_card" | "personal_card" | "cash";

export type ReportStatus =
  | "draft"
  | "submitted"
  | "team_approved"
  | "reviewed"
  | "closed"
  | "rejected";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  team_id: string | null;
  is_active: boolean;
}

export interface Account {
  id: string;
  name: string;
  default_deductible: boolean;
}

export interface ExpenseItem {
  id: string;
  tx_date: string;
  supply_amount: number;
  vat_amount: number;
  total_amount: number;
  account_id: string | null;
  evidence_type: EvidenceType;
  pay_method: PayMethod;
  vat_deductible: boolean;
  dept_snapshot: string | null;
  team_snapshot: string | null;
  pjt_code: string | null;
  memo: string | null;
}

export interface ExpenseReport {
  id: string;
  title: string;
  period: string;
  status: ReportStatus;
  user_id: string;
  created_at: string;
  items: ExpenseItem[];
}

export interface ItemValidation {
  item_id: string;
  evidence_warning: string | null;
  amount_ok: boolean;
}

export interface Closing {
  id: string;
  period: string;
  closed_at: string;
  export_key: string | null;
}

export interface ExpenseItemInput {
  tx_date: string;
  total_amount: number;
  account_id: string | null;
  vendor_name?: string;
  evidence_type: EvidenceType;
  pay_method: PayMethod;
  memo?: string;
}
