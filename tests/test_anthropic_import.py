def test_anthropic_sdk_importable() -> None:
    import anthropic

    assert hasattr(anthropic, "__version__")
