import { act } from 'react'
import { expect, it, vi } from 'vitest'
import content from './game/dongba_content.json'

it('首页到东巴通关、Agent、目录与恢复的完整离线路径', async () => {
  localStorage.clear()
  history.replaceState(null, '', '/')
  document.body.innerHTML = '<div id="root"></div>'
  vi.stubGlobal('scrollTo', () => {})
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
  await act(async () => { await import('./main') })
  const click = async (selector: string, index = 0) => {
    const button = document.querySelectorAll<HTMLButtonElement>(selector)[index]
    expect(button, selector).toBeTruthy()
    await act(async () => { button.click() })
  }
  await click('.hero-actions .primary')
  expect(location.pathname).toBe('/game/opening')
  for (let i = 0; i < 17; i++) await click('.dialogue-box .primary')
  expect(location.pathname).toBe('/game/dongba_book')
  for (let i = 0; i < 5; i++) await click('.book-controls .primary')
  expect(location.pathname).toBe('/game/dongba_quiz')
  for (const question of content.quiz.questions) {
    await click('.options button', question.answer_index)
    await click('.feedback button.primary')
  }
  expect(location.pathname).toBe('/game/dongba_complete')
  await click('.completion-actions .primary')
  expect(location.pathname).toBe('/login')
  expect(new URLSearchParams(location.search).get('next')).toContain('/agent/dongba')
  await click('.topbar nav button', 1)
  expect(location.pathname).toBe('/chapters')
  const saved = JSON.parse(localStorage.getItem('naxi-ai-studio:guest-save:v1')!)
  expect(saved.completedSteps).toContain('dongba_quiz')
  expect(saved.currentStep).toBe('dongba_complete')
  await click('.chapter-card.live .text-button')
  expect(location.pathname).toBe('/game/dongba_complete')
})
