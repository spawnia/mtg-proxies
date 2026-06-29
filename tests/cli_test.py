from unittest.mock import patch

import pytest


def test_main(capsys: pytest.CaptureFixture) -> None:
    """Test the main function.

    Ensure that ther a are no import errors and that the help message is printed correctly.
    """
    from mtg_proxies.cli import main

    # Mock argv
    with patch("sys.argv", ["mtg-proxies", "--help"]), pytest.raises(SystemExit):
        main()

    # Check output
    captured = capsys.readouterr()
    assert (
        captured.out
        == """usage: mtg-proxies [-h] {print,convert,tokens,deck_value} ...

Create high quality MtG proxies from your decklist.

positional arguments:
  {print,convert,tokens,deck_value}
    print               Prepare a decklist for printing
    convert             Convert a decklist to text or arena format
    tokens              Append the created tokens to a decklist
    deck_value          Show deck value decomposition

options:
  -h, --help            show this help message and exit
"""
    )


def test_print_help_mentions_new_flags(capsys: pytest.CaptureFixture) -> None:
    from mtg_proxies.cli import main

    with patch("sys.argv", ["mtg-proxies", "print", "--help"]), pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert "--bleed" in captured.out
    assert "--gutter" in captured.out


def test_border_crop_and_gutter_mutually_exclusive(capsys: pytest.CaptureFixture) -> None:
    from mtg_proxies.cli import main

    argv = [
        "mtg-proxies",
        "print",
        "/tmp/does-not-exist.txt",
        "/tmp/out.pdf",
        "--border_crop=14",
        "--gutter=5",
    ]
    with patch("sys.argv", argv), pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert "mutually exclusive" in (captured.err + captured.out)
