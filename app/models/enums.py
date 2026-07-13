import enum


class Role(str, enum.Enum):
    employee = "employee"      # 일반 직원
    manager = "manager"        # 팀장 / 부서장 (승인)
    admin = "admin"            # 경영지원실 (관리자)


class ReportStatus(str, enum.Enum):
    draft = "draft"                    # 작성중
    submitted = "submitted"            # 제출(팀장 승인 대기)
    team_approved = "team_approved"    # 팀장 승인
    reviewed = "reviewed"              # 경영지원실 검토 완료
    closed = "closed"                  # 마감(잠금)
    rejected = "rejected"              # 반려


class EvidenceType(str, enum.Enum):
    tax_invoice = "tax_invoice"        # 세금계산서 (적격)
    invoice = "invoice"                # 계산서 (적격, 면세)
    card = "card"                      # 신용카드 매출전표 (적격)
    cash_receipt = "cash_receipt"      # 지출증빙용 현금영수증 (적격)
    simple_receipt = "simple_receipt"  # 간이영수증 (비적격)
    etc = "etc"                        # 기타 (비적격)

    @property
    def is_qualified(self) -> bool:
        """적격증빙 여부."""
        return self in {
            EvidenceType.tax_invoice,
            EvidenceType.invoice,
            EvidenceType.card,
            EvidenceType.cash_receipt,
        }


class PayMethod(str, enum.Enum):
    corporate_card = "corporate_card"  # 법인카드
    personal_card = "personal_card"    # 개인카드
    cash = "cash"                      # 현금


class OcrStatus(str, enum.Enum):
    pending = "pending"    # 처리중
    success = "success"    # 자동 추출 성공
    failed = "failed"      # 실패 → 수동 입력 필요
    manual = "manual"      # 수동 입력됨


class ApprovalAction(str, enum.Enum):
    submit = "submit"
    approve = "approve"
    reject = "reject"
    review = "review"
    close = "close"
