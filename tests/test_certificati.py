"""Certificati intermedi per i siti che non li mandano (MIT, ENEA, ISMEA; 09/10/2026)."""

from cryptography import x509

from app.raccolta import scarica


def test_intermedi_validi_e_caricati():
    testo = scarica.INTERMEDI.read_bytes()
    certificati = x509.load_pem_x509_certificates(testo)
    nomi = {c.subject.rfc4514_string() for c in certificati}
    assert any("Sectigo Public Server Authentication CA DV R36" in n for n in nomi)
    assert any("GEANT TLS RSA 1" in n for n in nomi)
    assert all(c.not_valid_after_utc.year >= 2030 for c in certificati)
    ctx = scarica.contesto_ssl()
    assert ctx.cert_store_stats()["x509_ca"] > 100                     # certifi + intermedi
    client = scarica.nuovo_client()
    client.close()
