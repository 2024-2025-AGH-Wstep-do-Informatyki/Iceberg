# print("Tutaj pojawi się wkrótce kod")
from pynput import keyboard


class MyException(Exception): pass

def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def on_release(key):
    print('{0} released'.format(
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