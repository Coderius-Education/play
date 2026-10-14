# play — Python-bibliotheek (geen docs-repo)

De schrijfstijl en didactiek uit `../CLAUDE.md` gelden **niet** voor deze repo. Dit is een Python-package (`pyproject.toml`, `setup.py`, `tests/`), niet een Docusaurus-leersite.

## Conventies

- Volg de bestaande package layout (`play/`, `tests/`).
- Pytest voor tests.
- Geen Nederlandse leerlinginstructies, geen PRIMM, geen `<details>`-blokken.
- Wijzigingen die de publieke API raken stralen uit naar `../play-docs/`: noem dat in de PR-beschrijving en update beide repos in dezelfde wijzigingsronde.

## Commentaar

Reviewers keuren te veel commentaar af. Uitgangspunt: **voeg geen commentaar toe.**

- **Geen inline commentaar in `play/`** dat uitlegt wat de code doet, waarom een fix nodig was, of welke bug het oplost. Dat hoort in het commitbericht en de PR-beschrijving. Voorbeelden die zijn afgekeurd: `if self.alive():  # a removed sprite's body has already left the space`, `return  # removed: nothing to simulate any more`, en een tweeregelige uitleg boven een `if` over een pymunk-beperking.
- **Maak de code duidelijk in plaats van haar uit te leggen**: een betere naam, een kleine helper met een docstring van één regel, of een duidelijke foutmelding.
- **Docstrings**: één regel voor private helpers (`_naam`). Publieke API volgt de bestaande stijl met `:param:`/`:return:`; geen extra alinea's.
- **Toegestaan**: `# pylint: disable=...`, `# noqa` en `# pragma: no cover` waar nodig. Bestaand commentaar laat je staan, tenzij je de code eromheen herschrijft.
- **Tests**: de testnaam beschrijft het gedrag. Hooguit één regel commentaar als het scenario niet uit de naam en de code blijkt.
- **Controleer vóór elke commit** de toegevoegde regels met `git diff | grep '^+.*#'` en haal weg wat niet aan deze regels voldoet.
