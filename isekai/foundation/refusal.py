"""The one refusal exception, in a module that imports nothing.

`Refusal` says the work cannot be done and that saying so is the correct output
-- never a zero, never a best-effort parse. It lives in the lowest layer so the
pipeline and the evaluator raise one class rather than two of one name.
"""


class Refusal(Exception):
    """The work cannot be done, and saying so is the correct output."""
