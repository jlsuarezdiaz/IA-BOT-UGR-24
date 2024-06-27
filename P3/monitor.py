import pandas as pd
import threading
import time
from db_functions import get_P3_classification
import curses
import time

class ClassificationMonitor:
    def __init__(self, func, stdscr, refresh_rate=10, rows=50, old_refresh_rate=60):
        self.screen = stdscr

        self.func = func
        self.refresh_rate = refresh_rate
        self.old_refresh_rate = old_refresh_rate
        self.rows = rows
        self.stop = False
        self.thread = threading.Thread(target=self.listen)
        self.show_range = (0, self.rows)
        self.current_page = 0
        self.total_pages = None
        self.last_refresh = None
        self.last_old_refresh = None
        self.last_df = None
        self.thread.start()

        self.group_modes = {
            "ALL": lambda df: df['group_name'] != "",
            "A1D": lambda df: df['group_name'] == "A1D",
            "A2D": lambda df: df['group_name'] == "A2D",
            "A3D": lambda df: df['group_name'] == "A3D",
            "DG": lambda df: df['group_name'].str[-1] == "D",
            "A1": lambda df: df['group_name'] == "A1",
            "A2": lambda df: df['group_name'] == "A2",
            "A3": lambda df: df['group_name'] == "A3",
            "A": lambda df: (df['group_name'].str[0] == "A") & (df['group_name'].str.len() == 2),
            "B1": lambda df: df['group_name'] == "B1",
            "B2": lambda df: df['group_name'] == "B2",
            "B3": lambda df: df['group_name'] == "B3",
            "B": lambda df: (df['group_name'].str[0] == "B") & (df['group_name'].str.len() == 2),
            "C1": lambda df: df['group_name'] == "C1",
            "C2": lambda df: df['group_name'] == "C2",
            "C": lambda df: (df['group_name'].str[0] == "C") & (df['group_name'].str.len() == 2),
            "D1": lambda df: df['group_name'] == "D1",
            "D2": lambda df: df['group_name'] == "D2",
            "D3": lambda df: df['group_name'] == "D3",
            "D": lambda df: (df['group_name'].str[0] == "D") & (df['group_name'].str.len() == 2),
            "PROFES": lambda df: df['group_name'] == "PROFES",
        }

        self.column_modes = {
            "NORMAL": list(range(1, 11)) + [19, 22],
            "P1": list(range(1, 7)) + list(range(11, 15)) + [20, 22],
            "P2": list(range(1, 7)) + list(range(15, 19)) + [21, 22],
            "MINIMAL": list(range(1, 7)),
            # "LEADERBOARD": [1] + list(range(4, 22))
        }

        self.current_group_mode = "ALL"
        self.current_column_mode = "NORMAL"
        self.current_group_index = 0
        self.current_column_index = 0
        self.total_group_modes = len(self.group_modes)
        self.total_column_modes = len(self.column_modes)
        
        self.run()

    def run(self):
        while not self.stop:
            df = self.func('current')
            self.last_refresh = time.time()
            self.show(df)
            time.sleep(self.refresh_rate)
            if self.last_df is None or (self.last_old_refresh is not None and time.time() - self.last_old_refresh > self.old_refresh_rate):
                self.last_df = self.func("prev")
                self.last_old_refresh = time.time()

    def listen(self):
        while not self.stop:
            key = self.screen.getch()
            key = chr(key)
            # Refresh when key is pressed or each refresh_rate seconds
            refresh = self.on_press(key)
            if refresh:
                df = self.func("current")
                self.last_refresh = time.time()
                self.show(df)
            

    def show(self, df):
        self.screen.clear()
        df_filtered = df[self.group_modes[self.current_group_mode](df)]
        self.total_pages = len(df_filtered) // self.rows
        if len(df_filtered) % self.rows > 0:
            self.total_pages += 1

        df_to_show = df_filtered.iloc[self.show_range[0]:self.show_range[1], self.column_modes[self.current_column_mode]]
        df_len = len(df_to_show)
        
        df_string = df_to_show.to_string()
        #self.screen.addstr(1, 0, df_to_show.to_string())
        # If the df_to_show has no rows, show a message
        if df_len == 0:
            self.screen.addstr(0, 0, 'No users for this group!', curses.A_BOLD | curses.color_pair(1))
        else:
            for i, line in enumerate(df_string.split('\n')):
                if i == 0:
                    self.screen.addstr(i, 0, line, curses.A_BOLD | curses.color_pair(4))
                else:
                    # Get the corresponding item from the df
                    curr_abbr = df_to_show.iloc[i - 1, :]
                    curr = df[df['player_id'] == curr_abbr['player_id']].iloc[0, :]
                    # Find the same row in the old df (if exists). Use the 'id' column to match
                    if self.last_df is not None:
                        old = self.last_df[self.last_df['player_id'] == curr['player_id']]
                        if len(old) > 0:
                            old = old.iloc[0, :]
                            # Compare the indices of the current and old df
                            # If curr is lower than old, green (better rank)
                            if int(curr.name) < int(old.name):
                                self.screen.addstr(i, 0, line, curses.A_BOLD | curses.color_pair(2))
                            # If curr is higher than old, red (worse rank)
                            elif int(curr.name) > int(old.name):
                                self.screen.addstr(i, 0, line, curses.A_BOLD | curses.color_pair(1))
                            # If the indices are the same but the leaderboard_score has improved, green as well
                            elif int(curr.name) == int(old.name) and curr['points'] > old['points']:
                                self.screen.addstr(i, 0, line, curses.A_BOLD | curses.color_pair(2))
                            # Otherwise, check if there is any change in the values. If there is, yellow
                            #elif not curr.equals(old):
                            #    self.screen.addstr(i, 0, line, curses.A_BOLD | curses.color_pair(3))
                            # Otherwise, normal
                            else:
                                self.screen.addstr(i, 0, line)  
                        else:
                            # New addition, green
                            self.screen.addstr(i, 0, line, curses.A_BOLD | curses.color_pair(2))

                        #self.screen.addstr(i, 0, curr.index, curses.A_BOLD | curses.color_pair(4))
                    else:
                        # First refresh, normal
                        self.screen.addstr(i, 0, line)

        # Add at the end of the df output
        self.screen.addstr(2 + df_len, 0, 'Page {}/{}'.format(self.current_page + 1, self.total_pages), curses.A_BOLD | curses.color_pair(4))
        self.screen.addstr(3 + df_len, 0, f"Group mode: {self.current_group_mode}, Column mode: {self.current_column_mode}", curses.A_BOLD | curses.color_pair(4))
        self.screen.addstr(4 + df_len, 0, f"Press 'q' to exit, 'n' to go to next page, 'p' to go to previous page, 'g' to filter by groups, 'c' to change columns", curses.A_BOLD | curses.color_pair(4))
        self.screen.addstr(5 + df_len, 0, f"Last refresh: {time.strftime('%H:%M:%S', time.localtime(self.last_refresh)) if self.last_refresh is not None else 'Never'} - Last diff refresh: {time.strftime('%H:%M:%S', time.localtime(self.last_old_refresh)) if self.last_old_refresh is not None else 'Never'}", curses.A_BOLD | curses.color_pair(4))
        self.screen.refresh()


    def on_press(self, key):
        refresh = False
        if key == 'q':
            self.stop = True

        elif (key == 'n' or key == curses.KEY_RIGHT) and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_range = (self.current_page * self.rows, (self.current_page + 1) * self.rows)
            refresh = True
        elif (key == 'p' or key == curses.KEY_RIGHT) and self.current_page > 0:
            self.current_page -= 1
            self.show_range = (self.current_page * self.rows, (self.current_page + 1) * self.rows)
            refresh = True
        elif key == 'g':
            self.current_page = 0
            self.show_range = (0, self.rows)
            # Loop to next group mode
            self.current_group_index = (self.current_group_index + 1) % self.total_group_modes
            self.current_group_mode = list(self.group_modes.keys())[self.current_group_index]
            refresh = True
        elif key == 'c':
            self.current_page = 0
            self.show_range = (0, self.rows)
            # Loop to next column mode
            self.current_column_index = (self.current_column_index + 1) % self.total_column_modes
            self.current_column_mode = list(self.column_modes.keys())[self.current_column_index]
            refresh = True


        return refresh
        

def main(stdscr):
    monitor = None
    try:
        stdscr.scrollok(True)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        monitor = ClassificationMonitor(get_P3_classification, stdscr, refresh_rate=10, rows=50, old_refresh_rate=300)
        monitor.stop = True
        monitor.thread.join()
    except KeyboardInterrupt:
        monitor.thread.join()
        print('Exiting monitor')

if __name__ == '__main__':
    curses.wrapper(main)
