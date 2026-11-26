import unittest
import os
import tempfile

from src.utils import read_csv_file, split_values


class TestReadCSVFile(unittest.TestCase):

    def test_read_valid_csv(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False,
            newline="", encoding="utf-8"
        ) as file:
            file.write("id,name\n1,Rohan\n2,Ruchitha\n")
            path = file.name

        try:
            result = read_csv_file(path)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Rohan")
        finally:
            os.remove(path)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            read_csv_file("file_that_does_not_exist.csv")

    def test_empty_csv(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False,
            encoding="utf-8"
        ) as file:
            file.write("id,name\n")
            path = file.name

        try:
            self.assertEqual(read_csv_file(path), [])
        finally:
            os.remove(path)


class TestSplitValues(unittest.TestCase):

    def test_split_semicolon_values(self):
        self.assertEqual(
            split_values("A;B;C"),
            ["A", "B", "C"]
        )

    def test_empty_value(self):
        self.assertEqual(split_values(""), [])


if __name__ == "__main__":
    unittest.main()