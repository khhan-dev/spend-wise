import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { endpoints } from "../lib/api";
import { ROLE_LABEL } from "../lib/format";
import type { CompanyTree, Department, Role, User } from "../lib/types";

type OnErr = (e: unknown) => void;
const errDetail = (e: unknown) =>
  (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "작업에 실패했습니다.";

export function AdminPage() {
  const [err, setErr] = useState<string | null>(null);
  const onErr: OnErr = (e) => setErr(errDetail(e));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">조직 · 사용자 관리</h1>
        <p className="text-sm text-gray-500">부서·팀을 구성하고 직원 계정을 관리합니다.</p>
      </div>
      {err && (
        <div className="rounded-lg bg-seal/10 px-4 py-2 text-sm text-seal" role="alert">
          {err}
        </div>
      )}
      <OrgSection onErr={onErr} clearErr={() => setErr(null)} />
      <UsersSection onErr={onErr} clearErr={() => setErr(null)} />
    </div>
  );
}

// ── 조직 (부서/팀) ───────────────────────────────
function OrgSection({ onErr, clearErr }: { onErr: OnErr; clearErr: () => void }) {
  const qc = useQueryClient();
  const { data: org } = useQuery<CompanyTree>({ queryKey: ["org"], queryFn: endpoints.org });
  const refresh = () => {
    clearErr();
    qc.invalidateQueries({ queryKey: ["org"] });
  };

  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const addDept = useMutation({
    mutationFn: () => endpoints.createDepartment({ name, code: code || undefined }),
    onSuccess: () => {
      setName("");
      setCode("");
      refresh();
    },
    onError: onErr,
  });

  return (
    <div className="card space-y-4">
      <div className="flex items-baseline justify-between">
        <h2 className="font-semibold">조직 — {org?.name ?? ""}</h2>
        <span className="font-mono text-xs text-gray-400">{org?.biz_no ?? ""}</span>
      </div>

      <div className="space-y-3">
        {org?.departments.map((d) => (
          <DepartmentItem key={d.id} department={d} onErr={onErr} refresh={refresh} />
        ))}
        {org?.departments.length === 0 && <p className="text-sm text-gray-400">등록된 부서가 없습니다.</p>}
      </div>

      <div className="flex flex-wrap items-end gap-2 border-t border-gray-100 pt-4">
        <div className="flex-1">
          <label className="label">새 부서명</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="예) 영업본부" />
        </div>
        <div className="w-32">
          <label className="label">코드(선택)</label>
          <input className="input" value={code} onChange={(e) => setCode(e.target.value)} placeholder="SALES" />
        </div>
        <button className="btn-primary" disabled={!name.trim() || addDept.isPending} onClick={() => addDept.mutate()}>
          부서 추가
        </button>
      </div>
    </div>
  );
}

function DepartmentItem({
  department,
  onErr,
  refresh,
}: {
  department: Department;
  onErr: OnErr;
  refresh: () => void;
}) {
  const [teamName, setTeamName] = useState("");
  const [editDept, setEditDept] = useState(false);
  const [dName, setDName] = useState(department.name);
  const [dCode, setDCode] = useState(department.code ?? "");
  const [editTeamId, setEditTeamId] = useState<string | null>(null);
  const [tName, setTName] = useState("");

  const addTeam = useMutation({
    mutationFn: () => endpoints.createTeam({ department_id: department.id, name: teamName }),
    onSuccess: () => {
      setTeamName("");
      refresh();
    },
    onError: onErr,
  });
  const delTeam = useMutation({ mutationFn: (id: string) => endpoints.deleteTeam(id), onSuccess: refresh, onError: onErr });
  const delDept = useMutation({ mutationFn: () => endpoints.deleteDepartment(department.id), onSuccess: refresh, onError: onErr });
  const renameDept = useMutation({
    mutationFn: () => endpoints.updateDepartment(department.id, { name: dName, code: dCode || undefined }),
    onSuccess: () => {
      setEditDept(false);
      refresh();
    },
    onError: onErr,
  });
  const renameTeam = useMutation({
    mutationFn: (id: string) => endpoints.updateTeam(id, { name: tName }),
    onSuccess: () => {
      setEditTeamId(null);
      refresh();
    },
    onError: onErr,
  });

  return (
    <div className="rounded-lg border border-gray-200 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        {editDept ? (
          <div className="flex flex-1 items-center gap-2">
            <input className="input py-1 text-sm" value={dName} onChange={(e) => setDName(e.target.value)} autoFocus />
            <input
              className="input w-24 py-1 text-sm"
              value={dCode}
              onChange={(e) => setDCode(e.target.value)}
              placeholder="코드"
            />
            <button
              className="text-xs font-semibold text-ledger hover:underline disabled:opacity-40"
              disabled={!dName.trim() || renameDept.isPending}
              onClick={() => renameDept.mutate()}
            >
              저장
            </button>
            <button
              className="text-xs text-gray-400 hover:underline"
              onClick={() => {
                setEditDept(false);
                setDName(department.name);
                setDCode(department.code ?? "");
              }}
            >
              취소
            </button>
          </div>
        ) : (
          <>
            <div className="font-medium">
              {department.name}
              {department.code && <span className="ml-2 font-mono text-xs text-gray-400">{department.code}</span>}
            </div>
            <div className="flex gap-3">
              <button className="text-xs text-gray-400 hover:text-ledger" onClick={() => setEditDept(true)}>
                이름 수정
              </button>
              <button className="text-xs text-gray-400 hover:text-seal" onClick={() => delDept.mutate()}>
                부서 삭제
              </button>
            </div>
          </>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {department.teams.map((t) =>
          editTeamId === t.id ? (
            <span key={t.id} className="inline-flex items-center gap-1">
              <input
                className="w-24 rounded-md border border-gray-300 px-2 py-1 text-xs outline-none focus:border-ledger"
                value={tName}
                onChange={(e) => setTName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && tName.trim() && renameTeam.mutate(t.id)}
                autoFocus
              />
              <button className="text-xs font-semibold text-ledger hover:underline" onClick={() => renameTeam.mutate(t.id)}>
                저장
              </button>
              <button className="text-xs text-gray-400" onClick={() => setEditTeamId(null)}>
                취소
              </button>
            </span>
          ) : (
            <span key={t.id} className="chip bg-ledger-soft text-ledger-dark">
              {t.name}
              <button
                className="ml-1 text-ledger-dark/50 hover:text-ledger-dark"
                title="이름 수정"
                onClick={() => {
                  setEditTeamId(t.id);
                  setTName(t.name);
                }}
              >
                ✎
              </button>
              <button className="ml-0.5 text-ledger-dark/60 hover:text-seal" title="삭제" onClick={() => delTeam.mutate(t.id)}>
                ×
              </button>
            </span>
          )
        )}
        <span className="inline-flex items-center gap-1">
          <input
            className="w-28 rounded-md border border-gray-300 px-2 py-1 text-xs outline-none focus:border-ledger"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            placeholder="팀 추가"
            onKeyDown={(e) => e.key === "Enter" && teamName.trim() && addTeam.mutate()}
          />
          <button
            className="text-xs font-semibold text-ledger hover:underline disabled:opacity-40"
            disabled={!teamName.trim() || addTeam.isPending}
            onClick={() => addTeam.mutate()}
          >
            + 팀
          </button>
        </span>
      </div>
    </div>
  );
}

