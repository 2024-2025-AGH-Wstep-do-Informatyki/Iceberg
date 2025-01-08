import json
from pynput import keyboard
from enum import Enum
from dataclasses import dataclass
import os
from datetime import datetime
from typing import Optional

# Dziedziczymy Enum, ponieważ jest ona jak szafa, nie możemy pomylić jej nazwy np.:
# Bez Enum: category = "NUMPAD" - można przez przypadek inaczej napisać - błąd
# Z Enum: category = KeyCategory.NUMPAD - Zawsze ta sama nazwa, bez możliwości pomyłki!
class KeyCategory(Enum):
    STANDARD = "STANDARD"  # np. Litery, cyfry
    NUMPAD = "NUMPAD"  # klawiatura numeryczna (numpad)
    FUNCTION = "FUNCTION"  # klawisze F1-F12
    SPECIAL = "SPECIAL"  # Klawisze specjalne np. Enter, Backspace, Tab, Escape
    MODIFIER = "MODIFIER"  # Klawisze modyfikujące (zmieniające działanie innych klawiszy):
    # Shift (zmienia małe litery na wielkie): Ctrl (do skrótów jak Ctrl+C), Alt (podobnie jak Ctrl),
    # Cmd (klawisz Windows/Command na Macu)
    NAVIGATION = "NAVIGATION"  # Klawisze do poruszania się (Left, Right, Up, Down, End, Page Up, Page Down)
    UNKNOWN = "UNKNOWN"  # Reszta klawiszy, która nie pasuje do żadnej z kategorii powyżej
    MULTIMEDIA = "MULTIMEDIA"  # Klawisze multimedialne (głośność, play/pause etc.)


@dataclass  # @dataclass pisze za nas nudny kod, upraszcza tworzenie klas do przechowywania danych
# automatycznie generuje konstruktor i inne metody, pozwala łatwo zarządzać wartościami
# domyślnymi i niezmiennością, zwiększa czytelność i redukuje ilość powielanego kodu
class KeyEvent:
    key: str  # jaki klawisz
    category: KeyCategory  # kategoria klawisza
    timestamp: datetime  # kiedy naciśnięto
    event_type: str  # press/release
    is_modifier_active: bool = False  # czy Shift/Ctrl/Alt jest wciśnięty
    # Optional mówi Pythonowi, że wartość może być None albo obiektem, nie wiemy dokładnie jakiego typu będzie klawisz z
    # pynput, chcemy być elastyczni i móc przyjąć każdy typ obiektu, każda rzecz jest obiektem
    raw_key: Optional[object] = None  # Surowy klawisz to skomplikowany oryginalny obiekt klawisza z biblioteki pynput
    # zawiera techniczne informacje o klawiszu, zachowujemy go na wszelki wypadek, gdybyśmy
    # Potrzebowali technicznych szczegółów


class MyException(Exception): pass


