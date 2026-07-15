import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BarList, SplitBar } from "./Charts";

describe("BarList", () => {
  it("항목명과 금액을 렌더한다", () => {
    render(<BarList data={[{ name: "복리후생비", amount: 11000 }, { name: "소모품비", amount: 40000 }]} />);
    expect(screen.getByText("복리후생비")).toBeInTheDocument();
    expect(screen.getByText("소모품비")).toBeInTheDocument();
    expect(screen.getByText("40,000")).toBeInTheDocument();
  });

  it("빈 데이터는 안내 문구를 보여준다", () => {
    render(<BarList data={[]} />);
    expect(screen.getByText(/데이터가 없습니다/)).toBeInTheDocument();
  });
});

describe("SplitBar", () => {
  it("공제·불공제 금액을 표시한다", () => {
    render(<SplitBar deductible={11000} nonDeductible={62000} />);
    expect(screen.getByText("공제")).toBeInTheDocument();
    expect(screen.getByText("11,000")).toBeInTheDocument();
    expect(screen.getByText("62,000")).toBeInTheDocument();
  });
});
