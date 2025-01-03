import win32gui

def callback(hwnd, window_titles):
    if win32gui.IsWindowVisible(hwnd):
        window_title = win32gui.GetWindowText(hwnd)
        if window_title:
            window_titles.append(window_title)

def list_windows():
    window_titles = []
    win32gui.EnumWindows(callback, window_titles)
    return sorted(window_titles)

if __name__ == "__main__":
    print("Found windows:")
    for title in list_windows():
        if "discord" in title.lower():
            print(f"Discord window found: '{title}'")
        else:
            print(f"Other window: '{title}'")