# Nie używamy @dataclass, bo korzystamy z niego tylko do przechowywania danych, natomiast nasza klasa działa
# troche jak robot, keyboardeventhandler jest mózgiem całym przechwytywania klawiszy
class KeyboardEventHandler:
    """
        Główna klasa odpowiedzialna za przechwytywanie i przetwarzanie zdarzeń klawiatury.
        Obsługuje kategoryzację klawiszy, kombinacje klawiszy i modyfikatory.
    """

    def __init__(self):
        self.modifiers_active = set()  # set() jest jak lista, ale każda rzecz może być tylko raz (nie zawiera duplikatów)
        # Łatwo sprawdzić co jest w środku, łatwo dodawać i usuwać rzeczy
        self.last_key = None
        self.caps_lock_on = False #Dodajemy śledzenie stanu Caps Locka

    # funkcje zaczynające się od _ to funkcje wewnętrzne, których nie powinno wywoływać się w zewnętrznym kodzie.
    def _categorize_key(self, key) -> KeyCategory:  # metoda zwraca wartość typu KeyCategory
        """
            Kategoryzuje klawisz na podstawie jego właściwości
        """
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
            elif key.name in ['shift', 'ctrl', 'alt', 'cmd']:  # klawisz cmd często możemy znaleźć na klawiaturach MAC
                return KeyCategory.MODIFIER
            # Jeśli nazwa to jeden z klawiszy nawigacyjnych
            elif key.name in ['up', 'down', 'left', 'right', 'home', 'end', 'page_up', 'page_down']:
                return KeyCategory.NAVIGATION
            elif key.name in ['media_play_pause', 'media_volume_up', 'media_volume_down', 'media_next','media_previous']:
                return KeyCategory.MULTIMEDIA
            # Inne klawisze specjalne (Enter, Backspace itp.)
            return KeyCategory.SPECIAL

        # Jeśli nie pasuje do żadnej kategorii
        return KeyCategory.UNKNOWN

    # Funkcja wewnętrzna-nie wykorzystujemy jej w kodzie zewnętrznym
    def _format_key(self, key, should_capitalize=False) -> str:
        try:
            # Mapowanie polskich znaków - dodajemy też wielkie litery
            polish_chars = {
                '\u0105': 'ą',  '\u0107': 'ć',  '\u0119': 'ę',  '\u0142': 'ł',  '\u0144': 'ń',  '\u00f3': 'ó',
                '\u015b': 'ś',  '\u017a': 'ź',  '\u017c': 'ż',  '\u0104': 'Ą',  '\u0106': 'Ć',  '\u0118': 'Ę',
                '\u0141': 'Ł',  '\u0143': 'Ń',  '\u00d3': 'Ó',  '\u015a': 'Ś',  '\u0179': 'Ź',  '\u017b': 'Ż' }

            # Sprawdzamy, czy to nie jest znak kontrolny (Ctrl+litera)
            if hasattr(key, 'char') and key.char and ord(key.char) < 32:
                ctrl_chars = {
                    1: 'Ctrl+A', 2: 'Ctrl+B', 3: 'Ctrl+C', 4: 'Ctrl+D',
                    5: 'Ctrl+E', 6: 'Ctrl+F', 7: 'Ctrl+G', 8: 'Ctrl+H',
                    9: 'Ctrl+I', 10: 'Ctrl+J', 11: 'Ctrl+K', 12: 'Ctrl+L',
                    13: 'Ctrl+M', 14: 'Ctrl+N', 15: 'Ctrl+O', 16: 'Ctrl+P',
                    17: 'Ctrl+Q', 18: 'Ctrl+R', 19: 'Ctrl+S', 20: 'Ctrl+T',
                    21: 'Ctrl+U', 22: 'Ctrl+V', 23: 'Ctrl+W', 24: 'Ctrl+X', 25: 'Ctrl+Y', 26: 'Ctrl+Z'
                }
                return ctrl_chars.get(ord(key.char), f'Ctrl+{key.char}')

            # Obsługa klawiszy specjalnych
            special_keys = {
                'space': 'SPACE',
                'enter': 'ENTER',
                'backspace': 'BACKSPACE',
                'tab': 'TAB',
                'media_play_pause': 'PLAY/PAUSE',
                'media_volume_up': 'VOL_UP',
                'media_volume_down': 'VOL_DOWN'
            }

            # Dla klawiszy z numpada dodajemy prefix 'NUM_'
            # i odejmujemy 96, by otrzymać właściwą cyfrę (96=0, 97=1 itd.)
            if hasattr(key, 'vk') and 96 <= key.vk <= 105:
                return f"NUM_{key.vk - 96}"

            # Dla zwykłych klawiszy zwracamy ich znak (literę/cyfrę)
            elif hasattr(key, 'char') and key.char:
                #Dodatkowe sprawdzenie dla polskich znaków
                formatted_char = key.char.encode('utf-8').decode('utf-8')

                if formatted_char in polish_chars:
                    formatted_char = polish_chars[formatted_char]
                # Zwróć już po uwzględnieniu shift/caps
                if should_capitalize:
                    return formatted_char.upper()
                else:
                    return formatted_char.lower()

            # Dla klawiszy z nazwą (F1, Enter itp.) zwracamy nazwę wielkimi literami
            elif hasattr(key, 'name'):
                return key.name.upper()

            # Jeśli żaden warunek nie pasuje, konwertujemy obiekt na tekst
            return str(key)

            # Jeśli wystąpi błąd podczas próby odczytu atrybutów klawisza
        except AttributeError:
            return "UNKNOWN_KEY"

    def _handle_modifier(self, key, is_press: bool):
        # Obsługa Caps Locka
        if hasattr(key, 'name') and key.name == 'caps_lock' and is_press:
            self.caps_lock_on = not self.caps_lock_on  # Przełączamy stan
            return

        MODIFIER_NAMES = ['shift', 'shift_l', 'shift_r','ctrl', 'ctrl_l',
                          'ctrl_r','alt', 'alt_l', 'alt_r','cmd', 'cmd_l', 'cmd_r']
        # Sprawdzamy, czy klawisz ma atrybut 'name' i czy jest modyfikatorem
        if hasattr(key, 'name') and key.name in MODIFIER_NAMES:
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

        if key is None:
            raise MyException("Otrzymano nieprawidłowe zdarzenie klawisza")

        # Aktualizacja stanu modyfikatorów przed utworzeniem zdarzenia (np.ctrl, shift etc.)
        # aby zapewnić spójność stanu dla nowego KeyEvent
        self._handle_modifier(key, True)  # True oznacza naciśnięcie

        # Sprawdzamy, czy Shift/Caps mają wpływ na wielkość liter
        is_shift_active = any(
            mod in self.modifiers_active
            for mod in ['shift', 'shift_l', 'shift_r']
        )
        should_capitalize = self.caps_lock_on != is_shift_active

        # Określamy kategorię klawisza (NUMPAD, FUNCTION, itp.)
        category = self._categorize_key(key)

        # Zamieniamy obiekt klawisza na czytelny format tekstowy
        formatted_key = self._format_key(key, should_capitalize=should_capitalize)

        # Tworzymy nowy obiekt KeyEvent zawierający wszystkie informacje o zdarzeniu
        event = KeyEvent(
            key=formatted_key,  # sformatowana nazwa klawisza
            category=category,  # kategoria klawisza
            timestamp=datetime.now(),  # dokładny czas naciśnięcia
            event_type='press',  # typ zdarzenia (naciśnięcie)
            is_modifier_active=bool(self.modifiers_active),  # czy są aktywne modyfikatory
            raw_key=key  # oryginalny obiekt klawisza
        )

        # Zapisujemy ostatnie zdarzenie
        self.last_key = event

        # Zwracamy utworzony obiekt zdarzenia
        return event

    def handle_release(self, key) -> KeyEvent:
        # Aktualizujemy stan modyfikatorów
        # False oznacza puszczenie klawisza
        self._handle_modifier(key, False)

        # Podobnie jak w handle_press, określamy kategorię
        category = self._categorize_key(key)
        formatted_key = self._format_key(key)

        # Tworzymy obiekt zdarzenia dla puszczenia klawisza
        event = KeyEvent(
            key=formatted_key,  # sformatowana nazwa klawisza
            category=category,  # kategoria klawisza
            timestamp=datetime.now(),  # dokładny czas naciśnięcia
            event_type='release',  # typ zdarzenia (puszczenie)
            is_modifier_active=bool(self.modifiers_active),  # czy są aktywne modyfikatory
            raw_key=key  # oryginalny obiekt klawisza
        )

        # Zapisujemy ostatnie zdarzenie
        self.last_key = event
        print(f'{event.key}')
        return event


