from pathlib import Path


class SQLUnitCLI:
    def __init__(self):
        pass

    def test(self, input_path: Path):
        pass


def main():
    from fire import Fire

    Fire(SQLUnitCLI)
