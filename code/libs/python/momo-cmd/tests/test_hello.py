"""Hello unit test module."""

from momo_cmd.hello import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello momo-cmd"
