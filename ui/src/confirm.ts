/* The words of the confirmation dialog: its title, and the name it shows under it. */

export interface Confirmation {
  title: string
  name: string | null
}

/** The question asked before a render is deleted; it names nothing under its title. */
export const deletion: Confirmation = { title: 'Delete this render?', name: null }

/** Return the question asked before the tattoo `name` is removed.
    e.g. "bow" -> { title: "Remove this tattoo?", name: "bow" } */
export function removal(name: string): Confirmation {
  return { title: 'Remove this tattoo?', name }
}
