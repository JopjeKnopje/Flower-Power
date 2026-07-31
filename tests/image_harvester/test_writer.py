import pathlib
import tempfile

from pathlib import Path


from image_harvester.harvester import (
    recording_path_file_name,
    recording_path_find_part_id,
)


def generate_file_range(p: Path, camid: int) -> None:
    for i in range(0, 10):
        s = recording_path_file_name(camid, i)
        p.joinpath(pathlib.Path(s)).touch()


def test_find_new_path_part() -> None:
    tmp_dir = Path(tempfile.TemporaryDirectory(delete=False).name)

    file_count_parts = [3, 0, 12]

    for i in range(0, len(file_count_parts)):
        # generate some test files.
        for j in range(0, file_count_parts[i]):
            s = recording_path_file_name(i, j)
            tmp_dir.joinpath(Path(s)).touch()

    tmp_dir.joinpath(Path("random-file-that-should-not-be-listed")).touch()

    part_max = recording_path_find_part_id(tmp_dir)
    assert part_max is max(file_count_parts)


def test_find_new_path_part_no_files() -> None:
    tmp_dir = Path(tempfile.TemporaryDirectory(delete=False).name)

    tmp_dir.joinpath(Path("random-file-that-should-not-be-listed")).touch()

    part_max = recording_path_find_part_id(tmp_dir)
    assert part_max == 0


class StaticCounter:
    score: int = 0

    def __init__(self) -> None:
        # instance
        StaticCounter.score = 10

    @classmethod
    def count(cls) -> None:
        cls.score += 1

    def get_score(self) -> int:
        return self.score


def test_static_counter() -> None:
    c = StaticCounter()

    assert c.score == 10
    c.count()
    c.count()
    assert c.score == 12
    assert c.get_score() == 12
