import { useEffect, useState } from 'react'
import { getJson, postJson } from './api'

type User = { id: string; username: string; role: string; active: number; created_at: string; expires_at: string | null; last_login: string | null }
type Approval = { id: string; user_id: string; status: string; created_at: string; outfit: string; background: string; video_info: { duration?: number; size_bytes?: number; width?: number; height?: number }; job_id?: string }
type QuotaRequest = { id: string; user_id: string; agent: string; status: string; created_at: string }
type Usage = { username: string; agent: string; created_at: string; status: string; model: string | null; job_id: string | null }

export default function AdminPanel() {
  const [users, setUsers] = useState<User[]>([])
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [requests, setRequests] = useState<QuotaRequest[]>([])
  const [usage, setUsage] = useState<Usage[]>([])
  const [settings, setSettings] = useState({ quota_dongba: '10', quota_music: '3', ai_paused: 'false' })
  const [name, setName] = useState('')
  const [expiry, setExpiry] = useState('')
  const [oneTimePassword, setOneTimePassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const load = async () => {
    const [a,b,c,d,e] = await Promise.all([
      getJson<{users:User[]}>('/api/admin/users'), getJson<typeof settings>('/api/admin/settings'),
      getJson<{approvals:Approval[]}>('/api/admin/approvals'), getJson<{usage:Usage[]}>('/api/admin/usage'),
      getJson<{requests:QuotaRequest[]}>('/api/admin/quotas/requests')])
    setUsers(a.users); setSettings(b); setApprovals(c.approvals); setUsage(d.usage); setRequests(e.requests)
  }
  useEffect(() => { load().catch(e => setError(e.message)) }, [])
  const run = async (action: () => Promise<unknown>) => { if (busy) return; setBusy(true); setError(''); try { await action(); await load() } catch (e) { setError(e instanceof Error ? e.message : '操作失败。') } finally { setBusy(false) } }
  const userAction = (user: User, action: string) => run(async () => {
    if (action === 'delete' && !window.confirm(`撤销评委 ${user.username} 的账号？历史作品会保留。`)) return
    const value = await postJson<{password?:string}>(`/api/admin/users/${user.id}/${action}`, {})
    if (value.password) setOneTimePassword(`${user.username} 的一次性新密码：${value.password}`)
  })
  return <main className="page agent-page"><p className="eyebrow">管理员专用</p><h1>账号、额度与 AI 审批</h1>{error && <p role="alert">{error}</p>}
    <section className="agent-result"><h2>账号管理</h2><p>初始密码只显示一次。请当面或通过可信渠道交给评委。</p><div className="agent-form-grid"><label>评委用户名<input value={name} onChange={e => setName(e.target.value)}/></label><label>到期时间（可选）<input type="datetime-local" value={expiry} onChange={e => setExpiry(e.target.value)}/></label></div><button disabled={busy} onClick={() => run(async () => { const value = await postJson<{initial_password:string}>('/api/admin/users', {username:name, expires_at:expiry ? new Date(expiry).toISOString() : null}); setOneTimePassword(`${name} 的一次性初始密码：${value.initial_password}`); setName('') })}>创建评委账号</button>{oneTimePassword && <p className="one-time-password" role="status">{oneTimePassword} <button onClick={() => setOneTimePassword('')}>关闭</button></p>}
      <div className="review-scroll"><table><thead><tr><th>账号</th><th>角色</th><th>状态</th><th>创建 / 到期 / 最近登录</th><th>管理</th></tr></thead><tbody>{users.map(user => <tr key={user.id}><td>{user.username}</td><td>{user.role}</td><td>{user.active ? '启用' : '禁用'}</td><td>{new Date(user.created_at).toLocaleString('zh-CN')}<br/>{user.expires_at ? new Date(user.expires_at).toLocaleString('zh-CN') : '无到期日'}<br/>{user.last_login ? new Date(user.last_login).toLocaleString('zh-CN') : '未登录'}</td><td>{user.role === 'judge' && <><button disabled={busy} onClick={() => userAction(user, 'reset')}>重置密码</button><button disabled={busy} onClick={() => userAction(user, user.active ? 'disable' : 'enable')}>{user.active ? '禁用' : '启用'}</button><button disabled={busy} onClick={() => userAction(user, 'revoke')}>撤销会话</button><button disabled={busy} onClick={() => userAction(user, 'delete')}>删除/撤销</button><button disabled={busy} onClick={() => { const value = prompt('新的 UTC 到期时间（ISO 8601，留空取消）：'); if (value) void run(() => postJson(`/api/admin/users/${user.id}/expire`, {expires_at:value})) }}>设置到期</button></>}</td></tr>)}</tbody></table></div></section>
    <section className="agent-result"><h2>每日额度与全局开关</h2><div className="agent-form-grid"><label>东巴文每账号每日真实请求<input type="number" min="0" max="1000" value={settings.quota_dongba} onChange={e => setSettings({...settings,quota_dongba:e.target.value})}/></label><label>古乐每账号每日外部请求<input type="number" min="0" max="1000" value={settings.quota_music} onChange={e => setSettings({...settings,quota_music:e.target.value})}/></label></div><label><input type="checkbox" checked={settings.ai_paused === 'true'} onChange={e => setSettings({...settings,ai_paused:e.target.checked ? 'true' : 'false'})}/> 暂停所有 AI 服务</label><button disabled={busy} onClick={() => run(() => postJson('/api/admin/settings', {quota_dongba:Number(settings.quota_dongba),quota_music:Number(settings.quota_music),ai_paused:settings.ai_paused === 'true'}))}>保存设置</button><p>对单个账号追加额度：在下方申请列表审批，或使用账号 ID 直接设置。</p>{users.filter(x=>x.role==='judge').map(user=><div key={user.id}>{user.username}：<button onClick={() => { const value=prompt('东巴文每日上限（0–1000）：'); if (value!==null) void run(() => postJson(`/api/admin/users/${user.id}/quota`, {agent:'dongba',limit:Number(value)})) }}>设置东巴额度</button><button onClick={() => { const value=prompt('古乐每日上限（0–1000）：'); if (value!==null) void run(() => postJson(`/api/admin/users/${user.id}/quota`, {agent:'music',limit:Number(value)})) }}>设置古乐额度</button></div>)}</section>
    <section className="agent-result"><h2>打跳视频审批</h2><p>批准会发起一次可能计费的 Wan 任务；预计费用因当前缺少可核对单价而不展示。</p>{approvals.map(item => <article className="work-card" key={item.id}><strong>{users.find(x=>x.id===item.user_id)?.username || item.user_id} · {item.status}</strong><p>{new Date(item.created_at).toLocaleString('zh-CN')} · 服饰：{item.outfit} · 背景：{item.background}</p><p>原视频：{item.video_info.duration ?? '待核实'} 秒，{item.video_info.width ?? '?'}×{item.video_info.height ?? '?'}，{item.video_info.size_bytes ? (item.video_info.size_bytes/1048576).toFixed(1) : '?'} MB；任务：{item.job_id || '尚未生成'}</p>{item.status === 'pending_approval' && <><button disabled={busy} onClick={() => { if (!window.confirm('批准后将调用 Wan 视频生成 API，可能产生实际费用，是否继续？')) return; void run(() => postJson(`/api/admin/approvals/${item.id}/approve`, {confirm:true})) }}>批准生成</button><button disabled={busy} onClick={() => run(() => postJson(`/api/admin/approvals/${item.id}/reject`, {}))}>拒绝</button><button disabled={busy} onClick={() => { if (window.confirm('删除此待审批申请？')) void run(() => postJson(`/api/admin/approvals/${item.id}/delete`, {})) }}>删除申请</button></>}</article>)}</section>
    <section className="agent-result"><h2>额外体验额度申请</h2>{requests.map(item => <article className="work-card" key={item.id}>{users.find(x=>x.id===item.user_id)?.username || item.user_id} · {item.agent} · {item.status} · {new Date(item.created_at).toLocaleString('zh-CN')}{item.status === 'pending' && <><button onClick={() => run(() => postJson(`/api/admin/quotas/requests/${item.id}/approve`, {}))}>批准增加 5 次</button><button onClick={() => run(() => postJson(`/api/admin/quotas/requests/${item.id}/reject`, {}))}>拒绝</button></>}</article>)}</section>
    <section className="agent-result"><h2>Agent 使用记录</h2><p>仅记录已验证的真实模型结果；不把本地合成和估算费用当作实际账单。异常响应会暂占额度，需人工核查。</p><div className="review-scroll"><table><thead><tr><th>账号</th><th>Agent</th><th>时间</th><th>状态</th><th>模型</th><th>任务 ID</th></tr></thead><tbody>{usage.map((x,i)=><tr key={i}><td>{x.username}</td><td>{x.agent}</td><td>{new Date(x.created_at).toLocaleString('zh-CN')}</td><td>{x.status}</td><td>{x.model || '本地/未确定'}</td><td>{x.job_id || '—'}</td></tr>)}</tbody></table></div></section>
  </main>
}
