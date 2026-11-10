import { expect, it } from 'vitest'
import content from './music_content.json'
import { answerQuiz, nextQuestion, startQuiz } from './state'

it('古乐原题库与三次错答规则均保留，题目可在下一轮重问', () => {
  const questions = content.quiz.questions
  expect(questions).toHaveLength(5)
  expect(content.book.spreads).toHaveLength(6)
  expect(questions.map(q => q.prompt.audio)).toEqual([
    'res://Assets/music/dongjing/dongjing_01.ogv',
    'res://Assets/music/baisha/baisha_01.ogv',
    'res://Assets/music/dongjing/dongjing_02.ogv',
    'res://Assets/music/baisha/baisha_02.ogv',
    'res://Assets/music/dongjing/dongjing_03.ogv',
  ])
  let q = startQuiz(questions.map(item => item.id))
  for (const question of questions) {
    const selected = question.id === 'music_q1' ? 1 : question.answer_index
    q = answerQuiz(q, question.id, question.answer_index, selected, question.explanation)
    q = nextQuestion(q).quiz
  }
  expect(q.round).toBe(2)
  expect(q.queue).toEqual([0])
  for (let i = 0; i < 2; i++) {
    q = answerQuiz(q, 'music_q1', 0, 1, questions[0].explanation)
    const next = nextQuestion(q)
    q = next.quiz
    if (i === 1) expect(next.finished).toBe(true)
  }
  expect(q.status.music_q1).toBe('skipped')
  expect(Object.values(q.status).filter(x => x === 'done')).toHaveLength(4)
})
