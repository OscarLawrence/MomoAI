"""Hello unit test module."""

from momo_workflow.hello import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello momo-workflow"
