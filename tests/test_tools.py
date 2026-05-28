from core.tools import detect_and_run

def test_calculator_tool():
    name, context = detect_and_run("What is 15 * 23?")
    assert name == "calculator"
    assert "345" in context

def test_calculator_tool_complex():
    name, context = detect_and_run("calculate 2 + 3 * 4")
    assert name == "calculator"
    assert "14" in context

def test_datetime_tool():
    name, context = detect_and_run("What time is it right now?")
    assert name == "datetime"
    assert "UTC" in context

def test_no_tool():
    name, context = detect_and_run("Hello, how are you?")
    assert name is None
    assert context == ""
