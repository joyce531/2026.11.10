export type Job<T = Record<string, unknown>> = { task_id: string; agent: string; submitted_at: string; status: string; model: string | null; result: T | null; error: string | null }

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
export const apiUrl = (path: string) => API_BASE + path
let sessionCsrf = ''

function csrfToken() {
  const value = document.cookie.split('; ').find(part => part.startsWith('naxi_csrf='))
  return value ? decodeURIComponent(value.slice('naxi_csrf='.length)) : ''
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(apiUrl(path), { cache: 'no-store', credentials: 'include' })
  const value = await response.json()
  if (!response.ok) throw new Error(value.error || `请求失败（HTTP ${response.status}）`)
  if (path === '/api/auth/me') sessionCsrf = value.csrf_token || ''
  return value as T
}

export async function postJson<T>(path: string, body: object, key?: string): Promise<T> {
  const csrf = sessionCsrf || csrfToken()
  const response = await fetch(apiUrl(path), { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRF-Token': csrf } : {}), ...(key ? { 'Idempotency-Key': key } : {}) }, body: JSON.stringify(body) })
  const value = await response.json()
  if (!response.ok) throw new Error(value.error || `请求失败（HTTP ${response.status}）`)
  if (path === '/api/auth/login') sessionCsrf = value.csrf_token || ''
  if (path === '/api/auth/logout') sessionCsrf = ''
  return value as T
}

export function readFile(file: File, maxBytes: number): Promise<string> {
  if (file.size > maxBytes || !file.size) return Promise.reject(new Error(`文件须非空且不超过 ${Math.round(maxBytes / 1048576)} MB。`))
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('无法读取上传文件。'))
    reader.onload = () => resolve(String(reader.result))
    reader.readAsDataURL(file)
  })
}

export const newKey = () => crypto.randomUUID()
