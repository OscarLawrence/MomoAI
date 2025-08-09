"""Tests for backend factory system."""

import pytest
from momo_logger.factory import BackendFactory
from momo_logger.backends.console import ConsoleBackend
from momo_logger.backends.file import FileBackend
from momo_logger.backends.buffer import BufferBackend


def test_backend_factory_creation():
    """Test that backend factory can be created."""
    factory = BackendFactory()
    assert factory is not None


def test_builtin_backends_registered():
    """Test that builtin backends are registered."""
    factory = BackendFactory()

    # Check that builtin backends are registered
    assert "console" in factory._backends
    assert "file" in factory._backends
    assert "buffer" in factory._backends

    # Check that they point to correct classes
    assert factory._backends["console"] == ConsoleBackend
    assert factory._backends["file"] == FileBackend
    assert factory._backends["buffer"] == BufferBackend


def test_create_backend_by_name():
    """Test creating backends by name."""
    factory = BackendFactory()

    # Create console backend
    console_backend = factory.create_backend("console")
    assert isinstance(console_backend, ConsoleBackend)

    # Create file backend
    file_backend = factory.create_backend("file")
    assert isinstance(file_backend, FileBackend)

    # Create buffer backend
    buffer_backend = factory.create_backend("buffer")
    assert isinstance(buffer_backend, BufferBackend)


def test_create_backend_with_instance():
    """Test that existing backend instances are returned as-is."""
    factory = BackendFactory()

    # Create a backend instance
    existing_backend = ConsoleBackend()

    # Factory should return the same instance
    returned_backend = factory.create_backend(existing_backend)
    assert returned_backend is existing_backend


def test_create_unknown_backend():
    """Test that creating unknown backend raises ValueError."""
    factory = BackendFactory()

    with pytest.raises(ValueError, match="Unknown backend"):
        factory.create_backend("unknown_backend")


def test_register_new_backend():
    """Test registering a new backend."""
    factory = BackendFactory()

    # Create a mock backend class
    class MockBackend:
        pass

    # Register the backend
    factory.register_backend("mock", MockBackend)

    # Verify it's registered
    assert "mock" in factory._backends
    assert factory._backends["mock"] == MockBackend

    # Create instance
    mock_backend = factory.create_backend("mock")
    assert isinstance(mock_backend, MockBackend)
