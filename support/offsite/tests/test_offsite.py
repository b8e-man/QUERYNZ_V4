"""What the copy and the rehearsal share: the credential file is read, not
printed, and an upload retries before it gives up; all with fakes."""
import os

import pytest

import support.offsite as off


class FakeClient:
    def __init__(self, fail_first=0):
        self.uploads, self.fail_first = [], fail_first

    def upload_file(self, path, bucket, key):
        if self.fail_first:
            self.fail_first -= 1
            raise ConnectionError("blip")
        self.uploads.append((bucket, key, os.path.getsize(path)))


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / "offsite.env"
    p.write_text("# a comment\nOFFSITE_BUCKET=bkt\nOFFSITE_KEY_ID='AKIA'\nOFFSITE_PASSPHRASE=\"secret-pass\"\n")
    return str(p)


def test_the_credential_file_is_read_with_quotes_stripped(env_file):
    env = off.read_env(env_file)
    assert env == {"OFFSITE_BUCKET": "bkt", "OFFSITE_KEY_ID": "AKIA", "OFFSITE_PASSPHRASE": "secret-pass"}


def test_upload_retries_then_succeeds(tmp_path, env_file):
    sleeps = []
    client = FakeClient(fail_first=2)
    off.upload(client, "bkt", "k", env_file, attempts=5, sleep=sleeps.append)
    assert len(client.uploads) == 1 and sleeps == [5, 10]
    with pytest.raises(RuntimeError) as err:
        off.upload(FakeClient(fail_first=9), "bkt", "k", env_file, attempts=3, sleep=lambda s: None)
    assert "secret" not in str(err.value) and "ConnectionError" in str(err.value)
