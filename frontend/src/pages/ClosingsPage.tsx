import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints, tokenStore, API_BASE } from "../lib/api";
import type { Closing } from "../lib/types";

export function ClosingsPage() {
  const qc = useQueryClient();
  const [period, setPeriod] = useState(new Date().toISOString().slice(0, 7));
  const [error, setError] = useState<string | null>(null);

  const { data: closings = [] } = useQuery<Closing[]>({
    queryKey: ["closings"],
    queryFn: endpoints.closings,
  });

  const close = useMutation({
    mutationFn: () => endpoints.close(period),
    onSuccess: () => {
      setError(null);
      qc.invalidateQueries({ queryKey: ["closings"] });
      qc.invalidateQueries({ queryKey: ["reports"] });
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "마감에 실패했습니다.";
      setError(detail);
    },
  });

  async function download(c: Closing) {
    // 인증 헤더가 필요하므로 fetch 후 blob 다운로드
    const res = await fetch(endpoints.downloadUrl(c.id), {
      headers: { Authorization: `Bearer ${tokenStore.access()}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `경비마감_${c.period}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">월 마감</h1>
        <p className="text-sm text-gray-500">
          검토완료된 경비를 마감하고 세무 신고용 엑셀을 생성합니다. <span className="text-gray-400">(홈택스 자동수집 미연동)</span>
        </p>
      </div>

      <div className="card flex flex-wrap items-end gap-3">
        <div>
          <label className="label">귀속월</label>
          <input className="input" type="month" value={period} onChange={(e) => setPeriod(e.target.value)} />
        </div>
        <button className="btn-primary" disabled={close.isPending} onClick={() => close.mutate()}>
          {close.isPending ? "마감 중…" : "마감 + 엑셀 생성"}
        </button>
        <p className="text-xs text-gray-400">
          API base: <span className="font-mono">{API_BASE}</span>
        </p>
      </div>
      {error && <p className="text-sm text-seal">{error}</p>}

      <div className="card p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
              <th className="px-4 py-3 font-semibold">귀속월</th>
              <th className="px-4 py-3 font-semibold">마감일시</th>
              <th className="px-4 py-3 font-semibold">산출물</th>
            </tr>
          </thead>
          <tbody>
            {closings.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                  마감 이력이 없습니다.
                </td>
              </tr>
            ) : (
              closings.map((c) => (
                <tr key={c.id} className="border-b border-gray-50">
                  <td className="px-4 py-3 font-mono font-semibold">{c.period}</td>
                  <td className="px-4 py-3 font-mono text-gray-500">
                    {new Date(c.closed_at).toLocaleString("ko-KR")}
                  </td>
                  <td className="px-4 py-3">
                    <button className="btn-ghost" onClick={() => download(c)}>
                      ⬇ 엑셀 다운로드
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
