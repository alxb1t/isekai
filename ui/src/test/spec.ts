import { test } from 'vitest'

/* `tests/test_spec_bindings.py` reads the key out of `spec("…")`, so it must be
   one string literal on the call, as a pytest marker's argument is. */

/** Declare a vitest test bound to one scenario key, named by that key. */
export function spec(key: string, fn: () => void | Promise<void>): void {
  test(key, fn)
}
