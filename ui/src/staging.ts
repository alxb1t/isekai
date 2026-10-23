/* An import's staging folder, and when the sheet discards it. A closed sheet
   cancels its folder once no commit is moving it: at closing, or when a commit
   in flight then is refused. */

/** Whether the sheet cancels `staging` now. e.g. ('s1', true, true, false) -> false */
export function discards(
  staging: string | null,
  closed: boolean,
  committing: boolean,
  committed: boolean,
): boolean {
  return staging !== null && closed && !committing && !committed
}
