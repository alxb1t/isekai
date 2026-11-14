/* The words of the confirmation dialog: its title, and the name it shows under it. */

export interface Confirmation {
  title: string
  name: string | null
}

/** The question asked before a render is deleted; it names nothing under its title. */
export const deletion: Confirmation = { title: 'Delete this render?', name: null }

/** Return `run` with `told` called once it succeeds, so the word does not travel through the
    dialog that asked: one dismissed while `run` is pending is gone when `run` settles. A refusal
    tells nothing and is thrown on. */
export function reporting<T>(run: () => Promise<T>, told: () => void): () => Promise<T> {
  return async () => {
    const done = await run()
    told()
    return done
  }
}

/** Return the question asked before the tattoo `name` is removed.
    e.g. "bow" -> { title: "Remove this tattoo?", name: "bow" } */
export function removal(name: string): Confirmation {
  return { title: 'Remove this tattoo?', name }
}
