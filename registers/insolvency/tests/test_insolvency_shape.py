from support.lane import check_folder
import os


def test_the_lane_folder_has_the_shape():
    assert check_folder(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) == []
