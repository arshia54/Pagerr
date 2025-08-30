# narme afzar 1

from tkinter import *
import tkinter.scrolledtext as scrolledtext
import webbrowser
import wikipedia
import pyttsx3
import pygame
import pyperclip
import threading
import speech_recognition as sp
from PIL import ImageTk, Image
import requests
import os
from io import BytesIO

app = Tk()
app.title("wiki_app")
app.geometry("400x300")
app.resizable(0,0)
background_color = "#121212"
app.config(bg=background_color)

pygame.init()
pusestatus = False
stopstatues = False

languages = {
    "English": "en", "French": "fr", "Spanish": "es", "German": "de",
    "Italian": "it", "Portuguese": "pt", "Russian": "ru", "Korean": "ko"
}
selected_language = StringVar(app)
selected_language.set("English")  # default lang

# funcs
def change_look():
   global background_color
   if background_color == "#121212":
      background_color = "purple"
   else:
      background_color = "#121212"


   for widget in [searchentry, searcbuttton, pausebutton, stopbutton,copybutton, webbutton, savebutton, voice_button, wikiresult]:
      widget.configure(bg=background_color, fg="white")

   lang_menu.config(bg=background_color, fg="white", highlightthickness=0)
   lang_menu["menu"].config(bg=background_color, fg="white")

   img_label.config(bg=background_color)
   app.config(bg=background_color)

def search():
   global pusestatus, wikisearch, searchitem, stopstatues
   searchitem = searchentry.get().strip()
   wikipedia.set_lang(languages[selected_language.get()])

   if not searchitem:
      wikiresult.delete('1.0', 'end')
      wikiresult.insert(INSERT, "Please type.")
      return

   try:
      page = wikipedia.page(searchitem)
      wikisearch = wikipedia.summary(searchitem, sentences=5)
   except wikipedia.exceptions.DisambiguationError:
      wikiresult.delete('1.0', 'end')
      wikiresult.insert(INSERT, "Too many results (DisambiguationError). Please be more specific.")
      return
   except wikipedia.exceptions.PageError:
      wikiresult.delete('1.0', 'end')
      wikiresult.insert(INSERT, "Page not found.")
      return
   except Exception as a:
      wikiresult.delete('1.0', 'end')
      wikiresult.insert(INSERT, f"Error: {a}")
      return


   if getattr(page, "images", None):
      try:
         response = requests.get(page.images[0], timeout=10)
         img_data = Image.open(BytesIO(response.content))
         img_data = img_data.resize((120,120))
         photo = ImageTk.PhotoImage(img_data)
         img_label.config(image=photo)
         img_label.image = photo
      except Exception:
         img_label.config(image='', text='[no image]')
         img_label.image = None
   else:
      img_label.config(image='', text='[no image]')
      img_label.image = None


   wikiresult.delete('1.0', 'end')
   wikiresult.insert(INSERT, wikisearch)

   # audio
   pausebutton.config(text='pause', state='normal')
   stopbutton.config(text='stop', state='normal')
   copybutton.config(state='normal')
   webbutton.config(state='normal')
   savebutton.config(state='normal')

   pusestatus = False
   stopstatues = False
   try:
      pygame.mixer.music.unload()
   except Exception:
      pass
   engine = pyttsx3.init()
   engine.save_to_file(wikisearch, 'wikiresult.wav')
   engine.runAndWait()
   pygame.mixer.music.unload()
   pygame.mixer.music.load('wikiresult.wav')
   pygame.mixer.music.play(0)

def voice_search():
   r = sp.Recognizer()
   try:
      with sp.Microphone() as source:
         wikiresult.delete('1.0', 'end')
         wikiresult.insert(INSERT, 'listening...')
         audio = r.listen(source)
      query = r.recognize_google(audio)
      searchentry.delete(0,END)
      searchentry.insert(0, query)
      search()
   except Exception:
      wikiresult.delete('1.0', 'end')
      wikiresult.insert(INSERT, "Sorry, I couldn't understand.")

def pause():
   global pusestatus
   if not pusestatus:
      pygame.mixer.music.pause()
      pusestatus = True
      pausebutton.config(text='unpause')
   else:
      pygame.mixer.music.unpause()
      pusestatus = False
      pausebutton.config(text='pause')

def stop():
   global stopstatues, pusestatus
   if not stopstatues:
      pygame.mixer.music.stop()
      stopbutton.config(text='play')
      pusestatus = False
      pausebutton.config(text='pause')
      stopstatues = True
   else:
      pygame.mixer.music.play()
      stopbutton.config(text='stop')
      stopstatues = False

def copy():
   try:
      pyperclip.copy(wikisearch)
   except Exception:
      pass

def save_artc():
   try:
      if not os.path.exists('saved_articles'):
         os.makedirs("saved_articles")
      with open(f"saved_articles/{searchitem}.txt", 'w', encoding='utf-8') as file:
         file.write(wikisearch)
      wikiresult.insert(INSERT, f'\n\n[article saved as {searchitem}.txt]')
   except Exception as e:
      wikiresult.insert(INSERT, f'\n\n[save error: {e}]')

def open_browser():
   try:
      webbrowser.open(wikipedia.page(searchitem).url)
   except Exception:
      print("no page")

#adding menu////////////
menubar = Menu(app)
menubar.add_command(label="theme",command=change_look)
app.config(menu=menubar)

# UI elements
searchentry = Entry(app, width=30,font=('arial',12))
searchentry.place(relx= 0.05, rely=0.05)

searcbuttton = Button(app,width=10,text="search",command=search)
searcbuttton.place(relx=0.75,rely=0.05)

voice_button = Button(app, text="voice search", command=voice_search, bg=background_color, fg="white")
voice_button.place(relx=0.75, rely=0.12)

lang_menu = OptionMenu(app, selected_language, *languages.keys())
lang_menu.config(bg=background_color, fg="white")
lang_menu["menu"].config(bg=background_color, fg="white")
lang_menu.place(relx=0.05, rely=0.12)

pausebutton = Button(app,width=10,text="pause", command=pause)
pausebutton.place(relx=0.05,rely=0.20)

stopbutton = Button(app,width=10,text="stop",command=stop)
stopbutton.place(relx=0.26,rely=0.20)

copybutton = Button(app,width=10,text="copy",command=copy)
copybutton.place(relx=0.47,rely=0.20)

savebutton = Button(app,width=10,text="save",command=save_artc)
savebutton.place(relx=0.68,rely=0.20)

webbutton = Button(app,text="read on wikipedia",command=open_browser)
webbutton.place(relx=0.05,rely=0.27)


img_label = Label(app, bg=background_color)
img_label.place(relx=0.75, rely=0.27)

wikiresult = scrolledtext.ScrolledText(app, height=12,width=44,padx=10,font=("arial"))
wikiresult.pack(pady=(80,0))

# states/colors
for w in [searchentry, searcbuttton, voice_button, pausebutton, stopbutton, copybutton, savebutton, webbutton, wikiresult]:
   w.configure(bg="#121212", fg="white")
lang_menu.config(bg="#121212", fg="white")
lang_menu["menu"].config(bg="#121212", fg="white")

pausebutton.configure(state='disabled')
stopbutton.configure(state='disabled')
copybutton.configure(state='disabled')
savebutton.configure(state='disabled')
webbutton.configure(state='disabled')

app.mainloop()
