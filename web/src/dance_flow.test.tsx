import { act } from 'react'
import { expect, it, vi } from 'vitest'
import content from './game/dance_content.json'
import dialogues from './game/dialogues.json'
import videos from './game/dance_video_manifest.json'
import { loadProgress } from './game/state'

it('打跳章节沿用目录、剧情、文化书、视频、排序、通关和 Agent 返回路径', async () => {
  localStorage.clear()
  history.replaceState(null, '', '/chapters')
  document.body.innerHTML = '<div id="root"></div>'
  vi.stubGlobal('scrollTo', () => {})
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true)
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
  await act(async () => { await import('./main') })
  const click = async (selector: string, index = 0) => {
    const button = document.querySelectorAll<HTMLButtonElement>(selector)[index]
    expect(button, selector).toBeTruthy()
    await act(async () => { button.click() })
  }
  await click('.dance-card .primary')
  expect(location.pathname).toBe('/game/dance_intro')
  await click('.dialogue-box .primary')
  expect(loadProgress().dialogueIndex).toBe(1)
  await click('.game-top-actions button', 1)
  expect(location.pathname).toBe('/chapters')
  await click('.dance-card .text-button')
  expect(location.pathname).toBe('/game/dance_intro')
  expect(loadProgress().dialogueIndex).toBe(1)
  const lines = dialogues.dance_intro.filter(e => e.kind === 'dialogue')
  for (let i = 1; i < lines.length; i++) await click('.dialogue-box .primary')
  expect(location.pathname).toBe('/game/dance_book')
  expect(content.book.spreads).toHaveLength(5)
  for (let i = 0; i < content.book.spreads.length; i++) await click('.book-controls .primary')
  expect(location.pathname).toBe('/game/dance_learning')
  expect(document.querySelector('video')?.getAttribute('src')).toBe(videos.find(v => v.game_path === content.dance.full_video)?.web_path)
  expect(document.querySelector('video')?.hasAttribute('muted')).toBe(false)
  const fullVideo = document.querySelector('video')!
  fullVideo.currentTime = 5
  await act(async () => { fullVideo.dispatchEvent(new Event('timeupdate', { bubbles: true })) })
  expect((loadProgress().miniGames.dance as { videoTimes: Record<string,number> }).videoTimes[content.dance.full_video]).toBe(5)
  await click('.dance-shell section .primary')
  for (const step of content.dance.steps) {
    expect(document.body.textContent).toContain(step.title)
    expect(document.querySelector('video')?.getAttribute('src')).toBe(videos.find(v => v.game_path === step.video)?.web_path)
    await click('.dance-shell section > .dance-actions .primary')
  }
  expect(document.body.textContent).toContain('口诀排列小游戏')
  for (let i = 0; i < content.dance.steps.length; i++) {
    const state = loadProgress().miniGames.dance as { order: number[]; arrangeIndex: number }
    const step = content.dance.steps[state.order[state.arrangeIndex]]
    for (const cue of step.actions.map(a => a.cue)) {
      const buttons = [...document.querySelectorAll<HTMLButtonElement>('.cue-pool button')]
      const target = buttons.find(b => b.textContent === cue)
      expect(target).toBeTruthy()
      await act(async () => { target!.click() })
    }
    await click('.cue-card .primary')
    expect(document.querySelector('.dance-feedback.correct')).toBeTruthy()
    await click('.dance-feedback .primary')
  }
  const finished = loadProgress().miniGames.dance as { phase: string; completed: string[] }
  expect(finished.phase).toBe('complete')
  expect(finished.completed).toHaveLength(3)
  expect(finished.completed).toEqual(expect.arrayContaining(['step_01', 'step_02', 'step_03']))
  await click('.dance-finish .primary')
  expect(location.pathname).toBe('/game/dance_complete')
  expect(loadProgress().completedSteps).toContain('dance_learning')
  await click('.completion-actions .primary')
  expect(location.pathname).toBe('/login')
  expect(new URLSearchParams(location.search).get('next')).toContain('/agent/dance')
  await click('.topbar nav button', 1)
  await click('.dance-card .stage-pills button', 4)
  expect(location.pathname).toBe('/game/dance_learning')
  expect((loadProgress().miniGames.dance as { stepIndex: number; phase: string }).stepIndex).toBe(2)
  expect((loadProgress().miniGames.dance as { stepIndex: number; phase: string }).phase).toBe('lesson')
  await click('.dance-actions.bottom button')
  expect((loadProgress().miniGames.dance as { paused: boolean }).paused).toBe(true)
  await click('.dance-actions.bottom button', 1)
  expect(location.pathname).toBe('/chapters')
  await click('.dance-card .text-button')
  expect(location.pathname).toBe('/game/dance_learning')
  expect(document.body.textContent).toContain('已暂停')
  await click('.dance-paused .primary')
  expect((loadProgress().miniGames.dance as { paused: boolean }).paused).toBe(false)
})
