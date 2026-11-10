import { newKey, postJson, type Job } from './agents/api'
import { useEffect, useRef, useState } from 'react'

const glyphs = [
  ['dongba_01', '人', 'dongba_01_person.png'],
  ['dongba_02', '山', 'dongba_02_mountain.png'],
  ['dongba_03', '水', 'dongba_03_water.png'],
  ['dongba_04', '火', 'dongba_04_fire.png'],
  ['dongba_05', '太阳', 'dongba_05_sun.png'],
] as const
type Result = { status: string; similarity_score: number; overall_feedback: string; differences: string[]; improvement_suggestions: string[]; source: string; fallback_reason?: string; model?: string | null }

export default function MockDongbaPanel({onEvaluated}:{onEvaluated:(source:string)=>void}) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const drawing = useRef(false)
  const [glyph, setGlyph] = useState<(typeof glyphs)[number]>(glyphs[0])
  const [mode, setMode] = useState<'online_canvas'|'photo_upload'>('online_canvas')
  const [weight, setWeight] = useState(8)
  const [color, setColor] = useState('#193246')
  const [photo, setPhoto] = useState<string>('')
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const requesting = useRef(false)
  const submissionKey = useRef<string | null>(null)
  const reset = () => { const ctx = canvas.current?.getContext('2d'); if (ctx) { ctx.fillStyle = '#ffffff'; ctx.fillRect(0,0,400,400) } setResult(null); submissionKey.current=null }
  useEffect(() => { reset() }, [])
  const point = (e: React.PointerEvent<HTMLCanvasElement>) => { const box = e.currentTarget.getBoundingClientRect(); return { x: (e.clientX-box.left)*400/box.width, y: (e.clientY-box.top)*400/box.height } }
  const start = (e: React.PointerEvent<HTMLCanvasElement>) => { drawing.current = true; e.currentTarget.setPointerCapture(e.pointerId); const ctx = e.currentTarget.getContext('2d')!; const p=point(e); ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(p.x+.01,p.y+.01); ctx.lineWidth=weight; ctx.lineCap='round'; ctx.strokeStyle=color; ctx.stroke() }
  const move = (e: React.PointerEvent<HTMLCanvasElement>) => { if (!drawing.current) return; const ctx=e.currentTarget.getContext('2d')!; const p=point(e); ctx.lineTo(p.x,p.y); ctx.stroke() }
  const upload = async (file?: File) => { setError(''); setResult(null); if (!file) return; if (!['image/png','image/jpeg'].includes(file.type) || file.size > 5*1024*1024) { setError('只支持不超过 5 MB 的 PNG / JPG 图片。'); return } try { const url=URL.createObjectURL(file); const img=new Image(); img.src=url; await img.decode(); const temp=document.createElement('canvas'); temp.width=img.naturalWidth; temp.height=img.naturalHeight; if (temp.width*temp.height > 20_000_000) throw new Error('图片像素过大。'); temp.getContext('2d')!.drawImage(img,0,0); setPhoto(temp.toDataURL('image/png')); URL.revokeObjectURL(url) } catch { setError('图片无法读取，请重新上传清晰照片。') } }
  const evaluate = async () => { if (requesting.current) return; requesting.current=true; setBusy(true); setError(''); setResult(null); try { const image=mode==='online_canvas' ? canvas.current!.toDataURL('image/png') : photo; if (!image) throw new Error('请先上传照片。'); submissionKey.current ||= newKey(); const job=await postJson<Job<Result>>('/api/agents/dongba/evaluate',{character_id:glyph[0],input_method:mode,image},submissionKey.current); if (!job.result || !['qwen_vision','openai_responses','mock','quality_check'].includes(job.result.source)) throw new Error('评价来源未通过校验。'); setResult({...job.result,model:job.model}); onEvaluated(job.result.source); submissionKey.current=null } catch(e) { setError(e instanceof Error ? e.message : '本地接口不可用。请启动 Mock 服务。') } finally { requesting.current=false; setBusy(false) } }
  return <div className="mock-panel"><div className="mock-head"><strong>东巴文 AI 临摹评价</strong><span>点击后优先使用已启用的视觉 AI；本地模式与失败回退会明确标记</span></div><label>选择目标字 <select value={glyph[0]} onChange={e=>{setGlyph(glyphs.find(x=>x[0]===e.target.value)!);setResult(null);submissionKey.current=null}}>{glyphs.map(x=><option key={x[0]} value={x[0]}>{x[1]}</option>)}</select></label><div className="mock-reference"><img src={'/godot/Assets/dongba/glyphs/'+glyph[2]} alt={'目标字：'+glyph[1]}/><span>目标字：{glyph[1]}<br/>示范图来自原游戏与现有字库</span></div><div className="mode-row"><button className={mode==='online_canvas'?'selected':''} onClick={()=>{setMode('online_canvas');submissionKey.current=null}}>在线临摹</button><button className={mode==='photo_upload'?'selected':''} onClick={()=>{setMode('photo_upload');submissionKey.current=null}}>拍照上传</button></div><div className="input-area"><div style={{display:mode==='online_canvas'?'block':'none'}}><div className="canvas-tools"><label>画笔 <input type="range" min="3" max="24" value={weight} onChange={e=>setWeight(Number(e.target.value))}/>{weight}px</label><label>颜色 <input type="color" value={color} onChange={e=>setColor(e.target.value)}/></label><button onClick={reset}>清空画布</button></div><canvas ref={canvas} width="400" height="400" onPointerDown={start} onPointerMove={move} onPointerUp={()=>drawing.current=false} onPointerCancel={()=>drawing.current=false} aria-label="手写画布"/></div>{mode==='photo_upload'&&<><input type="file" accept="image/png,image/jpeg" onChange={e=>upload(e.target.files?.[0])}/>{photo&&<img className="photo-preview" src={photo} alt="上传图片预览"/>}</>}</div><button className="primary" onClick={evaluate} disabled={busy}>{busy?'评价中…':'开始评价'}</button>{error&&<p className="mock-error">{error}</p>}{result&&<div className="mock-result"><strong>来源：{result.source==='mock'?'Mock 本地形态测量':result.source==='quality_check'?'图片质量检查':result.source==='qwen_vision'?'Qwen 视觉 AI':'OpenAI 视觉 AI'} · {result.status}</strong><p>{result.overall_feedback}</p>{result.fallback_reason&&<p>真实 AI 不可用，已回退 Mock：{result.fallback_reason}</p>}{result.model&&<p>模型：{result.model}；相似度为未标定的视觉估计。</p>}{result.source==='mock'&&<p>本地计算相似度：{result.similarity_score}（非 AI 估计或识别准确率）</p>}{(result.source==='qwen_vision'||result.source==='openai_responses')&&<p>视觉相似度估计：{result.similarity_score}（非识别准确率）</p>}<ul>{result.differences.map((d,i)=><li key={i}>{d}</li>)}{result.improvement_suggestions.map((d,i)=><li key={'s'+i}>{d}</li>)}</ul></div>}</div>
}
