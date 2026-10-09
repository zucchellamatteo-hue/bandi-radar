"""Glossario degli articoli (10/10/2026): prima comparsa, niente titoli/link, sezione finale."""

from app.pubblico import glossario


def test_prima_comparsa_e_zone_escluse():
    h, usate = glossario.applica('<h2>APE</h2><p>Serve l\'APE. Di nuovo APE. <a href="/x">DURC</a> e DURC.</p>'
                                 '<table><tr><td>GBER</td></tr></table><p>IRAP e de minimis.</p>')
    assert usate == ["APE", "DURC", "de minimis", "IRAP"]
    assert h.count('class="glossa"') == 4 and "<h2>APE</h2>" in h and '<a href="/x">DURC</a>' in h
    assert "<td>GBER</td>" in h                                   # nelle tabelle no
    assert h.count('href="#g-ape"') == 1                          # solo la prima volta


def test_sezione_finale():
    s = glossario.sezione(["DURC", "de minimis"])
    assert 'id="g-durc"' in s and 'id="g-de-minimis"' in s and "Parole difficili" in s
    assert glossario.sezione([]) == ""
