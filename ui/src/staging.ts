/* An import's staging folder, and when closing the sheet discards it. A folder a
   commit is moving is never cancelled: if that commit fails, the sweep takes it. */

/** Whether closing the sheet cancels `staging`. e.g. ('s1', true, false) -> false */
export function discards(staging: string | null, committing: boolean, committed: boolean): staging is string {
  return staging !== null && !committing && !committed
}