// ── 사용자 ───────────────────────────────────────
const ROLES: Role[] = ["employee", "manager", "admin"];

function UsersSection({ onErr, clearErr }: { onErr: OnErr; clearErr: () => void }) {
  const qc = useQueryClient();
  const { data: users = [] } = useQuery<User[]>({ queryKey: ["users"], queryFn: endpoints.users });
  const { data: org } = useQuery<CompanyTree>({ queryKey: ["org"], queryFn: endpoints.org });
  const teams = org?.departments.flatMap((d) => d.teams.map((t) => ({ id: t.id, label: `${d.name} / ${t.name}` }))) ?? [];
  const refresh = () => {
    clearErr();
    qc.invalidateQueries({ queryKey: ["users"] });
  };

  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: unknown }) => endpoints.updateUser(id, body),
    onSuccess: refresh,
    onError: onErr,
  });

  const [form, setForm] = useState({ name: "", email: "", password: "", role: "employee" as Role, team_id: "" });
  const create = useMutation({
    mutationFn: () =>
      endpoints.createUser({
        name: form.name,
        email: form.email,
        password: form.password,
        role: form.role,
        team_id: form.team_id || null,
      }),
    onSuccess: () => {
      setForm({ name: "", email: "", password: "", role: "employee", team_id: "" });
      refresh();
    },
    onError: onErr,
  });

  return (
    <div className="card space-y-4">
      <h2 className="font-semibold">사용자</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs text-gray-500">
              <th className="px-2 py-2 font-semibold">이름</th>
              <th className="px-2 py-2 font-semibold">이메일</th>
              <th className="px-2 py-2 font-semibold">역할</th>
              <th className="px-2 py-2 font-semibold">소속 팀</th>
              <th className="px-2 py-2 font-semibold">활성</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-gray-50">
                <td className="px-2 py-2 font-medium">{u.name}</td>
                <td className="px-2 py-2 font-mono text-xs text-gray-500">{u.email}</td>
                <td className="px-2 py-2">
                  <select
                    className="rounded-md border border-gray-300 px-2 py-1 text-xs"
                    value={u.role}
                    onChange={(e) => update.mutate({ id: u.id, body: { role: e.target.value } })}
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {ROLE_LABEL[r]}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-2">
                  <select
                    className="rounded-md border border-gray-300 px-2 py-1 text-xs"
                    value={u.team_id ?? ""}
                    onChange={(e) => update.mutate({ id: u.id, body: { team_id: e.target.value || null } })}
                  >
                    <option value="">(없음)</option>
                    {teams.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-2">
                  <button
                    className={`chip ${u.is_active ? "bg-ledger-soft text-ledger-dark" : "bg-gray-100 text-gray-500"}`}
                    onClick={() => update.mutate({ id: u.id, body: { is_active: !u.is_active } })}
                  >
                    {u.is_active ? "활성" : "비활성"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-2 border-t border-gray-100 pt-4 sm:grid-cols-2 lg:grid-cols-5">
        <input className="input" placeholder="이름" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input className="input" placeholder="이메일" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input
          className="input"
          type="password"
          placeholder="초기 비밀번호"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABEL[r]}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <select className="input" value={form.team_id} onChange={(e) => setForm({ ...form, team_id: e.target.value })}>
            <option value="">팀(선택)</option>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
          <button
            className="btn-primary whitespace-nowrap"
            disabled={!form.name.trim() || !form.email.trim() || !form.password || create.isPending}
            onClick={() => create.mutate()}
          >
            추가
          </button>
        </div>
      </div>
    </div>
  );
}
