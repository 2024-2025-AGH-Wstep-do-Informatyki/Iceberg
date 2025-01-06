from pynput import keyboard
from enum import Enum
from dataclasses import dataclass
import os
from datetime import datetime
from typing import Optional

from unicodedata import category

# Ścieżka do katalogu zawierającego aktualny plik
base_directory = os.path.dirname(os.path.abspath(__file__))

# Tworzenie ścieżki do folderu `src/data`
data_directory = os.path.join(base_directory, "..", "data")
file_path = os.path.join(data_directory, "keypress_log.txt")

# Tworzenie katalogu, jeśli go nie ma
os.makedirs(data_directory, exist_ok=True)

#Dziedziczymy Enum, ponieważ jest ona jak szafa, nie możemy pomylić jej nazwy np.:
#Bez Enum: category = "NUMPAD" - można przez przypadek inaczej napisać - błąd
#Z Enum: category = KeyCategory.NUMPAD - Zawsze ta sama nazwa, bez możliwości pomyłki!
class KeyCategory(Enum):
    STANDARD = "STANDARD" # np. Litery, cyfry
    NUMPAD = "NUMPAD"     # klawiatura numeryczna (numpad)
    FUNCTION = "FUNCTION" # klawisze F1-F12
    SPECIAL = "SPECIAL"   # Klawisze specjalne np. Enter, Backspace, Tab, Escape
    MODIFIER = "MODIFIER" # Klawisze modyfikujące (zmieniające działanie innych klawiszy):
    # Shift (zmienia małe litery na wielkie): Ctrl (do skrótów jak Ctrl+C), Alt (podobnie jak Ctrl),
    # Cmd (klawisz Windows/Command na Macu)
    NAVIGATION = "NAVIGATION" # Klawisze do poruszania się (Left, Right, Up, Down, End, Page Up, Page Down)
    UNKNOWN = "UNKNOWN" # Reszta klawiszy, która nie pasuje do żadnej z kategorii powyżej

@dataclass #@dataclass pisze za nas nudny kod, upraszcza tworzenie klas do przechowywania danych
#automatycznie generuje konstruktor i inne metody, pozwala łatwo zarządzać wartościami
#domyślnymi i niezmiennością, zwiększa czytelność i redukuje ilość powielanego kodu
class KeyEvent:
    key: str                    # jaki klawisz
    category: KeyCategory       # kategoria klawisza
    timestamp: datetime         # kiedy naciśnięto
    event_type: str            # press/release
    is_modifier_active: bool = False    # czy Shift/Ctrl/Alt jest wciśnięty
    #Optional mówi Pythonowi, że wartość może być None albo obiektem, nie wiemy dokładnie jakiego typu będzie klawisz z
    #pynput, chcemy być elastyczni i móc przyjąć każdy typ obiektu, każda rzecz jest obiektem
    raw_key: Optional[object] = None   # Surowy klawisz to skomplikowany oryginalny obiekt klawisza z biblioteki pynput
                                    #zawiera techniczne informacje o klawiszu, zachowujemy go na wszelki wypadek, gdybyśmy
                                    #Potrzebowali technicznych szczegółów

class MyException(Exception): pass

