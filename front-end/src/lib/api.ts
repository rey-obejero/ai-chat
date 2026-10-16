export interface ProblemDetails {
  type: string
  title: string
  status: number
  detail?: string
  instance?: string
  code?: string
  errors?: unknown
  /**
   * The unverified-allowance extension member (ADR-0039): the request was
   * refused because the account's email is not verified, and verifying it lifts
   * the refusal. The quota problem is the only one that sets it.
   */
  verification_required?: boolean
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details?: unknown
  /** See `ProblemDetails.verification_required` (ADR-0039). */
  readonly verificationRequired: boolean

  constructor(problem: ProblemDetails) {
    super(problem.detail ?? problem.title)
    this.name = 'ApiError'
    this.status = problem.status
    this.code = problem.code ?? 'UNKNOWN'
    this.details = problem.errors
    this.verificationRequired = problem.verification_required === true
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
