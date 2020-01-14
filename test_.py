import pytest
import json

import id_extractor
import utils


@pytest.fixture
def temp_folder_and_files():
    import tempfile

    with tempfile.TemporaryDirectory() as tempdirname:
        open(f"{tempdirname}/file1", "w")
        open(f"{tempdirname}/file2", "w")
        open(f"{tempdirname}/file3", "w")

        yield tempdirname


def test_get_file_list_from_folder(temp_folder_and_files):
    folder = temp_folder_and_files
    file_list = utils.get_file_list_from_folder(folder)
    assert len(file_list) == 3
    assert "file1" in file_list
    assert "file2" in file_list
    assert "file3" in file_list


def test_extract_pixiv_art_id_format1():
    info = {
        "url": "http://www.pixiv.net/member_illust.php?mode=medium&illust_id=61230245",
        "time": "2017-02-01 23:06",
    }

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "art"
    assert info_id == 61230245


def test_extract_pixiv_art_id_format2():
    info = {
        "url": "https://www.pixiv.net/en/artworks/77296788",
        "time": "2019-10-14 11:16",
        "drive_id": "1E-zKnukXBVvsPOCDKFBEWI5nKME8OzPr",
    }

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "art"
    assert info_id == 77296788


def test_extract_pixiv_art_id_format1_with_fbclid():
    info = {
        "url": "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=64864399&fbclid=IwAR1GGyuBkLsh454q7bXOj9t77cvpEkL8JVDoUoxT6ySFJp19zg5xJMWL94g",
        "time": "2018-08-25 12:13",
    }

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "art"
    assert info_id == 64864399


def test_extract_pixiv_art_id_format2_with_fbclid():
    info = {
        "url": "https://www.pixiv.net/en/artworks/76963557?fbclid=IwAR0fnjsiiOyx7cq3N3GoV567zIXnfiJbI5RPbiI9iXyg00rIhnh3WjmNOms",
        "time": "2019-09-25 11:44",
    }

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "art"
    assert info_id == 76963557


def test_extract_pixiv_artist_id():
    info = {
        "url": "http://www.pixiv.net/member.php?id=13044818",
        "time": "2017-02-02 11:30",
    }

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "artist"
    assert info_id == 13044818


def test_extract_pixiv_artist_id_with_fbclid():
    info = {
        "url": "https://www.pixiv.net/member.php?id=673438&fbclid=IwAR1VTliqx9EzHFea4dXZ6giVCd7nRNR35Qs--b0tPnb0sad3HmZPB4ie-rE",
        "time": "2018-12-20 15:39",
    }

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "artist"
    assert info_id == 673438


def test_extract_pixiv_other():
    info = {"url": "https://www.pixiv.net/contest/fgo3", "time": "2019-07-28 15:04"}

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "other"
    assert info_id == -1


def test_extract_pixiv_bad_url():
    info = {"url": "apaowievz;xlcnwpoeaijsd"}

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "other"
    assert info_id == -1


def test_extract_pixiv_no_url():
    info = {}

    info_type, info_id = id_extractor.extract_pixiv_id(info)
    assert info_type == "other"
    assert info_id == -1


def test_extract_twitter_art_id():
    info = {
        "url": "https://twitter.com/harimoji/status/863768682274537477",
        "time": "2017-05-16 12:31",
    }

    info_type, info_id = id_extractor.extract_twitter_id(info)
    assert info_type == "art"
    assert info_id == 863768682274537477


def test_extract_twitter_art_id_with_query():
    info = {
        "url": "https://twitter.com/tziro460/status/1183336121045880832?s=09",
        "time": "2019-10-13 14:50",
        "drive_id": "1DQimUCgq9aTCl8rHoiy2VXIPK1xQgqGp",
    }

    info_type, info_id = id_extractor.extract_twitter_id(info)
    assert info_type == "art"
    assert info_id == 1183336121045880832


def test_extract_twitter_art_id_with_selected_image():
    info = {
        "url": "https://twitter.com/kerorira1/status/837980988596592640/photo/1",
        "time": "2018-11-09 09:51",
    }

    info_type, info_id = id_extractor.extract_twitter_id(info)
    assert info_type == "art"
    assert info_id == 837980988596592640


def test_extract_twitter_artist_id():
    info = {"url": "https://twitter.com/_club_3", "time": "2017-02-17 02:22"}

    info_type, info_id = id_extractor.extract_twitter_id(info)
    assert info_type == "artist"
    assert info_id == "_club_3"


def test_extract_twitter_artist_id_with_query():
    info = {
        "url": "https://twitter.com/gridgrid3?protected_redirect=true",
        "time": "2018-12-10 09:47",
    }

    info_type, info_id = id_extractor.extract_twitter_id(info)
    assert info_type == "artist"
    assert info_id == "gridgrid3"
