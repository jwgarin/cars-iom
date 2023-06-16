import pyperclip
import time

prev_paste = None
while True:
    time.sleep(0.25)
    try:
        if pyperclip.paste().startswith('http'):
            curr_paste = pyperclip.paste().split('/')[-1]
            pyperclip.copy(curr_paste)
        if not prev_paste or prev_paste != curr_paste:
            prev_paste = curr_paste
            print(curr_paste)
    except:
        pass
