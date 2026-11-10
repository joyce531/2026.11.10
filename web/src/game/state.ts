export const FLOW = ['opening','dongba_book','dongba_quiz','dongba_complete','clear_story','music_intro','music_book','music_quiz','music_complete','dance_intro','dance_book','dance_learning','dance_complete','dance_transition','end'] as const
export type StepId = typeof FLOW[number]
export type AnswerStatus = 'pending' | 'done' | 'skipped'
export type Feedback = { correct: boolean; answerIndex: number; chosenIndex: number; explanation: string; skipped: boolean }
export type QuizState = { status: Record<string, AnswerStatus>; wrongCounts: Record<string, number>; queue: number[]; pos: number; round: number; feedback: Feedback | null }
export type Progress = { version: 1; userId: string; currentStep: StepId; dialogueIndex: number; bookIndex: number; completedSteps: string[]; skippedSteps: string[]; quiz: QuizState | null; miniGames: Record<string, unknown>; agentUses: { kind: string; at: string; source: string }[]; works: { id: string; kind: string; createdAt: string }[]; lastPlayedAt: string }
const KEY = 'naxi-ai-studio:guest-save:v1'
export const DEFAULT_PROGRESS: Progress = { version: 1, userId: 'guest-local', currentStep: 'opening', dialogueIndex: 0, bookIndex: 0, completedSteps: [], skippedSteps: [], quiz: null, miniGames: {}, agentUses: [], works: [], lastPlayedAt: '' }
export function loadProgress(): Progress {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) || 'null') as Partial<Progress> | null
    if (parsed?.version !== 1 || !FLOW.includes(parsed.currentStep as StepId)) return { ...DEFAULT_PROGRESS }
    return { ...DEFAULT_PROGRESS, ...parsed, completedSteps: parsed.completedSteps ?? [], skippedSteps: parsed.skippedSteps ?? [] }
  } catch { return { ...DEFAULT_PROGRESS } }
}
export function saveProgress(progress: Progress): boolean { try { localStorage.setItem(KEY, JSON.stringify({ ...progress, lastPlayedAt: new Date().toISOString() })); return true } catch { return false } }
export function startQuiz(ids: string[]): QuizState { return { status: Object.fromEntries(ids.map(id => [id, 'pending'])), wrongCounts: {}, queue: ids.map((_, i) => i), pos: 0, round: 1, feedback: null } }
export function answerQuiz(quiz: QuizState, id: string, answerIndex: number, chosenIndex: number, explanation: string): QuizState {
  if (quiz.feedback || quiz.status[id] !== 'pending') return quiz
  const correct = chosenIndex === answerIndex
  const wrongCounts = { ...quiz.wrongCounts, [id]: (quiz.wrongCounts[id] ?? 0) + (correct ? 0 : 1) }
  const skipped = !correct && wrongCounts[id] >= 3
  const status = { ...quiz.status, [id]: correct ? 'done' : skipped ? 'skipped' : 'pending' } as Record<string, AnswerStatus>
  return { ...quiz, status, wrongCounts, feedback: { correct, answerIndex, chosenIndex, explanation, skipped } }
}
export function nextQuestion(quiz: QuizState): { quiz: QuizState; finished: boolean } {
  if (!quiz.feedback) return { quiz, finished: false }
  if (quiz.pos + 1 < quiz.queue.length) return { quiz: { ...quiz, pos: quiz.pos + 1, feedback: null }, finished: false }
  const pending = Object.entries(quiz.status).flatMap(([, state], index) => state === 'pending' ? [index] : [])
  if (!pending.length) return { quiz: { ...quiz, feedback: null }, finished: true }
  return { quiz: { ...quiz, queue: pending, pos: 0, round: quiz.round + 1, feedback: null }, finished: false }
}
