# print("Tutaj pojawi się wkrótce kod")
from pynput import keyboard
FILE_PATH="core/keypress_log.txt"

class MyException(Exception): pass

def on_press(key):
    try:
        #hasattr to funkcja, która sprawdza, czy dany obiekt ma określony atrybut (vk - virtual key code)
        if hasattr(key, 'vk') and 96 <= key.vk <= 105: # Kody klawiszy 96-105 to Numpad (0-9)
            numpad_key = key.vk - 96 # Obliczamy wartość klawisza Numpad
            print(f'Numpad key {numpad_key} pressed')
        else:
            print('alphanumeric key {0} pressed'.format(key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))
    try:
        with open(FILE_PATH, "a") as f:
            f.write(str(key) + "\n")
    except FileNotFoundError:
        with open(FILE_PATH, "w") as f:
            f.write(str(key) + "\n")

def on_release(key):
    try:
        if hasattr(key, 'vk') and 96 <= key.vk <= 105:
            numpad_key = key.vk - 96
            print(f'Numpad key {numpad_key} released').format(key.char)
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

# ...or, in a non-blocking fashion:
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()