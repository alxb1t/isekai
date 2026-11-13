"""A request held at the network, and the helper that waits for the page to send it."""

from playwright.sync_api import Page, Route


def hold(page: Page, pattern: str, method: str = "PUT") -> list[Route]:
    """Hold each `method` request to `pattern`, appending it to the list returned."""
    held: list[Route] = []

    def take(route: Route) -> None:
        if route.request.method == method:
            held.append(route)
        else:
            route.continue_()

    page.route(pattern, take)
    return held


def sent(page: Page, held: list[Route], nth: int = 0) -> Route:
    """Return the `nth` held request, once the page has sent it."""
    for _ in range(100):
        if len(held) > nth:
            return held[nth]
        page.wait_for_timeout(50)
    raise AssertionError("the held request was never sent")
