import { useEffect, useState } from 'react'
import { apiUrl, getJson, type Job } from './api'

type Result = { source?: string; status?: string; overall_feedback?: string; wav_url?: string; midi_url?: string; video_url?: string; mode?: string }

export default function WorksPanel({ refresh }: { refresh: number }) {
  const [works, setWorks] = useState<Job<Result>[]>([])
  const [error, setError] = useState('')
  useEffect(() => { getJson<{ works: Job<Result>[] }>('/api/works').then(value => setWorks(value.works)).catch(e => setError(e.message)) }, [refresh])
  return <section className="agent-result"><h2>我的任务与作品</h2><p>只展示当前账号有权查看的记录；游戏游客存档仍保存在此浏览器。</p>{error && <p role="alert">{error}</p>}
    {works.length === 0 && <p>暂无服务端任务。</p>}
    {works.map(work => <article key={work.task_id} className="work-card"><h3>{work.agent === 'dongba' ? '东巴文评价' : work.agent === 'music_arrange' ? '古乐改编' : work.agent === 'music_recognize' ? '曲谱识别' : '打跳视频'} · {work.status}</h3><p>{new Date(work.submitted_at).toLocaleString('zh-CN')} · {work.model || '本地流程 / 未配置模型'}</p>
      {work.result?.source && <p>评价来源：{work.result.source}{work.result.overall_feedback ? ` · ${work.result.overall_feedback}` : ''}</p>}
      {work.result?.mode && <p>编曲规划：{work.result.mode}</p>}{work.error && <p role="alert">{work.error}</p>}
      {work.result?.wav_url && <><audio controls crossOrigin="use-credentials" src={apiUrl(work.result.wav_url)}/><p><a href={apiUrl(work.result.wav_url)} download>下载 WAV</a>　{work.result.midi_url && <a href={apiUrl(work.result.midi_url)} download>下载 MIDI</a>}</p></>}
      {work.result?.video_url && <><video controls crossOrigin="use-credentials" playsInline src={apiUrl(work.result.video_url)}/><p><a href={apiUrl(work.result.video_url)} download>下载 MP4</a></p></>}
    </article>)}
  </section>
}
