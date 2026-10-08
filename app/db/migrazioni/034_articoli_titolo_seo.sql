-- Titolo breve per Google (09/10/2026, valutazione SEO/GEO): il <title> degli articoli deve stare in circa 60 caratteri,
-- ma i titoli veri sono spesso piu' lunghi (l'iperammortamento ne ha 112). Campo facoltativo: se e' vuoto la pagina usa il
-- titolo accorciato da solo alla parola (app/pubblico/seo.titolo_breve); il titolo intero resta nell'<h1>.
ALTER TABLE articoli ADD COLUMN IF NOT EXISTS titolo_seo text;

-- L'unico articolo pubblicato oggi riceve subito un titolo breve scritto a mano (si cambia dalla pagina Blog).
UPDATE articoli SET titolo_seo = 'Iperammortamento 2026: risparmio, software e IRAP'
WHERE slug = 'iperammortamento-2026-guida-completa' AND titolo_seo IS NULL;
