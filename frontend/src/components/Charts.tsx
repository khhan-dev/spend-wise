import { won } from "../lib/format";
import type { MonthAmount, NamedAmount } from "../lib/types";

const LEDGER = "#1C6B4B";

/** 수평 막대 목록 차트 (금액 기준) */
export function BarList({ data }: { data: NamedAmount[] }) {
  if (data.length === 0) return <p className="py-6 text-center text-sm text-gray-400">데이터가 없습니다.</p>;
  const max = Math.max(1, ...data.map((d) => d.amount));
  return (
    <div className="space-y-2.5">
      {data.map((d) => (
        <div key={d.name} className="flex items-center gap-3 text-sm">
          <span className="w-24 shrink-0 truncate text-gray-600" title={d.name}>
            {d.name}
          </span>
          <div className="relative h-5 flex-1 overflow-hidden rounded bg-gray-100">
            <div className="h-full rounded bg-ledger transition-all" style={{ width: `${(d.amount / max) * 100}%` }} />
          </div>
          <span className="w-24 shrink-0 text-right font-mono tabular-nums text-ink">{won(d.amount)}</span>
        </div>
      ))}
    </div>
  );
}

/** 월별 추이 영역 차트 (SVG) */
export function AreaChart({ points }: { points: MonthAmount[] }) {
  if (points.length === 0) return <p className="py-6 text-center text-sm text-gray-400">데이터가 없습니다.</p>;
  const W = 560;
  const H = 160;
  const P = 10;
  const max = Math.max(1, ...points.map((p) => p.amount));
  const n = points.length;
  const x = (i: number) => (n <= 1 ? W / 2 : P + (i * (W - 2 * P)) / (n - 1));
  const y = (v: number) => H - P - (v / max) * (H - 2 * P);
  const line = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.amount).toFixed(1)}`).join(" ");
  const area = `${line} L${x(n - 1).toFixed(1)},${H - P} L${x(0).toFixed(1)},${H - P} Z`;
  const last = points[n - 1];

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="월별 경비 추이">
        <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke="#E5E7EB" strokeWidth="1" />
        <path d={area} fill={LEDGER} fillOpacity="0.1" />
        <path d={line} fill="none" stroke={LEDGER} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {points.map((p, i) => (
          <circle key={p.period} cx={x(i)} cy={y(p.amount)} r={i === n - 1 ? 4 : 2.5} fill={LEDGER} />
        ))}
      </svg>
      <div className="mt-1 flex justify-between px-1 font-mono text-[11px] text-gray-400">
        {points.map((p) => (
          <span key={p.period}>{p.period.slice(2)}</span>
        ))}
      </div>
      <p className="mt-2 text-xs text-gray-500">
        최근 {n}개월 · 최고 <b className="font-mono text-ink">{won(max)}원</b>
        {last && (
          <>
            {" "}
            · 최근({last.period.slice(2)}) <b className="font-mono text-ink">{won(last.amount)}원</b>
          </>
        )}
      </p>
    </div>
  );
}

/** 공제 / 불공제 2분할 막대 */
export function SplitBar({ deductible, nonDeductible }: { deductible: number; nonDeductible: number }) {
  const total = deductible + nonDeductible || 1;
  const dPct = (deductible / total) * 100;
  return (
    <div className="space-y-2">
      <div className="flex h-6 overflow-hidden rounded-md">
        <div className="bg-ledger" style={{ width: `${dPct}%` }} />
        <div className="bg-gray-300" style={{ width: `${100 - dPct}%` }} />
      </div>
      <div className="flex justify-between text-sm">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-ledger" /> 공제{" "}
          <b className="font-mono tabular-nums">{won(deductible)}</b>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-gray-300" /> 불공제{" "}
          <b className="font-mono tabular-nums">{won(nonDeductible)}</b>
        </span>
      </div>
    </div>
  );
}
