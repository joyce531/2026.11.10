import { useEffect, useRef, useState } from 'react'
import { apiUrl, getJson, newKey, postJson, readFile, type Job } from './api'

type Options = { outfits: string[]; backgrounds: string[]; model: string }
type Approval = { id: string; status: string; created_at: string; outfit: string; background: string; job_id: string | null; video_info: { duration_seconds?: number; width?: number; height?: number } }
type DanceResult = { video_url?: string; size_bytes?: number }

export default function DanceAgentPanel({ userId, onCreated }: { userId: string; onCreated: () => void }) {
  const [options, setOptions] = useState<Options | null>(null)
  const [video, setVideo] = useState<File | null>(null)
  const [portrait, setPortrait] = useState<File | null>(null)
  const [videoPreview, setVideoPreview] = useState('')
  const [portraitPreview, setPortraitPreview] = useState('')
  const [outfit, setOutfit] = useState('')
  const [background, setBackground] = useState('')
  const [style, setStyle] = useState('写实')
  const [description, setDescription] = useState('')
  const [consent, setConsent] = useState(false)
  const [approval, setApproval] = useState<Approval | null>(null)
  const [job, setJob] = useState<Job<DanceResult> | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const inFlight = useRef(false)
  const pendingKey = 'naxi-dance-approval:' + userId

  useEffect(() => { if (!video) { setVideoPreview(''); return }; const url = URL.createObjectURL(video); setVideoPreview(url); return () => URL.revokeObjectURL(url) }, [video])
  useEffect(() => { if (!portrait) { setPortraitPreview(''); return }; const url = URL.createObjectURL(portrait); setPortraitPreview(url); return () => URL.revokeObjectURL(url) }, [portrait])
  useEffect(() => {
    getJson<Options>('/api/agents/dance/options').then(value => { setOptions(value); setOutfit(value.outfits[0] ?? ''); setBackground(value.backgrounds[0] ?? '') }).catch(e => setError(e.message))
    getJson<{requests:Approval[]}>('/api/agents/dance/requests').then(value => setApproval(value.requests[0] ?? null)).catch(e => setError(e.message))
    const key = localStorage.getItem(pendingKey)
    if (key) getJson<Approval>('/api/agents/dance/requests/by-key/' + key).then(setApproval).catch(() => { /* Keep key after ambiguous submission. */ })
  }, [pendingKey])

  const submit = async () => {
    if (inFlight.current || !video || !portrait || !consent || !outfit || !background || approval) return
    inFlight.current = true; setBusy(true); setError('')
    const key = localStorage.getItem(pendingKey) || newKey()
    localStorage.setItem(pendingKey, key)
    try {
      const [videoData, portraitData] = await Promise.all([readFile(video, 50*1048576), readFile(portrait, 10*1048576)])
      const value = await postJson<Approval>('/api/agents/dance/requests', {video:videoData,portrait:portraitData,outfit,background,style,description,consent:true}, key)
      setApproval(value); setJob(null); onCreated()
    } catch (e) {
      setError(e instanceof Error ? e.message : '申请失败。')
      try { setApproval(await getJson<Approval>('/api/agents/dance/requests/by-key/' + key)) }
      catch { /* No known server application: retain key to avoid duplicates. */ }
    } finally { inFlight.current=false; setBusy(false) }
  }
  const refresh = async () => {
    if (!approval || inFlight.current) return
    inFlight.current=true; setBusy(true); setError('')
    try {
      const latest = await getJson<Approval>('/api/agents/dance/requests/' + approval.id)
      setApproval(latest)
      if (latest.job_id) setJob(await getJson<Job<DanceResult>>('/api/agents/dance/jobs/' + latest.job_id))
      onCreated()
    } catch (e) { setError(e instanceof Error ? e.message : '查询失败。') }
    finally { inFlight.current=false; setBusy(false) }
  }
  const reset = () => { localStorage.removeItem(pendingKey); setApproval(null); setJob(null); setConsent(false); setError('') }
  const picture = (kind:string, name:string) => apiUrl('/api/agents/dance/assets/' + kind + '/' + encodeURIComponent(name))
  return <div className="agent-workflow"><h2>玩家视频编辑 · 管理员审批后调用 Wan</h2><p>上传本人的 2–10 秒舞蹈 MP4 与个人照片，选择参考服饰和背景。点击申请只保存私有素材，不调用 Wan；管理员二次确认批准后才可能产生费用。</p>
    <div className="agent-form-grid"><label>本人舞蹈 MP4（≤50 MB）<input type="file" accept="video/mp4,.mp4" onChange={e => setVideo(e.target.files?.[0] ?? null)}/></label><label>个人照片（PNG/JPG，≤10 MB）<input type="file" accept="image/png,image/jpeg" onChange={e => setPortrait(e.target.files?.[0] ?? null)}/></label></div>
    {videoPreview && <video className="agent-input-video" src={videoPreview} controls playsInline aria-label="本人原视频预览"/>}{portraitPreview && <img className="agent-portrait" src={portraitPreview} alt="本人照片预览"/>}
    {options && <><div className="agent-form-grid"><label>服饰参考图<select value={outfit} onChange={e => setOutfit(e.target.value)}>{options.outfits.map(name => <option key={name}>{name}</option>)}</select></label><label>背景参考图<select value={background} onChange={e => setBackground(e.target.value)}>{options.backgrounds.map(name => <option key={name}>{name}</option>)}</select></label></div><div className="agent-image-pair">{outfit && <figure><img src={picture('outfit',outfit)} alt={'服饰：'+outfit}/><figcaption>{outfit}（原素材，身份与授权待核实）</figcaption></figure>}{background && <figure><img src={picture('background',background)} alt={'背景：'+background}/><figcaption>{background}</figcaption></figure>}</div></>}
    <div className="agent-form-grid"><label>画面风格<input value={style} maxLength={80} onChange={e => setStyle(e.target.value)}/></label><label>补充说明<input value={description} maxLength={500} onChange={e => setDescription(e.target.value)}/></label></div>
    <label><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/> 我确认有权使用本人视频与照片，并同意管理员批准后发送至百炼。</label>
    <button className="primary" disabled={busy || !video || !portrait || !outfit || !background || !consent || !!approval} onClick={submit}>{busy ? '处理中…' : '申请生成视频'}</button>
    {error && <p className="agent-error" role="alert">{error}</p>}
    {approval && <div className="agent-result"><h3>申请状态：{approval.status}</h3><p>申请时间：{new Date(approval.created_at).toLocaleString('zh-CN')} · 服饰：{approval.outfit} · 背景：{approval.background}</p><p>批准前不会创建 Wan 任务。{approval.job_id ? `生成任务：${approval.job_id}` : '等待管理员审批。'}</p><button disabled={busy} onClick={refresh}>查询申请及生成状态</button>{['rejected','failed','cancelled','succeeded'].includes(approval.status) && <button onClick={reset}>开始新申请</button>}</div>}
    {job && <div className="agent-result"><h3>生成任务：{job.status}</h3>{job.error && <p role="alert">{job.error}</p>}{job.status === 'SUCCEEDED' && job.result?.video_url && <><video className="agent-output-video" src={apiUrl(job.result.video_url)} crossOrigin="use-credentials" controls playsInline aria-label="AI 生成视频"/><a href={apiUrl(job.result.video_url)} download={'naxi-dance-'+job.task_id+'.mp4'}>下载生成 MP4</a></>}</div>}
  </div>
}
