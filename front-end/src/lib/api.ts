export interface ProblemDetails {
  type: string
  title: string
  status: number
  detail?: string
  instance?: string
  code?: string
  errors?: unknown
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details?: unknown

  constructor(problem: ProblemDetails) {
    super(problem.detail ?? problem.title)
    this.name = 'ApiError'
    this.status = problem.status
    this.code = problem.code ?? 'UNKNOWN'
    this.details = problem.errors
  }
}

/** Parse an RFC 9457 response into an `ApiError`, tolerating non-JSON bodies. */
export async function readProblem(response: Response): Promise<ApiError> {
  let problem: ProblemDetails = {
    type: 'about:blank',
    title: response.statusText,
    status: response.status,
  }
  try {
    problem = (await response.json()) as ProblemDetails
  } catch {
    // Non-JSON error body — fall back to the status line above.
  }
  return new ApiError(problem)
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
  })

  if (!response.ok) {
    throw await readProblem(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
