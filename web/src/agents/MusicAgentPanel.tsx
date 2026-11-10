import { useEffect, useRef, useState } from 'react'
import { apiUrl, getJson, newKey, postJson, readFile, type Job } from './api'

type Asset = { asset_id: string; label: string; identity_status: string; sample_mapping: { note?: string; mode?: string } | null }
type Row = { start: number | null; duration: number | null; pitch: number | null; rest: boolean; voice: string; symbol: string; uncertain: boolean; issue: string; reviewed: boolean }
type Document = { notation: 'jianpu' | 'staff'; tonic_note?: string | null; tonic_degree?: number | null; bpm?: number | null; meter?: string | null; coverage: string; warnings: string[]; unsupported_symbols: string[]; rows?: Row[]; tempos?: { time: number; bpm: number }[]; engine: string; model?: string }
type Recognition = { kind: 'structured' | 'needs_notation' | 'jianpu' | 'staff'; message?: string; format?: string; note_count?: number; duration_seconds?: number; notes?: unknown[]; warnings?: string[]; document?: Document }
type Review = { rows: Row[]; tempos: { time: number; bpm: number }[]; has_limitations: boolean; warnings: string[]; unsupported_symbols: string[] }
type Arrangement = { mode: string; model: string | null; fallback_reason: string | null; plan: { explanation: string; limitations: string[] }; usage: { label: string; sample_notes: number; auxiliary_notes: number; phrases: number }[]; duration_seconds: number; midi_url: string; wav_url: string; cultural_status: string }
const TONICS = ['', 'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']
const note = (value: string) => value.trim() === '' ? null : Number(value)

