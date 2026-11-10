import { useEffect, useState } from 'react'
import { getJson, postJson } from './api'

type Quota = Record<string, {limit:number;used:number;remaining:number}>
export default function QuotaPanel() {
  const [quota, setQuota] = useState<Quota | null>(null)
  const [notice, setNotice] = useState('')
  useEffect(() => { getJson<Quota>('/api/quotas/me').then(setQuota).catch(e => setNotice(e.message)) }, [])
  const request = async (agent:string) => {
    try { await postJson('/api/quotas/requests', {agent}); setNotice('额外体验次数申请已提交，等待管理员审核。') }
    catch (e) { setNotice(e instanceof Error ? e.message : '申请失败。') }
  }
  return <div className="quota-panel"><span>今日东巴文剩余 {quota?.dongba.remaining ?? '…'} / {quota?.dongba.limit ?? '…'} 次</span><span>古乐外部模型剩余 {quota?.music.remaining ?? '…'} / {quota?.music.limit ?? '…'} 次</span>{quota?.dongba.remaining === 0 && <button onClick={() => request('dongba')}>申请东巴文额度</button>}{quota?.music.remaining === 0 && <button onClick={() => request('music')}>申请古乐额度</button>}{notice && <small role="status">{notice}</small>}</div>
}
