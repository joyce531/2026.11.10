export type DancePhase = 'overview' | 'lesson' | 'arrange' | 'complete'
export type DanceState = {
  phase: DancePhase
  stepIndex: number
  order: number[]
  arrangeIndex: number
  available: string[]
  answer: string[]
  wrongCounts: Record<string, number>
  completed: string[]
  skipped: string[]
  feedback: 'correct' | 'wrong' | null
  paused: boolean
  videoTimes: Record<string, number>
}
export type DanceStep = { id: string; actions: { id: string; cue: string; input: string }[] }
export const newDanceState = (): DanceState => ({ phase: 'overview', stepIndex: 0, order: [], arrangeIndex: 0, available: [], answer: [], wrongCounts: {}, completed: [], skipped: [], feedback: null, paused: false, videoTimes: {} })
export function shuffle<T>(values: T[], random = Math.random): T[] {
  const copy = [...values]
  for (let i = copy.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [copy[i], copy[j]] = [copy[j], copy[i]] }
  return copy
}
export function startArrange(state: DanceState, steps: DanceStep[], random = Math.random): DanceState {
  const order = shuffle(steps.map((_, index) => index).filter(index => !state.skipped.includes(steps[index].id)), random)
  if (!order.length) return { ...state, phase: 'complete', order: [], answer: [], available: [] }
  return { ...state, phase: 'arrange', order, arrangeIndex: 0, answer: [], available: shuffle(steps[order[0]].actions.map(a => a.id), random), feedback: null }
}
export function submitAnswer(state: DanceState, step: DanceStep): DanceState {
  if (state.feedback === 'correct') return state
  const expected = step.actions.map(a => a.cue)
  const actual = state.answer.map(id => step.actions.find(a => a.id === id)?.cue ?? '')
  const correct = actual.length === expected.length && expected.every((cue, index) => cue === actual[index])
  return correct
    ? { ...state, feedback: 'correct', completed: [...new Set([...state.completed, step.id])] }
    : { ...state, feedback: 'wrong', wrongCounts: { ...state.wrongCounts, [step.id]: (state.wrongCounts[step.id] ?? 0) + 1 } }
}
export function nextArrange(state: DanceState, steps: DanceStep[], random = Math.random): DanceState {
  const index = state.arrangeIndex + 1
  if (index >= state.order.length) return { ...state, phase: 'complete', feedback: null, answer: [], available: [] }
  return { ...state, arrangeIndex: index, available: shuffle(steps[state.order[index]].actions.map(a => a.id), random), answer: [], feedback: null }
}
export function skipArrange(state: DanceState, steps: DanceStep[], random = Math.random): DanceState {
  const id = steps[state.order[state.arrangeIndex]].id
  return nextArrange({ ...state, skipped: [...new Set([...state.skipped, id])] }, steps, random)
}
