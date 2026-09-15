"""The one refusal exception, in a module that imports nothing.

`Refusal` says the work cannot be done and that saying so is the correct output
-- never a zero, never a best-effort parse. It started in `isekai.evaluate`
because the scorer was the first thing that needed it, and it lives here now
because the pipeline needs it too: importing the evaluator from a pipeline
command would load several hundred lines of scoring rules to reach one exception
class, and declaring a second class under the same name is exactly the collision
the shared manifest module exists to prevent (design.md, *Risks / Trade-offs*).

It is a pure move. `isekai.evaluate` re-exports it, so both existing importers
keep resolving and no behaviour changes.
"""


class Refusal(Exception):
    """The work cannot be done, and saying so is the correct output."""
