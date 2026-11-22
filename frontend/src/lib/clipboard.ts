/** Write text to the clipboard, resolving `false` when no copy path succeeded. */
export async function copyToClipboard(text: string): Promise<boolean> {
  // Prefer the async Clipboard API; it is unavailable on any non-secure origin,
  // including the containerized e2e stack's `http://caddy`, so fall back to the
  // legacy `execCommand` path when the write cannot be attempted or fails.
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // Fall through to the legacy path.
    }
  }

  const area = document.createElement('textarea')
  area.value = text
  area.setAttribute('readonly', '')
  area.style.position = 'fixed'
  area.style.opacity = '0'
  document.body.appendChild(area)
  area.select()
  const copied = document.execCommand('copy')
  document.body.removeChild(area)
  return copied
}