#Nie używamy @dataclass, bo korzystamy z niego tylko do przechowywania danych, natomiast nasza klasa działa
#troche jak robot, keyboardeventhandler jest mózgiem całym przechwytywania klawiszy
class KeyboardEventHandler:
    def __init__(self):
        self.modifiers_active = set() #set() jest jak lista, ale każda rzecz może być tylko raz (nie zawiera duplikatów)
                                    # Łatwo sprawdzić co jest w środku, łatwo dodawać i usuwać rzeczy
        self.last_key = None
        self.key_combinations = []

    #funkcje zaczynające się od _ to funkcje wewnętrzne, których nie powinno wywoływać się w zewnętrznym kodzie.
    def _categorize_key(self, key) -> KeyCategory: #metoda zwraca wartość typu KeyCategory
        # hasattr to funkcja, która sprawdza, czy dany obiekt ('key') ma określony atrybut (vk - virtual key code)
        # np. hasattr(key, 'vk') sprawdza czy klawisz ma kod wirtualny

        # Sprawdzamy, czy to klawisz z numpada (kody 96 - 105)
        if hasattr(key, 'vk') and 96 <= key.vk <= 105:
            return KeyCategory.NUMPAD

        # Sprawdzamy, czy to zwykły klawisz (litera, cyfra, znak) - bez numpada!
        # hasattr sprawdza, czy klawisz generuje znak
        elif hasattr(key, 'char') and key.char:
            return KeyCategory.STANDARD

        # Sprawdzamy, czy klawisz ma nazwę (np. F1, Shift, Enter)
        elif hasattr(key, 'name'):
            # Jeśli nazwa zaczyna się na 'f' to klawisz funkcyjny (F1-F12)
            if key.name.startswith('f'):
                return KeyCategory.FUNCTION
            # Jeśli nazwa to jeden z modyfikatorów
            elif key.name in ['shift', 'ctrl','alt','cmd']: #klawisz cmd często możemy znaleźć na klawiaturach MAC
                return KeyCategory.MODIFIER
            # Jeśli nazwa to jeden z klawiszy nawigacyjnych
            elif key.name in ['up', 'down', 'left', 'right', 'home', 'end', 'page_up', 'page_down']:
                return KeyCategory.NAVIGATION
            # Inne klawisze specjalne (Enter, Backspace itp.)
            return KeyCategory.SPECIAL

        # Jeśli nie pasuje do żadnej kategorii
        return KeyCategory.UNKNOWN

    #Funkcja wewnętrzna-nie wykorzystujemy jej w kodzie zewnętrznym
    def _format_key(self, key) -> str:
        try:
            # Dla klawiszy z numpada dodajemy prefix 'NUM_'
            # i odejmujemy 96, by otrzymać właściwą cyfrę (96=0, 97=1 itd.)
            if hasattr(key, 'vk') and 96 <= key.vk <= 105:
                return f"NUM_{key.vk - 96}"

            # Dla zwykłych klawiszy zwracamy ich znak (literę/cyfrę)
            elif hasattr(key, 'char') and key.char:
                return key.char

            # Dla klawiszy z nazwą (F1, Enter itp.) zwracamy nazwę wielkimi literami
            elif hasattr(key, 'name'):
                return key.name.upper()

            # Jeśli żaden warunek nie pasuje, konwertujemy obiekt na tekst
            return str(key)

            # Jeśli wystąpi błąd podczas próby odczytu atrybutów klawisza
        except AttributeError:
            return "UNKNOWN_KEY"

    def _handle_modifier(self, key, is_press: bool):
        # Sprawdzamy, czy klawisz ma atrybut 'name' i czy jest modyfikatorem
        if hasattr(key, 'name') and key.name in ['shift', 'ctrl', 'alt', 'cmd']:
            # Jeśli klawisz jest naciskany
            if is_press:
                # Dodajemy go do zbioru aktywnych modyfikatorów
                # set.add() automatycznie ignoruje duplikaty
                self.modifiers_active.add(key.name)

            # Jeśli klawisz jest puszczany
            else:
                # Usuwamy go ze zbioru aktywnych modyfikatorów
                # discard() bezpiecznie usuwa element (nie wyrzuca błędu, jeśli go nie ma)
                self.modifiers_active.discard(key.name)

    def handle_press(self, key) -> KeyEvent:
        self._handle_modifier(key, True)

        category = self._categorize_key(key)
        formatted_key = self._format_key(key)

        event = KeyEvent(
            key=formatted_key,
            category=category,
            timestamp=datetime.now(),
            event_type="press",
            is_modifier_active=bool(self.modifiers_active),
            raw_key=key
        )

# def log_key(key):
#     try:
#         with open(file_path, "a") as f:
#             f.write(str(key) + "\n")
#     except FileNotFoundError:
#         with open(file_path, "w") as f:
#             f.write(str(key) + "\n")
#
# def on_press(key):
#     try:
#         #hasattr to funkcja, która sprawdza, czy dany obiekt ma określony atrybut (vk - virtual key code)
#         if hasattr(key, 'vk') and 96 <= key.vk <= 105: # Kody klawiszy 96-105 to Numpad (0-9)
#             numpad_key = key.vk - 96 # Obliczamy wartość klawisza Numpad
#             print(f'Numpad key {numpad_key} pressed')
#
#         elif hasattr(key, 'char'):
#             print(f'Key {key.char} pressed')
#         elif hasattr(key, 'name') and key.name.startswith('f'):
#              # Wykrywa klawisze F1-F12
#             print(f'Function key {key.name} pressed')
#         else:
#             print(f'Special key {key.char} pressed')
#     except AttributeError:
#         print(f'special key {key} pressed')
#     log_key(key)
#
# def on_release(key):
#     try:
#         if hasattr(key, 'vk') and 96 <= key.vk <= 105: # kody 96 - 105 to klawiatura numeryczna (numpad) 0-9
#             numpad_key = key.vk - 96
#             print(f'Numpad key {numpad_key} released')
#         else:
#             print('Key {0} released'.format(
#                 key))
#     except AttributeError:
#         print('special key {0} released'.format(
#             key))
#     if key == keyboard.Key.esc:
#         # Stop listener
#         raise MyException(key)
#
# def on_activate_h():
#     print('<ctrl>+<alt>+h pressed')
#
# def on_activate_i():
#     print('<ctrl>+<alt>+i pressed')
#
# def for_canonical(f):
#     return lambda k: f(listener.canonical(k))
#
# #Uruchom nasłuchiwanie skrótów w osobnym wątku
# hotkeys = keyboard.GlobalHotKeys({
#     '<ctrl>+<alt>+h': on_activate_h,
#     '<ctrl>+<alt>+i': on_activate_i})
# hotkeys.start()
#
# #Uruchom nasłuchiwanie zwykłych klawiszy
# # Collect events until released
# with keyboard.Listener(
#         on_press=on_press,
#         on_release=on_release) as listener:
#     try:
#         listener.join()
#     except MyException as e:
#         print('{0} was pressed'.format(e.args[0]))