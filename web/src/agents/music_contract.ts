/** Future Web/Python boundary only. No network request is implemented in Milestone 6C. */
export type ScoreFormat = 'midi' | 'musicxml' | 'mxl' | 'printed_image'
export type ReviewStatus = 'confirmed' | 'needs_review' | 'unreadable'

export interface ScoreUpload {
  file: File
  declaredFormat: ScoreFormat
}
export interface RecognizedNote {
  id: string
  pitch: number | null
  startBeat: number | null
  durationBeats: number | null
  isRest: boolean | null
  confidence: number | null
  reviewStatus: ReviewStatus
}
export interface ParsedScore {
  scoreId: string
  source: 'local_parser' | 'vision_ai'
  keySignature: string | null
  meter: string | null
  tempoBpm: number | null
  notes: RecognizedNote[]
  warnings: string[]
}
export interface ConfirmedScore {
  scoreId: string
  reviewedNotes: RecognizedNote[]
  confirmedByUser: true
}
export interface ArrangementRequest {
  scoreId: string
  instrumentIds: string[]
  referenceCategory: 'dongjing' | 'baisha'
  melodyRetention: number
}
export interface ArrangementArtifact {
  taskId: string
  planningSource: 'model' | 'local_rules'
  midiUrl: string | null
  wavUrl: string | null
  synthesisSources: string[]
  status: 'pending' | 'completed' | 'failed'
}
