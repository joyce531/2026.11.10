import { expect, it } from 'vitest'
import content from './dance_content.json'
import { newDanceState, nextArrange, skipArrange, startArrange, submitAnswer } from './dance_state'

const steps = content.dance.steps
it('排序使用原游戏口诀、重复口诀可互换，错误次数无阈值', () => {
  let state = startArrange(newDanceState(), steps, () => 0.1)
  const step = steps[state.order[0]]
  expect(state.order).toHaveLength(3)
  state = { ...state, answer: [...step.actions.map(a => a.id)].reverse() }
  state = submitAnswer(state, step)
  expect(state.feedback).toBe('wrong')
  expect(state.wrongCounts[step.id]).toBe(1)
  const ids = step.actions.map(a => a.id)
  const duplicate = step.actions.find((a, i) => step.actions.findIndex(b => b.cue === a.cue) !== i)
  if (duplicate) {
    const first = step.actions.find(a => a.cue === duplicate.cue)!
    const firstAt = ids.indexOf(first.id), secondAt = ids.indexOf(duplicate.id)
    ;[ids[firstAt], ids[secondAt]] = [ids[secondAt], ids[firstAt]]
  }
  state = submitAnswer({ ...state, answer: ids, feedback: null }, step)
  expect(state.feedback).toBe('correct')
  expect(state.completed).toContain(step.id)
  state = nextArrange(state, steps, () => 0.2)
  expect(state.arrangeIndex).toBe(1)
})

it('跳过单一步骤与完成分开记录', () => {
  let state = startArrange(newDanceState(), steps, () => 0.1)
  const skippedId = steps[state.order[0]].id
  state = skipArrange(state, steps, () => 0.3)
  expect(state.skipped).toContain(skippedId)
  expect(state.completed).not.toContain(skippedId)
  expect(state.arrangeIndex).toBe(1)
})
