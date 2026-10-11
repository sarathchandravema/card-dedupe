from app import app


def test_index_page_renders_groups():
    resp = app.test_client().get("/")
    assert resp.status_code == 200
    assert b"Same customer, multiple ids" in resp.data
    assert b"Group 1" in resp.data
