"""Tests for local-site environment-file quoting."""

import unittest

from configure_local_site import SECRET_KEY, get_env_value, quote_env_value


class EnvValueQuotingTests(unittest.TestCase):
    def test_quoted_values_round_trip_without_interpolation(self) -> None:
        values = (
            "secret$c-${UNSET}",
            "site's name",
            "backslash\\value",
            "backslash\\' and trailing slash\\",
        )

        for value in values:
            with self.subTest(value=value):
                line = f"{SECRET_KEY}={quote_env_value(value)}"
                self.assertEqual(get_env_value([line], SECRET_KEY), (0, value))

    def test_unquoted_existing_secret_can_be_preserved_and_quoted(self) -> None:
        existing = "legacy$c-secret"
        parsed = get_env_value([f"{SECRET_KEY}={existing}"], SECRET_KEY)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed[1], existing)
        self.assertEqual(
            get_env_value(
                [f"{SECRET_KEY}={quote_env_value(parsed[1])}"], SECRET_KEY
            ),
            (0, existing),
        )


if __name__ == "__main__":
    unittest.main()
