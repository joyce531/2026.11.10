import { useRef, useState } from 'react'
import content from './music_content.json'
import musicVideoManifest from './music_video_manifest.json'
import dialogues from './dialogues.json'
import { answerQuiz, nextQuestion, startQuiz, type Progress, type StepId } from './state'
import './music.css'

type Event = { kind: string; value: string; speaker?: string }
type Props = {
  step: StepId
  progress: Progress
  update: (next: Progress) => void
  go: (path: string) => void
  advance: (from: StepId, to: StepId) => void
  skip: () => void
}
const musicSteps = ['clear_story', 'music_intro', 'music_book', 'music_quiz', 'music_complete'] as const
export function isMusicStep(step: string): step is typeof musicSteps[number] { return musicSteps.includes(step as typeof musicSteps[number]) }
const asset = (path?: string | null) => path?.startsWith('res://') ? '/godot/' + path.slice(6) : ''
const questions = content.quiz.questions

function dialogueFor(step: 'clear_story' | 'music_intro') {
  return (dialogues[step] as Event[]).filter(e => e.kind === 'dialogue' || e.kind === 'narration')
}
function precedingClip(step: 'clear_story' | 'music_intro', index: number) {
  const events = dialogues[step] as Event[]
  const dialogue = dialogueFor(step)[index]
  const at = events.indexOf(dialogue)
  const previous = index ? events.indexOf(dialogueFor(step)[index - 1]) : -1
  const segment = events.slice(previous + 1, at)
  const clip = [...segment].reverse().find(e => e.kind === 'audio' && e.value.includes('res://Assets/'))
  return clip?.value.match(/res:\/\/Assets\/[^\"]+/)?.[0] ?? ''
}

function Player({ src, video = false, label }: { src: string; video?: boolean; label: string }) {
  const ref = useRef<HTMLMediaElement>(null)
  const [error, setError] = useState(false)
  const url = video ? musicVideoManifest.find(item => item.game_path === src)?.web_path ?? '' : asset(src)
  const replay = () => { if (ref.current) { ref.current.currentTime = 0; void ref.current.play().catch(() => setError(true)) } }
  return <div className="music-player">
    {video ? <video ref={ref as React.RefObject<HTMLVideoElement>} src={url || undefined} controls playsInline preload="metadata" aria-label={label} onError={() => setError(true)} /> : <audio ref={ref as React.RefObject<HTMLAudioElement>} src={url} controls preload="metadata" aria-label={label} onError={() => setError(true)} />}
    <button type="button" onClick={replay} disabled={error}>从头重播 ↺</button>
    {(error || !url) && <p role="alert">当前浏览器无法播放{video ? '由原 OGV 转制的 MP4 视频' : '原 OGG 音频'}。请检查素材和浏览器解码能力；本题不会用其他曲目替代。</p>}
  </div>
}

export default function MusicChapter({ step, progress, update, go, advance, skip }: Props) {
  if (step === 'clear_story' || step === 'music_intro') {
    const lines = dialogueFor(step)
    const index = Math.min(progress.dialogueIndex, lines.length - 1)
    const line = lines[index]
    const clip = precedingClip(step, index)
    const nextStep = step === 'clear_story' ? 'music_intro' : 'music_book'
    return <main className="story music-story" style={{ backgroundImage: `linear-gradient(0deg,rgba(8,18,35,.85),rgba(8,18,35,.12)),url('${asset('res://Assets/vn/backgrounds/bg_in_the_room.png')}')` }}>
      <div className="game-top"><span>第二章 · 纳西古乐 / {step === 'clear_story' ? '剧情过渡' : '剧情导入'}</span><div className="game-top-actions"><button onClick={skip}>跳过本章</button><button onClick={() => go('/chapters')}>退出并保存 ×</button></div></div>
      <img className="portrait left" src={asset('res://Assets/vn/portraits/char_tourist_camera.png')} alt="游客立绘"/>
      <img className="portrait right" src={asset('res://Assets/vn/portraits/char_male_casual.png')} alt="朋友立绘"/>
      <div className="dialogue-box music-dialogue"><small>{line.speaker === 'host' ? '朋友' : '游客'}　{index + 1} / {lines.length}</small><p>{line.value}</p>
        {clip && <><Player key={clip} src={clip} label="原游戏剧情音乐片段"/><small className="source-note">剧情对这段音乐的称呼与原文件名不一致，曲目身份待核实；这里保留原版剧情和原音频。</small></>}
        <button className="primary" onClick={() => index < lines.length - 1 ? update({ ...progress, dialogueIndex: index + 1 }) : advance(step, nextStep)}>{index < lines.length - 1 ? '继续剧情 →' : '翻开古乐文化书 →'}</button>
      </div>
    </main>
  }
  if (step === 'music_book') {
    const spreads = content.book.spreads
    const index = Math.min(progress.bookIndex, spreads.length - 1)
    const spread = spreads[index]
    return <main className="book-stage music-book"><div className="game-top dark-top"><span>第二章 · 纳西古乐 / 文化书</span><div className="game-top-actions"><button onClick={skip}>跳过本章</button><button onClick={() => go('/chapters')}>退出并保存 ×</button></div></div>
      <div className="book-shell"><p className="eyebrow dark">原游戏文化知识 · {index + 1} / {spreads.length}</p><h1>{spread.title}</h1>
        <div className={'book-spread ' + spread.layout}><div className="book-text">{spread.body.split('\n').map((line, i) => <p key={i}>{line || '\u00a0'}</p>)}</div>{spread.illustration && <figure><img src={asset(spread.illustration)} alt={spread.caption || spread.title}/>{spread.caption && <figcaption>{spread.caption}</figcaption>}</figure>}</div>
        {index === spreads.length - 1 && <p className="source-note">原工程没有提供经核实的具体曲牌名称，暂不补写曲牌资料；这里保留原有乐器与两类音乐的对比内容。</p>}
        <div className="book-controls"><button onClick={() => update({ ...progress, bookIndex: Math.max(0, index - 1) })} disabled={index === 0}>← 上一页</button><span>{index + 1} / {spreads.length} · 原工程翻书音效缺失</span><button className="primary" onClick={() => index < spreads.length - 1 ? update({ ...progress, bookIndex: index + 1 }) : advance('music_book', 'music_quiz')}>{index < spreads.length - 1 ? '下一页 →' : content.book.start_button + ' →'}</button></div>
      </div>
    </main>
  }
  if (step === 'music_quiz') {
    const quiz = progress.quiz && 'music_q1' in progress.quiz.status ? progress.quiz : startQuiz(questions.map(q => q.id))
    const q = questions[quiz.queue[quiz.pos]]
    const feedback = quiz.feedback
    const correct = Object.values(quiz.status).filter(v => v === 'done').length
    return <main className="quiz-stage music-quiz"><div className="game-top dark-top"><span>第二章 · 纳西古乐 / 音乐辨识</span><div className="game-top-actions"><button onClick={skip}>跳过本章</button><button onClick={() => go('/chapters')}>退出并保存 ×</button></div></div>
      <div className="quiz-paper"><p className="eyebrow dark">第 {quiz.round} 轮 · 第 {quiz.pos + 1} / {quiz.queue.length} 题 · 已答对 {correct}/{questions.length}</p><h1>{content.quiz.title}</h1><h2>{q.instruction}</h2>
        <div className="question-media"><Player key={q.id} src={q.prompt.audio!} video label={`原游戏音乐辨识题 ${q.id}`}/></div>
        <div className="options">{q.options.map((option, index) => <button key={index} disabled={!!feedback} className={feedback ? index === feedback.answerIndex ? 'correct' : index === feedback.chosenIndex ? 'wrong' : '' : ''} onClick={() => update({ ...progress, quiz: answerQuiz(quiz, q.id, q.answer_index, index, q.explanation) })}><span>{String.fromCharCode(65 + index)}</span>{option.text}</button>)}</div>
        {feedback && <div className={'feedback ' + (feedback.correct ? 'positive' : 'negative')}><strong>{feedback.correct ? '回答正确' : feedback.skipped ? '累计三次答错，本题标记待复习' : '回答不正确，本题会在下一轮重问'}</strong><p>{feedback.explanation}</p><button className="primary" onClick={() => { const next = nextQuestion(quiz); if (next.finished) { update({ ...progress, quiz: next.quiz, miniGames: { ...progress.miniGames, musicQuiz: next.quiz }, completedSteps: [...new Set([...progress.completedSteps, 'music_quiz', 'music_complete'])], currentStep: 'music_complete' }); go('/game/music_complete') } else update({ ...progress, quiz: next.quiz, miniGames: { ...progress.miniGames, musicQuiz: next.quiz } }) }}>继续 →</button><Player src={feedback.correct ? 'res://Assets/music/stingers/stinger_win_baisha.ogg' : 'res://Assets/music/stingers/stinger_fail_dongjing.ogg'} label="原游戏答题反馈音效"/></div>}
      </div>
    </main>
  }
  return <main className="completion" style={{ backgroundImage: `linear-gradient(0deg,rgba(9,23,39,.84),rgba(9,23,39,.34)),url('${asset(content.completion.background)}')` }}><div className="completion-card"><p className="eyebrow">第二章 · 完成</p><h1>{content.completion.title}</h1><p>{content.completion.summary}</p><div className="completion-actions"><button className="primary" onClick={() => { update({ ...progress, completedSteps: [...new Set([...progress.completedSteps, 'music_complete'])], agentUses: [...progress.agentUses, { kind: 'music', at: new Date().toISOString(), source: 'opened_offline' }] }); go('/agent/music?return=game') }}>进入纳西古乐 AI 创作</button><button className="ghost" onClick={() => advance('music_complete', 'dance_intro')}>继续打跳剧情 →</button><button className="ghost" onClick={() => go('/chapters')}>跳过 Agent，返回游戏目录</button></div><small>打跳章节已可独立进入；古乐 Agent 的原 Streamlit 页面可独立使用，本 Web 页面不会调用模型。</small></div></main>
}