# TODO: Zapis danych do pliku (Raczej z JSON będziemy korzystać)

class KeyboardEventSaver:
    def __init__(self):
        self.base_directory = os.path.dirname(os.path.abspath(__file__))
        self.data_directory = os.path.join(self.base_directory, "..", "data")
        self.handler = None #Odnośnik do handlera

    def set_handler(self, handler):
        """Ustawia referencję do KeyboardEventHandler"""
        self.handler = handler

    # Generowanie nazwy pliku z datą
    def get_daily_filename(self, type: str = "json"):
        current_date = datetime.now().strftime("%Y-%m-%d")
        if type == "json":
            return f"keypress_log_{current_date}.json"
        return f"keypress_text_{current_date}.txt"

    def get_file_path(self, type: str):
        filename = self.get_daily_filename(type)
        return os.path.join(self.data_directory, filename)

    def save_event_to_json(self, key_event: KeyEvent) -> bool:
        """
        Zapisuje zdarzenie 'KeyEvent' do pliku JSON.
        """

        try:
            # Przygotowanie danych do serializacji
            event_data = {
                "timestamp": key_event.timestamp.isoformat(),
                "key": key_event.key,
                "category": key_event.category.value,
                "event_type": key_event.event_type,
                "modifiers_active": key_event.is_modifier_active
            }
            # Upewniamy się, że katalog istnieje
            os.makedirs(self.data_directory, exist_ok=True)
            # Zapisujemy dane do pliku
            try:
                with open(self.get_file_path("json"), "a", encoding="utf-8") as f:
                    json_line = json.dumps(event_data, ensure_ascii=False)
                    f.write(json_line + "\n")
                return True

            except (PermissionError, OSError) as e:
                print(f"Błąd zapisu do pliku: {e}")
                return False
        except (TypeError, ValueError) as e:
            print(f"Błąd serializacji JSON: {e}")
            return False

    def save_formatted_text(self, key_event: KeyEvent) -> None:
        """
        Zapisuje sformatowany tekst do osobnego pliku w czytelnej formie
        """
        if key_event.event_type != 'press':
            return

        formatted_text = ""

        # Sprawdzamy stan Caps Locka i Shifta
        should_capitalize = False
        if self.handler:
            is_shift_active = 'shift' in self.handler.modifiers_active
            should_capitalize = self.handler.caps_lock_on != is_shift_active

        # Formatowanie specjalnych klawiszy
        # zapisujemy tylko naciśnięcia
        if key_event.key in ['SPACE', 'SPACEBAR']:
            formatted_text = " "
        elif key_event.key == 'ENTER':
            formatted_text = "\n"
        elif key_event.key == 'TAB':
            formatted_text = "\t"
        elif key_event.key in ['BACKSPACE', 'DELETE']:
            # Możemy zaimplementować usuwanie znaków
            return
        #Pomijamy klawisze specjalne:
        elif key_event.category in [
            KeyCategory.NAVIGATION,
            KeyCategory.FUNCTION,
            KeyCategory.MODIFIER,
            KeyCategory.MULTIMEDIA
        ]:
            return
        #Dla zwykłych klawiszy sprawdzamy, czy to pojedynczy znak
        elif len(key_event.key) == 1:
            formatted_text = key_event.key.upper() if should_capitalize else key_event.key.lower()

            # Zapisujemy do pliku
        try:
            with open(self.get_file_path(".txt"), "a", encoding="utf-8") as f:
                f.write(formatted_text)
        except (PermissionError, OSError) as e:
            print(f"Błąd zapisu tekstu: {e}")


def main():
    handler = KeyboardEventHandler()
    saver = KeyboardEventSaver()
    saver.set_handler(handler) #Ustawiamy referencję do handlera

    def on_press(key):
        event = handler.handle_press(key)
        saver.save_event_to_json(event)
        saver.save_formatted_text(event)

    def on_release(key):
        event = handler.handle_release(key)
        saver.save_event_to_json(event)
        saver.save_formatted_text(event)

    # Nasłuchiwanie klawiszy
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
