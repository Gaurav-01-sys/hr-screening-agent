import axios from "axios"
import type {
  ExtractPayload,
  ChatRequest,
  ChatResponse,
  HealthResponse,
  ParseDocumentResponse,
  ScreeningRequest,
  ScreeningResponse,
} from "../types"

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

const api = axios.create({ baseURL: API_URL })

export async function parseDocument(file: File): Promise<ParseDocumentResponse> {
  const formData = new FormData()
  formData.append("file", file)
  const response = await api.post<ParseDocumentResponse>("/parse-document", formData)
  return response.data
}

export async function extractScreening(payload: ExtractPayload): Promise<ScreeningRequest> {
  const response = await api.post<ScreeningRequest>("/extract", payload)
  return response.data
}

export async function screenCandidate(payload: ScreeningRequest): Promise<ScreeningResponse> {
  const response = await api.post<ScreeningResponse>("/screen", payload)
  return response.data
}

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/chat", payload)
  return response.data
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health")
  return response.data
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<{ detail?: string; error?: string }>(error)) {
    return error.response?.data?.detail || error.response?.data?.error || error.message || fallback
  }
  return error instanceof Error ? error.message : fallback
}
