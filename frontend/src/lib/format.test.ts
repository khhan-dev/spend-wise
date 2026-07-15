import { describe, expect, it } from "vitest";
import { evidenceWarning, isQualified, splitAmount, won } from "./format";

describe("splitAmount (금액 자동 분리)", () => {
  it("과세 적격(신용카드) 5,000 → 공급 4,545 + 부가 455", () => {
    expect(splitAmount(5000, "card")).toEqual([4545, 455]);
  });

  it("세금계산서 11,000 → 10,000 + 1,000", () => {
    expect(splitAmount(11000, "tax_invoice")).toEqual([10000, 1000]);
  });

  it("간이영수증(비적격)은 전액 공급가액, 부가세 0", () => {
    expect(splitAmount(8000, "simple_receipt")).toEqual([8000, 0]);
  });

  it("계산서(면세)는 부가세 0", () => {
    expect(splitAmount(10000, "invoice")).toEqual([10000, 0]);
  });
});

describe("evidenceWarning (3만원 규칙)", () => {
  it("3만원 초과 비적격 → 경고", () => {
    expect(evidenceWarning(40000, "simple_receipt")).toBeTruthy();
  });

  it("3만원 이하 비적격 → 경고 없음", () => {
    expect(evidenceWarning(20000, "simple_receipt")).toBeNull();
  });

  it("3만원 초과라도 적격증빙 → 경고 없음", () => {
    expect(evidenceWarning(500000, "card")).toBeNull();
  });
});

describe("isQualified (적격증빙 판정)", () => {
  it("적격 4종은 true", () => {
    for (const e of ["tax_invoice", "invoice", "card", "cash_receipt"] as const) {
      expect(isQualified(e)).toBe(true);
    }
  });

  it("간이영수증·기타는 false", () => {
    expect(isQualified("simple_receipt")).toBe(false);
    expect(isQualified("etc")).toBe(false);
  });
});

describe("won (통화 포맷)", () => {
  it("천단위 콤마", () => {
    expect(won(1234567)).toBe("1,234,567");
    expect(won(0)).toBe("0");
  });
});
