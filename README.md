...
# Iceberg
# Projekt: Keylogger – Narzędzie do Monitorowania Aktywności Klawiatury

## Opis projektu
Projekt keyloggera polega na stworzeniu oprogramowania, które umożliwia monitorowanie i rejestrowanie aktywności użytkownika na klawiaturze komputera. Keylogger, będący narzędziem klasy monitorującej, działa w tle systemu operacyjnego, zapisując wszystkie naciśnięcia klawiszy, co pozwala na analizę działań użytkownika w czasie rzeczywistym lub po zakończeniu sesji.

## Główne cele projektu
1. **Rejestrowanie aktywności klawiatury**: Zbieranie informacji o każdym naciśniętym klawiszu oraz odpowiednie ich zapisywanie w formie dziennika (logu).
2. **Praca w tle**: Program działa niezauważalnie dla użytkownika, bez wpływu na wydajność systemu.
3. **Bezpieczne przechowywanie danych**: Zapisane dane są chronione przed nieautoryzowanym dostępem, a logi mogą być szyfrowane.
4. **Obsługa różnych układów klawiatury**: Program dostosowuje się do różnych języków i układów klawiatury.

## Główne funkcje
- Rejestrowanie naciśnięć klawiszy (w tym kombinacji klawiszy, np. Ctrl + C).
- Możliwość wykluczenia z monitorowania określonych aplikacji lub stron internetowych.
- Okresowe przesyłanie zapisów do wybranej lokalizacji (np. serwera zdalnego lub chmury).
- Zabezpieczenie logów za pomocą szyfrowania oraz hasła.
- Możliwość uruchomienia programu podczas startu systemu.

## Technologie użyte w projekcie
- **Język programowania**: Python
- **Interfejs użytkownika**: Brak interfejsu (niewidoczna praca w tle) lub minimalistyczny panel do konfiguracji dla administratora.
