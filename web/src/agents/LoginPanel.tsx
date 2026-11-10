import { useState } from 'react'
import { postJson } from './api'

export type User = { id: string; username: string; role: 'admin' | 'judge'; active: number; expires_at: string | null }
export type Auth = { user: User; quota: Record<string, { limit: number; used: number; remaining: number }> }

export default function LoginPanel({ onLogin }: { onLogin: (auth: Auth) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); if (busy) return
    setBusy(true); setError('')
    try { onLogin(await postJson<Auth>('/api/auth/login', { username, password })); setPassword('') }
    catch (e) { setError(e instanceof Error ? e.message : '登录失败，请稍后重试。') }
    finally { setBusy(false) }
  }
  return <main className="page agent-page"><p className="eyebrow">NAXI AI STUDIO</p><h1>账号登录</h1><p className="page-lead">游戏章节可作为游客游玩。使用 AI Agent 和查看个人作品需要登录管理员或评委账号。</p>
    <form className="agent-workflow login-form" onSubmit={submit}><label>用户名<input autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required/></label><label>密码<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required/></label><button className="primary" disabled={busy}>{busy ? '登录中…' : '登录'}</button>{error && <p role="alert">{error}</p>}</form>
  </main>
}
