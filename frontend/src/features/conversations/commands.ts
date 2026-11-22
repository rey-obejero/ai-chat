/**
 * The command registry (WI-10) — local prompt templates, not server features.
 *
 * A command's "invocation" is its template inserted into the draft: the palette
 * has nothing to call, so it never sends a message. `kind` separates today's
 * prompts from the skills WI-14 will register into the same list, so the
 * palette needs no second shape when they arrive.
 */
export type CommandKind = 'prompt' | 'skill'

export interface Command {
  id: string
  kind: CommandKind
  /** The name shown in the palette, leading slash included. */
  label: string
  description: string
  /** The text inserted in place of the `/filter` the user typed. */
  template: string
}

export const COMMANDS: Command[] = [
  {
    id: 'explain',
    kind: 'prompt',
    label: '/explain',
    description: 'Explain a topic in simple terms',
    template: 'Explain the following in simple terms:\n\n',
  },
  {
    id: 'summarize',
    kind: 'prompt',
    label: '/summarize',
    description: 'Summarize text down to its key points',
    template: 'Summarize the following, keeping the key points:\n\n',
  },
  {
    id: 'rewrite',
    kind: 'prompt',
    label: '/rewrite',
    description: 'Rewrite text more clearly',
    template: 'Rewrite the following more clearly:\n\n',
  },
  {
    id: 'translate',
    kind: 'prompt',
    label: '/translate',
    description: 'Translate text into English',
    template: 'Translate the following into English:\n\n',
  },
]

/**
 * The filter after a leading slash, or null when the draft is not invoking a
 * command. The filter stops at the first whitespace, so `/trans hello` filters
 * on `trans` and leaves ` hello` as draft text; a slash anywhere else — the
 * `/api/v1` in ordinary prose — is not an invocation.
 */
export function commandQuery(draft: string): string | null {
  const match = /^\/([^\s]*)/.exec(draft)
  return match === null ? null : match[1]
}

/** The commands matching `query`, case-insensitively, over id and label. */
export function filterCommands(query: string): Command[] {
  const term = query.trim().toLowerCase()

  if (term.length === 0) {
    return [...COMMANDS]
  }

  return COMMANDS.filter(
    (command) =>
      command.id.toLowerCase().includes(term) || command.label.toLowerCase().includes(term),
  )
}

/**
 * Replace the leading `/filter` with the command's template, keeping whatever
 * followed the filter. The remainder loses the whitespace that separated it
 * from the filter — every template already ends in its own separator — so
 * `/trans hello` becomes the template followed by `hello`.
 */
export function applyCommand(draft: string, command: Command): string {
  const query = commandQuery(draft)

  if (query === null) {
    return command.template
  }

  const rest = draft.slice(query.length + 1).trimStart()
  return rest.length === 0 ? command.template : `${command.template}${rest}`
}

/** The DOM id of a command's row, shared by the listbox and `aria-activedescendant`. */
export function commandOptionId(command: Command): string {
  return `command-${command.id}`
}
