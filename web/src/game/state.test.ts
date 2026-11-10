import { beforeEach, describe, expect, it, vi } from 'vitest'
import { answerQuiz, DEFAULT_PROGRESS, loadProgress, nextQuestion, saveProgress, startQuiz } from './state'
import content from './dongba_content.json'
describe('原游戏问答与游客存档', () => {
  beforeEach(() => localStorage.clear())
  it('三次累计答错单独标记 skipped，已答对单独标记 done', () => {
    let q = startQuiz(['a', 'b'])
    q = answerQuiz(q, 'a', 0, 1, '解释')
    q = nextQuestion(q).quiz
    q = answerQuiz(q, 'b', 1, 1, '解释')
    q = nextQuestion(q).quiz
    expect(q.round).toBe(2)
    for (let i = 0; i < 2; i++) { q = answerQuiz(q, 'a', 0, 1, '解释'); q = nextQuestion(q).quiz }
    expect(q.status).toEqual({ a: 'skipped', b: 'done' })
    expect(q.wrongCounts.a).toBe(3)
  })
  it('重载后恢复剧情位置和问答反馈', () => {
    const q = answerQuiz(startQuiz(['a']), 'a', 0, 1, '解释')
    saveProgress({ ...DEFAULT_PROGRESS, currentStep: 'dongba_quiz', dialogueIndex: 7, quiz: q })
    expect(loadProgress().quiz?.feedback?.chosenIndex).toBe(1)
    expect(loadProgress().currentStep).toBe('dongba_quiz')
  })
  it('损坏或未知版本的存档安全回退', () => { localStorage.setItem('naxi-ai-studio:guest-save:v1', '{'); expect(loadProgress().currentStep).toBe('opening') })
  it('浏览器拒绝存档时返回失败状态', () => { const spy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('quota') }); expect(saveProgress(DEFAULT_PROGRESS)).toBe(false); spy.mockRestore() })
  it('原题库 16 题可完整通关且答案来自源数据', () => {
    const questions = content.quiz.questions
    expect(questions).toHaveLength(16)
    expect(content.book.spreads).toHaveLength(5)
    let q = startQuiz(questions.map(item => item.id))
    let finished = false
    for (const question of questions) {
      q = answerQuiz(q, question.id, question.answer_index, question.answer_index, question.explanation)
      const next = nextQuestion(q)
      q = next.quiz
      finished = next.finished
    }
    expect(finished).toBe(true)
    expect(Object.values(q.status).filter(x => x === 'done')).toHaveLength(16)
    expect(Object.values(q.status).filter(x => x === 'skipped')).toHaveLength(0)
  })
})
