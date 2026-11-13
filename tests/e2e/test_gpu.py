"""The busy-port probe on a real socket, bound to loopback port 0."""

import socket

import pytest

from isekai.boundary import gpu


@pytest.mark.spec("pod-image:session:a-busy-port-is-refused-before-the-session")
def test_answers_is_true_while_something_listens_and_false_once_it_stops() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]

        assert gpu.answers(port) is True

    assert gpu.answers(port) is False
