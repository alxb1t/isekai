import { test } from 'vitest'

/* `tests/test_spec_bindings.py` reads the keys out of `spec("…")` or
   `spec(["…", …])`, so each must be a string literal on the call, as a pytest
   marker's argument is. */

/** Declare a vitest test bound to one or more scenario keys, named by them joined. */
export function spec(keys: string | readonly string[], fn: () => void | Promise<void>): void {
  test(typeof keys === 'string' ? keys : keys.join(', '), fn)
}
