import { act } from 'react'
import { expect, it, vi } from 'vitest'
import music from './game/music_content.json'
import dialogues from './game/dialogues.json'
import videoManifest from './game/music_video_manifest.json'
import { loadProgress } from './game/state'

it('首页进入原版古乐剧情、文化书、五题辨识、通关及 Agent 往返，退出后保存位置', async () => {
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
  await click('.music-spotlight .primary')
  expect(location.pathname).toBe('/game/clear_story')
  for (let i = 0; i < (dialogues.clear_story.filter(x => x.kind === 'dialogue')).length; i++) await click('.music-dialogue .primary')
  expect(location.pathname).toBe('/game/music_intro')
  await click('.music-dialogue .primary')
  expect(loadProgress().dialogueIndex).toBe(1)
  await click('.game-top-actions button', 1)
  expect(location.pathname).toBe('/chapters')
  await click('.music-card .text-button')
  expect(location.pathname).toBe('/game/music_intro')
  expect(loadProgress().dialogueIndex).toBe(1)
  const introCount = dialogues.music_intro.filter(x => x.kind === 'dialogue').length
  await click('.music-dialogue .primary')
  expect(document.querySelector('.music-dialogue audio')?.getAttribute('src')).toContain('stinger_fail_dongjing.ogg')
  await click('.music-dialogue .primary')
  expect(document.querySelector('.music-dialogue audio')?.getAttribute('src')).toContain('stinger_win_baisha.ogg')
  for (let i = 3; i < introCount; i++) await click('.music-dialogue .primary')
  expect(location.pathname).toBe('/game/music_book')
  expect(music.book.spreads).toHaveLength(6)
  for (let i = 0; i < music.book.spreads.length; i++) await click('.book-controls .primary')
  expect(location.pathname).toBe('/game/music_quiz')
  expect(document.querySelector('video')?.getAttribute('src')).toContain('dongjing_01.mp4')
  for (const question of music.quiz.questions) {
    expect(document.querySelector('video')?.getAttribute('src')).toBe(videoManifest.find(item => item.game_path === question.prompt.audio)?.web_path)
    expect(document.querySelector('video')?.hasAttribute('muted')).toBe(false)
    await click('.options button', question.answer_index)
    expect(document.querySelector('.feedback audio')?.getAttribute('src')).toContain('stinger_win_baisha.ogg')
    await click('.feedback button.primary')
  }
  expect(location.pathname).toBe('/game/music_complete')
  const saved = loadProgress()
  expect(saved.completedSteps).toContain('music_complete')
  expect((saved.miniGames.musicQuiz as { status: Record<string,string> }).status.music_q5).toBe('done')
  await click('.completion-actions .primary')
  expect(location.pathname).toBe('/login')
  expect(new URLSearchParams(location.search).get('next')).toContain('/agent/music')
  await click('.topbar nav button', 1)
  expect(location.pathname).toBe('/chapters')
  await click('.music-card .text-button')
  expect(location.pathname).toBe('/game/music_complete')
  await click('.completion-actions .ghost', 1)
  expect(location.pathname).toBe('/chapters')
  await click('.music-card > .text-button:last-child')
  expect(loadProgress().skippedSteps).toContain('music_chapter')
  expect(loadProgress().completedSteps).toContain('music_complete')
  expect(loadProgress().currentStep).toBe('dance_intro')
  await click('.music-card .primary')
  expect(location.pathname).toBe('/game/clear_story')
  await click('.game-top-actions button')
  expect(location.pathname).toBe('/chapters')
  expect(loadProgress().skippedSteps).toContain('music_chapter')
})
