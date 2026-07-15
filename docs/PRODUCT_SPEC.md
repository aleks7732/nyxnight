# NyxNight product contract

NyxNight is a responsive local night-out planner.

## Generated product

The application accepts city, date, party size, per-person budget, vibe, and start/end times. It returns a deterministic three-stop itinerary whose first and last times match the requested window and whose total never exceeds the supplied budget. Stop names are honest route roles rather than invented venues. Each stop includes a typed HTTPS action that hands the user to a current external search; NyxNight itself performs no venue lookup.

## Visual contract

- True-black background (`#000000`).
- Crail-orange primary accent (`#C15F3C`).
- No green success treatment.
- Dependency-free browser JavaScript.
- Dynamic content must use text nodes or `textContent`; HTML parsing sinks are forbidden.
- Keyboard focus and reduced-motion handling are required.

## Architectural contract

Google ADK creates and verifies this repository, but the application runtime must not import or depend on `google-adk`. The factory is retained under `factory/` for provenance and reproducibility only.
