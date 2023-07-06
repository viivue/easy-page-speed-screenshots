import tkinter
from tkinter import ttk

from . import config

class EntryWithPlaceholder(tkinter.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", width=config.app_width):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.configure(font=(config.font, config.body_txt), width=width, borderwidth=2, relief='solid')

        if placeholder:
            self.bind("<FocusIn>", self.foc_in)
            self.bind("<FocusOut>", self.foc_out)

            self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = config.txt_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()