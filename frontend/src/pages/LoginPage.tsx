import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("employee@company.com");
  const [password, setPassword] = useState("test1234");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) {
    navigate("/", { replace: true });
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch {
      setError("이메일 또는 비밀번호가 올바르지 않습니다.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center px-6">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center gap-2">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-ledger font-mono text-lg font-bold text-white">
            ₩
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight">경비처리</h1>
            <p className="text-xs text-gray-500">경영지원실 경비 관리</p>
          </div>
        </div>
        <form onSubmit={submit} className="card space-y-4">
          <div>
            <label className="label">이메일</label>
            <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
          </div>
          <div>
            <label className="label">비밀번호</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-seal">{error}</p>}
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? "로그인 중…" : "로그인"}
          </button>
          <p className="text-center text-xs text-gray-400">
            데모: admin / manager / employee @company.com · test1234
          </p>
        </form>
      </div>
    </div>
  );
}
