# print("Tutaj pojawi się wkrótce kod")
from pynput import keyboard
from enum import Enum
from dataclasses import dataclass
import os
from datetime import datetime
from typing import Optional

# Ścieżka do katalogu zawierającego aktualny plik
base_directory = os.path.dirname(os.path.abspath(__file__))

# Tworzenie ścieżki do folderu `src/data`
data_directory = os.path.join(base_directory, "..", "data")
file_path = os.path.join(data_directory, "keypress_log.txt")

# Tworzenie katalogu, jeśli go nie ma
os.makedirs(data_directory, exist_ok=True)

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


def log_key(key):
    try:
        with open(file_path, "a") as f:
            f.write(str(key) + "\n")
    except FileNotFoundError:
        with open(file_path, "w") as f:
            f.write(str(key) + "\n")

def on_press(key):
    try:
        #hasattr to funkcja, która sprawdza, czy dany obiekt ma określony atrybut (vk - virtual key code)
        if hasattr(key, 'vk') and 96 <= key.vk <= 105: # Kody klawiszy 96-105 to Numpad (0-9)
            numpad_key = key.vk - 96 # Obliczamy wartość klawisza Numpad
            print(f'Numpad key {numpad_key} pressed')

        elif hasattr(key, 'char'):
            print(f'Key {key.char} pressed')
        elif hasattr(key, 'name') and key.name.startswith('f'):
             # Wykrywa klawisze F1-F12
            print(f'Function key {key.name} pressed')
        else:
            print(f'Special key {key.char} pressed')
    except AttributeError:
        print(f'special key {key} pressed')
    log_key(key)

def on_release(key):
    try:
        if hasattr(key, 'vk') and 96 <= key.vk <= 105: # kody 96 - 105 to klawiatura numeryczna (numpad) 0-9
            numpad_key = key.vk - 96
            print(f'Numpad key {numpad_key} released')
        else:
            print('Key {0} released'.format(
                key))
    except AttributeError:
        print('special key {0} released'.format(
            key))
    if key == keyboard.Key.esc:
        # Stop listener
        raise MyException(key)

def on_activate_h():
    print('<ctrl>+<alt>+h pressed')

def on_activate_i():
    print('<ctrl>+<alt>+i pressed')

def for_canonical(f):
    return lambda k: f(listener.canonical(k))

#Uruchom nasłuchiwanie skrótów w osobnym wątku
hotkeys = keyboard.GlobalHotKeys({
    '<ctrl>+<alt>+h': on_activate_h,
    '<ctrl>+<alt>+i': on_activate_i})
hotkeys.start()

#Uruchom nasłuchiwanie zwykłych klawiszy
# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    try:
        listener.join()
    except MyException as e:
        print('{0} was pressed'.format(e.args[0]))