export default function MusicAgentPanel({ onCreated }: { onCreated: () => void }) {
  const [assets, setAssets] = useState<Asset[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [encoded, setEncoded] = useState('')
  const [imagePreview, setImagePreview] = useState('')
  const [recognition, setRecognition] = useState<Recognition | null>(null)
  const [review, setReview] = useState<Review | null>(null)
  const [notation, setNotation] = useState('')
  const [tonic, setTonic] = useState('')
  const [degree, setDegree] = useState(1)
  const [octave, setOctave] = useState(4)
  const [bpm, setBpm] = useState(120)
  const [confirmed, setConfirmed] = useState(false)
  const [limitationsAccepted, setLimitationsAccepted] = useState(false)
  const [style, setStyle] = useState('洞经音乐')
  const [preservation, setPreservation] = useState(100)
  const [result, setResult] = useState<Arrangement | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const inFlight = useRef(false)
  const recognizeKey = useRef<string | null>(null)
  const arrangeKey = useRef<string | null>(null)

  useEffect(() => { getJson<{ assets: Asset[] }>('/api/agents/music/assets').then(data => { setAssets(data.assets); setSelected(data.assets.slice(0, 2).map(a => a.asset_id)) }).catch(e => setError(e.message)) }, [])
  const chooseFile = async (next?: File) => {
    setFile(next ?? null); setEncoded(''); setRecognition(null); setReview(null); setResult(null); setError(''); setImagePreview(''); recognizeKey.current = null; arrangeKey.current = null
    if (!next) return
    const suffix = next.name.split('.').pop()?.toLowerCase() ?? ''
    if (!['mid','midi','xml','musicxml','mxl','png','jpg','jpeg','webp'].includes(suffix)) { setError('支持 MIDI、MusicXML/MXL、清晰印刷谱 PNG/JPG/WebP；暂不支持 PDF。'); return }
    try { const value = await readFile(next, suffix.match(/^(mid|midi|xml|musicxml|mxl)$/) ? 2 * 1048576 : 10 * 1048576); setEncoded(value); if (/^(png|jpg|jpeg|webp)$/.test(suffix)) setImagePreview(value) }
    catch (e) { setError(e instanceof Error ? e.message : '无法读取曲谱。') }
  }
  const recognize = async () => {
    if (inFlight.current || !file || !encoded) return
    inFlight.current = true; setBusy(true); setError('')
    try {
      recognizeKey.current ||= newKey()
      const job = await postJson<Job<Recognition>>('/api/agents/music/recognize', { filename: file.name, file: encoded, notation: notation || null }, recognizeKey.current)
      if (!job.result) throw new Error(job.error || '未返回识谱结果。')
      setRecognition(job.result); setReview(null); recognizeKey.current = null; onCreated()
      if (job.result.document) { const doc = job.result.document; setTonic(doc.tonic_note ?? ''); setDegree(doc.tonic_degree ?? 1); setBpm(doc.bpm ?? 120) }
    } catch (e) { setError(e instanceof Error ? e.message : '曲谱识别失败。') }
    finally { inFlight.current = false; setBusy(false) }
  }
  const prepare = async () => {
    if (!recognition?.document || inFlight.current) return
    inFlight.current = true; setBusy(true); setError('')
    try { const data = await postJson<Review>('/api/agents/music/review', { document: recognition.document, tonic, degree, octave, bpm }); setReview(data); setConfirmed(false) }
    catch (e) { setError(e instanceof Error ? e.message : '无法建立校对表。') }
    finally { inFlight.current = false; setBusy(false) }
  }
  const edit = (index: number, patch: Partial<Row>) => { if (!review) return; setReview({ ...review, rows: review.rows.map((row, i) => i === index ? { ...row, ...patch } : row) }); setConfirmed(false); arrangeKey.current = null }
  const generate = async () => {
    if (inFlight.current || !file || !selected.length || !encoded || !recognition || recognition.kind === 'needs_notation') return
    inFlight.current = true; setBusy(true); setError('')
    try {
      const body = review ? { reviewed_rows: review.rows, tempos: review.tempos, confirmed, has_limitations: review.has_limitations,
        limitations_accepted: limitationsAccepted, asset_ids: selected, style, preservation }
        : { filename: file.name, file: encoded, asset_ids: selected, style, preservation }
      if (recognition.kind !== 'structured' && !review) throw new Error('图片识谱必须先建立校对表并确认。')
      arrangeKey.current ||= newKey()
      const job = await postJson<Job<Arrangement>>('/api/agents/music/arrange', body, arrangeKey.current)
      if (!job.result) throw new Error(job.error || '未生成作品。')
      setResult(job.result); arrangeKey.current = null; onCreated()
    } catch (e) { setError(e instanceof Error ? e.message : '生成失败。') }
    finally { inFlight.current = false; setBusy(false) }
  }
  return <div className="agent-workflow"><h2>上传曲谱并生成本地 MIDI / WAV</h2><p>印刷图片先通过现有识谱服务转为待校对音符；确认后才编曲。模型只负责识谱或编曲规划，WAV 由 Python 本地合成。</p>
    <label>曲谱文件 <input type="file" accept=".mid,.midi,.xml,.musicxml,.mxl,.png,.jpg,.jpeg,.webp" onChange={e => void chooseFile(e.target.files?.[0])}/></label>{imagePreview && <img className="score-preview" src={imagePreview} alt="上传曲谱预览"/>}
    {recognition?.kind === 'needs_notation' && <p role="alert">{recognition.message}</p>}{recognition?.kind === 'needs_notation' && <label>手动选择谱式 <select value={notation} onChange={e => { setNotation(e.target.value); recognizeKey.current = null }}><option value="">请选择</option><option value="jianpu">简谱</option><option value="staff">五线谱</option></select></label>}
    <button className="primary" disabled={!encoded || busy || (recognition?.kind === 'needs_notation' && !notation)} onClick={recognize}>{busy ? '处理中…' : '解析／识别曲谱'}</button>
    {recognition?.kind === 'structured' && <div className="agent-result"><h3>曲谱解析预览</h3><p>{recognition.format} · {recognition.note_count} 个音符 · {recognition.duration_seconds?.toFixed(1)} 秒</p><p>解析器的旋律候选仅作改编输入，复杂声部请先在制谱软件校正。</p>{recognition.warnings?.map((w, i) => <p key={i}>{w}</p>)}</div>}
    {recognition?.document && <div className="agent-result"><h3>识谱草稿 · {recognition.document.engine}</h3><p>覆盖范围：{recognition.document.coverage}；不确定项必须逐项校对，不会自动补猜。</p>{recognition.document.warnings?.map((w, i) => <p key={i}>{w}</p>)}{recognition.document.unsupported_symbols?.map((w, i) => <p key={'u' + i}>未支持：{w}</p>)}
      {recognition.kind === 'jianpu' && <div className="agent-form-grid"><label>调号音名（不得默认）<select value={tonic} onChange={e => setTonic(e.target.value)}>{TONICS.map(x => <option key={x} value={x}>{x || '请选择'}</option>)}</select></label><label>等号左侧级数<input type="number" min="1" max="7" value={degree} onChange={e => setDegree(Number(e.target.value))}/></label><label>参考八度<input type="number" min="1" max="6" value={octave} onChange={e => setOctave(Number(e.target.value))}/></label><label>速度 BPM<input type="number" min="20" max="300" value={bpm} onChange={e => setBpm(Number(e.target.value))}/></label></div>}
      <button onClick={prepare} disabled={busy}>建立待校对音符表</button></div>}
    {review && <div className="agent-result"><h3>逐项人工校对（时间：秒，音高：MIDI）</h3><div className="review-scroll"><table><thead><tr><th>#</th><th>原位置／符号</th><th>起点</th><th>时长</th><th>音高</th><th>休止</th><th>待校对原因</th><th>已核对</th></tr></thead><tbody>{review.rows.map((row, i) => <tr key={i}><td>{i + 1}</td><td>{row.symbol}</td><td><input type="number" step="0.01" value={row.start ?? ''} onChange={e => edit(i, { start: note(e.target.value) })}/></td><td><input type="number" step="0.01" value={row.duration ?? ''} onChange={e => edit(i, { duration: note(e.target.value) })}/></td><td><input type="number" min="0" max="127" value={row.pitch ?? ''} onChange={e => edit(i, { pitch: note(e.target.value) })}/></td><td><input type="checkbox" checked={row.rest} onChange={e => edit(i, { rest: e.target.checked })}/></td><td>{row.uncertain ? row.issue || '识别不确定' : '—'}</td><td><input type="checkbox" checked={row.reviewed} onChange={e => edit(i, { reviewed: e.target.checked })}/></td></tr>)}</tbody></table></div><label><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)}/> 我已逐项核对音高、起点、时值及调号</label>{review.has_limitations && <label><input type="checkbox" checked={limitationsAccepted} onChange={e => setLimitationsAccepted(e.target.checked)}/> 我已接受片段范围及未支持符号的限制</label>}</div>}
    <div className="agent-result"><h3>改编参数</h3><div className="agent-form-grid"><label>风格参考<select value={style} onChange={e => { setStyle(e.target.value); arrangeKey.current = null }}><option>洞经音乐</option><option>白沙细乐</option></select></label><label>旋律保留 {preservation}%<input type="range" min="50" max="100" step="5" value={preservation} onChange={e => { setPreservation(Number(e.target.value)); arrangeKey.current = null }}/></label></div><p>选择录音标签（身份待核实）；有限音高采样与辅助音源会在结果中分别列出。</p><div className="agent-options">{assets.map(asset => <label key={asset.asset_id}><input type="checkbox" checked={selected.includes(asset.asset_id)} onChange={e => { setSelected(e.target.checked ? [...selected, asset.asset_id] : selected.filter(id => id !== asset.asset_id)); arrangeKey.current = null }}/>{asset.label}<small>{asset.sample_mapping?.note ?? '仅辅助音源'}</small></label>)}</div><button className="primary" disabled={busy || !selected.length || !recognition || recognition.kind === 'needs_notation' || (recognition.kind !== 'structured' && (!review || !confirmed || (review.has_limitations && !limitationsAccepted)))} onClick={generate}>生成改编 MIDI 与 WAV</button></div>
    {error && <p className="agent-error" role="alert">{error}</p>}
    {result && <div className="agent-result"><h3>已生成作品 · {result.mode === 'qwen_plan' ? 'Qwen AI 规划＋本地合成' : result.mode === 'openai_plan' ? 'OpenAI AI 规划＋本地合成' : '本地规则规划＋本地合成（非 AI 方案）'}</h3>{result.fallback_reason && <p role="alert">{result.fallback_reason}</p>}<p>{result.plan.explanation}</p><p>{result.cultural_status}</p><p>时长 {result.duration_seconds.toFixed(1)} 秒；WAV 包含真实采样与明确标记的辅助音源。</p><audio controls crossOrigin="use-credentials" src={apiUrl(result.wav_url)}/><div className="agent-actions"><a href={apiUrl(result.wav_url)} download>下载 WAV</a><a href={apiUrl(result.midi_url)} download>下载 MIDI</a></div><ul>{result.usage.map(item => <li key={item.label}>{item.label}：采样音符 {item.sample_notes}，辅助音源 {item.auxiliary_notes}，录音片段 {item.phrases}</li>)}</ul></div>}
  </div>
}
