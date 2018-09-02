# Copyright (C) 2018 Caio Carrara <eu@caiocarrara.com.br>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# LICENSE for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
import logging.config
import os
import subprocess
import time
import threading
import tkinter as tk


logger = logging.getLogger('dojo_referee')


APPLICATION_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPLICATION_TITLE = 'Coding Dojo Referee'
APPLICATION_WIDTH = 400
APPLICATION_HEIGHT = 200
APPLICATION_GEOMETRY = '%sx%s' % (APPLICATION_WIDTH, APPLICATION_HEIGHT)
APPLICATION_DEFAULT_FONT = (None, 30, 'bold')
APPLICATION_SECONDARY_FONT = (None, 22)
ASSETS_DIR = os.path.join(APPLICATION_BASE_DIR, 'assets')
INITIAL_TIME = '05:00'
LOG_CONFIG_FILE = os.path.join(APPLICATION_BASE_DIR, 'logging.conf')
SOUND_EXEC = 'aplay'
SOUND_BEGIN_FILE = os.path.join(ASSETS_DIR, 'begin.wav')
SOUND_FINISH_FILE = os.path.join(ASSETS_DIR, 'finish.wav')


class CountdownThread(threading.Thread):
    def __init__(self, master, duration, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master = master
        self.duration = time.strptime(duration, '%M:%S')
        self.remaining_sec = self.duration.tm_min * 60 + self.duration.tm_sec

        self.should_stop = False

    def run(self):
        logger.info('Countdown started...')
        while self.remaining_sec >= 0 and not self.should_stop:
            remaining_min, remaining_sec = divmod(self.remaining_sec, 60)
            remaining = '{:02d}:{:02d}'.format(remaining_min, remaining_sec)
            self.master.update_remaining_time(remaining)
            time.sleep(1)
            self.remaining_sec -= 1
        logger.info('Countdown finished...')
        return

    def stop(self):
        self.should_stop = True


class BlinkingLabelThread(threading.Thread):
    def __init__(self, master, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.master = master
        self.text = text
        self.should_stop = False

    def run(self):
        while True and not self.should_stop:
            current_value = self.master.remaining_time.get()
            if current_value:
                self.master.remaining_time.set('')
            else:
                self.master.remaining_time.set(self.text)
            time.sleep(0.5)
        return

    def stop(self):
        self.should_stop = True


class DojoReferee(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APPLICATION_TITLE)
        self.geometry(APPLICATION_GEOMETRY)
        self.standard_font = APPLICATION_DEFAULT_FONT
        self.secondary_font = APPLICATION_SECONDARY_FONT
        self.resizable(False, False)

        self.setup_widgets()

        self.protocol('WM_DELETE_WINDOW', self.safe_exit)

    def setup_widgets(self):
        self.main_frame = tk.Frame(
            self,
            width=APPLICATION_WIDTH,
            height=APPLICATION_HEIGHT,
            bg='white',
            padx=10,
            pady=5,
        )
        self.start_button = tk.Button(
            self.main_frame,
            text='Start',
            width=8,
            bg='green',
            activebackground='green',
            fg='white',
            activeforeground='white',
            command=self.start,
            font=self.secondary_font,
        )

        self.stop_button = tk.Button(
            self.main_frame,
            text='Stop',
            width=8,
            bg='red',
            activebackground='red',
            fg='white',
            activeforeground='white',
            command=self.stop,
            font=self.secondary_font,
        )

        self.remaining_time = tk.StringVar(self.main_frame)
        self.remaining_time.set(INITIAL_TIME)
        self.countdown_label = tk.Label(
            self.main_frame,
            textvar=self.remaining_time,
            bg='white',
            fg='black',
            font=self.standard_font,
        )

        self.main_frame.pack(fill=tk.BOTH, expand=1)
        self.countdown_label.pack(fill=tk.X, pady=10)
        self.start_button.pack(side='left', pady=10)
        self.stop_button.pack(side='right', pady=10)

    def start(self):
        self.update_remaining_time(INITIAL_TIME)
        self.countdown = CountdownThread(self, INITIAL_TIME)
        self.countdown.start()
        try:
            self.sound_playing = subprocess.Popen([SOUND_EXEC, SOUND_BEGIN_FILE], stdout=subprocess.DEVNULL,
                                                  stderr=subprocess.STDOUT)
        except OSError as exc:
            logger.error('The following error happened trying to play finish sound', exc)

    def stop(self):
        self.countdown_label['fg'] = 'black'
        if hasattr(self, 'countdown'):
            self.countdown.stop()
            self.update_remaining_time(INITIAL_TIME)
        if hasattr(self, 'blinking'):
            self.blinking.stop()
        if hasattr(self, 'sound_playing'):
            self.sound_playing.terminate()

    def safe_exit(self):
        self.stop()
        self.after(200, self.destroy)

    def update_remaining_time(self, time):
        if time == '00:00':
            self.countdown_label['fg'] = 'red'
            self.blinking = BlinkingLabelThread(self, time)
            self.blinking.start()
            try:
                self.sound_playing = subprocess.Popen([SOUND_EXEC, SOUND_FINISH_FILE], stdout=subprocess.DEVNULL,
                                                      stderr=subprocess.STDOUT)
            except OSError as exc:
                logger.error('The following error happened trying to play finish sound', exc)
        self.remaining_time.set(time)


def main():
    logging.config.fileConfig(LOG_CONFIG_FILE)
    referee = DojoReferee()
    referee.mainloop()


if __name__ == '__main__':
    main()
