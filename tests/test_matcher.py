from dedupe.evaluate import evaluate
from dedupe.generate_data import generate
from dedupe.matcher import MatchConfig, compare, find_duplicates, name_similarity
from dedupe.models import Record
from dedupe.normalize import normalize_email, normalize_mobile


def rec(i, name, mobile="", email="", ip="", atm=""):
    return Record(str(i).zfill(16), name, atm, mobile, email, ip)


def test_name_variants_are_similar():
    assert name_similarity("Jonn Smith", "Jon Smith") >= 0.9
    assert name_similarity("Smith, John", "John Smith") == 1.0
    assert name_similarity("John Smith", "Alice Walker") < 0.7


def test_mobile_and_email_normalisation():
    assert normalize_mobile("+91 98765 43210") == normalize_mobile("09876543210")
    assert normalize_email("J.Smith+x@gmail.com") == "jsmith@gmail.com"


def test_three_fields_match():
    a = rec(1, "Jon Smith", "9876543210", "js@mail.com", "1.1.1.1", "ATM-A1")
    b = rec(2, "Jonn Smith", "+919876543210", "js@mail.com", "2.2.2.2", "ATM-B2")
    assert compare(a, b).is_match  # name + mobile + email


def test_two_fields_not_enough():
    a = rec(1, "Jon Smith", "9876543210", "a@mail.com")
    b = rec(2, "Jon Smith", "9876543210", "b@mail.com")
    assert not compare(a, b).is_match  # name + mobile only


def test_three_weak_fields_not_enough():
    a = rec(1, "Jon Smith", "9876543210", "a@mail.com", "1.1.1.1", "ATM-A1")
    b = rec(2, "Jon Smith", "9111111111", "b@mail.com", "1.1.1.1", "ATM-A1")
    assert not compare(a, b).is_match  # name + ip + atm = 3.5 < 4.5


def test_transitive_grouping():
    # a-b share name+mobile+email; b-c share name+mobile+ip; a-c share only name+mobile.
    a = rec(1, "Jon Smith", "9876543210", "a@mail.com")
    b = rec(2, "Jonn Smith", "9876543210", "a@mail.com", "1.1.1.1")
    c = rec(3, "John Smith", "9876543210", "c@mail.com", "1.1.1.1")
    assert not compare(a, c).is_match
    clusters = find_duplicates([a, b, c], MatchConfig())
    assert len(clusters) == 1 and len(clusters[0].records) == 3


def test_sample_data_accuracy():
    records, truth = generate()
    assert len(records) == 52  # 30 in duplicate groups + 2 look-alikes + 20 singles
    assert all(len(r.id) == 16 and r.id.isdigit() for r in records)
    metrics = evaluate(find_duplicates(records), dict(truth))
    assert metrics["precision"] == 1.0
    assert metrics["recall"] >= 0.9
