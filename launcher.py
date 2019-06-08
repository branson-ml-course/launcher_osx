from tkinter import *
from tkinter.messagebox import showwarning, askquestion
from tkinter.simpledialog import askstring
from tkinter.ttk import *
from collections import namedtuple
from traceback import format_exc
from PIL import Image, ImageTk
from subprocess import Popen, PIPE
from functools import partial
from os.path import exists, abspath
import pickle, re, threading
from datetime import datetime

"""
This module uses native dialogs via Tkinter
to simply the launching of Jupyter notebooks,
which usually require terminal commands

THIS MODULE IS FOR *MAC OSX* USE ONLY.
Please use the other module for Windows 
use
"""

__author__ = "Amrit Baveja"
__copyright__ = "(c) Copyright 2019, Amrit Baveja"

__license__ = "GNU General Public License v3.0"
__version__ = "1.0.1"
__maintainer__ = "Amrit Baveja"
__email__ = "amrit_baveja@branson.org"

# NO ATTRIBUTIONS -- CODED FROM SCRATCH 

class Messages:
    LONG_WORKSPACE_MSG = """In order to create notebooks, you must first
                specify your Workspace directory. Your Workspace directory is the location
                on your computer in which you are going to store notebooks. Please make
                sure you have access to this location (it is not located on an ephemeral
                storage device, such as a USB drive) as you will download notebooks from
                Haiku to this folder. Would you like to continue?""".replace("\n", " ").replace("  ", "")

    CHANGING_WORKSPACE_MSG = """Changing your workspace will lose all of your current work and can
                                have a multitude of unintended consequences, especially with Student
                                Backup-- this function will probably fail as git histories will be vastly
                                different. PLEASE DO NOT DO THIS ON YOUR OWN! ASK A TEACHER FOR HELP!""".replace(
                                    "\n", " ").replace("  ", "")

    JUPYTER_KILL_MSG = """"Please go back to your browser and save your
                         changes via ⌘S. Press okay when you are 
                         ready to exit""".replace("\n", " ").replace("  ", "")
        
class WindowUtilities:
    @staticmethod
    def center_and_size_window(window, width, height):
        """
        Center the main window in the screen
        """
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        # set width and height of screen, along with offset to center

    @staticmethod
    def add_label(window, x, y, size=20, text="", image_path="", image=False):
        """
        Create a new label and add it to 
        the dialog pane

        :param x: the x coordinate of the label
        :param y: the y coordinate of the label
        :param text: the text of the label (if text label)
        :param image_path: the path to the image asset (if image label)
        :param image: whether or not it is an image label
        """
        if not image:
            label = Label(window, text=text) # text label
            label.config(font=("Verdana", size)) # set font family + size
        else:
            image_file = Image.open(image_path) # open image using PIL
            image_file = image_file.resize((85, 85), Image.ANTIALIAS) # (height, width)
            photo = ImageTk.PhotoImage(image_file) # render resized photo
            label = Label(window, image=photo) 
            label.image = photo # avoid garbage collection
        label.place(x=x, y=y, anchor='center')

    @staticmethod
    def add_button(window, x, y, text, action_function):
        """
        Place a button in the dialog pane

        :param x: the x coordinate to place button
        :param y: y coordinate to place button
        :param text: the text of the button
        :param action_function: the function to call when
            button is clicked
        """
        button = Button(window, text=text, command=action_function)
        Launcher.BUTTONS[(x, y)] = button
        button.place(x=x, y=y, anchor='center')

class Handlers:
    @staticmethod
    def prompt_for_branson_email(mainWindow):
        """
        Prompt for branson email for username extraction --
        amrit_baveja@branson.org --> baveja_amrit
        :param mainWindow: the core dialog
        """
        email = askstring("Input", "Let's get to know you better!"
        " What is your Branson email address (x_y@branson.org)?",
        parent=mainWindow)
        branson_email_regex = re.compile('[A-Za-z-].*?_[A-Za-z-].*?@branson\.org')
        # validate first_last@branson.org (accounts for multi-word last names as well)

        if not email or len(email) == 0 or not branson_email_regex.match(email): # bad input
            user_response = askquestion("Error", "Please enter a valid Branson email. Continue?")
            if user_response == 'no': # allow user to exit
                return False
            else:
                return Handlers.prompt_for_branson_email(mainWindow) # try again (recursively)
        else:
            ready = askquestion("Confirm", "You entered {}. Is that correct?".format(email))
            if ready == 'no':
                return Handlers.prompt_for_branson_email(mainWindow) # try again (recursively)
            else:
                return email.split("@")[0] # extract username

    @staticmethod
    def check_for_branch_username(mainWindow):
        """
        Check for username existance. If it doesn't
        exist, create it
        """
        if exists(Launcher.USERNAME_FILE):
            Handlers.read_user()
            return True
        else:
            username = Handlers.prompt_for_branson_email(mainWindow)
            if not username:
                return False
            Handlers.write_username(username)
            return True
    
    @staticmethod
    def prompt_for_workspace():
        """
        Prompt for workspace directory
        """
        from getpass import getuser
        try:
            from tkinter import filedialog # start at ~ directory (home for logged in user)
            return filedialog.askdirectory(initialdir='/Users/{}'.format(getuser())) # python 3
        except:
            from tkinter import tkFiledialog # start at ~ directory (home for logged in user)
            return tkFileDialog.askdirectory(initialdir='/Users/{}'.format(getuser())) # python 2 fallback

    @staticmethod
    def write_path(path):
        """
        Write the workspace path to a file for persistance
        :param path: the workspace path to write
        """
        with open(Launcher.WORKSPACE_FILE, 'wb') as workspace:
            pickle.dump(path, workspace)
        Launcher.WORKSPACE_PATH = path

    @staticmethod
    def write_username(user):
        """
        Write the username to a file for git comitting later on
        :param user: the username to write
        """
        with open(Launcher.USERNAME_FILE, 'wb') as username_file:
            pickle.dump(user, username_file)
        Launcher.USERANAME = user
    
    @staticmethod
    def read_path():
        """
        Read the workspace path from a file for retrieval
        """
        with open(Launcher.WORKSPACE_FILE, 'rb') as workspace_file:
            Launcher.WORKSPACE_PATH = pickle.load(workspace_file)
    
    @staticmethod
    def read_user():
        """
        Read the workspace path from a file for retrieval
        """
        with open(Launcher.USERNAME_FILE, 'rb') as username_file:
            Launcher.USERNAME = pickle.load(username_file)
            print(Launcher.USERNAME)
    
    @staticmethod
    def check_for_workspace_directory(override=False):
        """
        Check if the workspace directory exists. If it doesn't,
        prompt and create it
        :param override: whether or not to ignore if file exists or not.
        """
        if override: showwarning("Warning!", Messages.CHANGING_WORKSPACE_MSG)
        if not override and exists(Launcher.WORKSPACE_FILE): 
            Handlers.read_path()
            return True
        else:
            user_continue = askquestion("Warning!", Messages.LONG_WORKSPACE_MSG) # user info
            if user_continue == 'no': return False # give user option to exit
            path = Handlers.prompt_for_workspace() # file dialog
            if not path:
                showwarning("Error", "Aborted. Path not set.") # data handling
                return False
            user_ready = askquestion("Success", """Path is {}. Would you like to adjust your choice?""". \
                format(path)) == 'no'
            
            if not user_ready: Handlers.check_for_workspace_directory()
            else: 
                Handlers.write_path(path) # serialize path
                showwarning("Success!", "Workspace set! Success")
                return True

    @staticmethod 
    def poll_error(process):
        """
        This checks a given bash process for errors
        and displays a tkinter dialog when it happens
        :param process: Popened process (running in sepparate thread than Python program)
        """
        output, error = process.communicate()
        if process.returncode != 0:
            showwarning("Error", "Error encountered:\n" + str(error))

    @staticmethod
    def run_bash_command(command, mainWindow):
        """
        Run the specified bash command
        :param command: the command to run
        """
        p = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        t1 = threading.Thread(target=partial(Handlers.poll_error, p), daemon=True)
        # run in a thread that is NON-BLOCKING, so that there is no problem
        # after the button is hit
        t1.start() # start daemon

    @staticmethod
    def check_initialize_git_repository(mainWindow):
        """
        Check if a git repository has already 
        been initialized in the Workspace path.
        If it hasn't, initialize it
        """
        PAT = "b98502d0ddf4ac575148ec04db03b3fdecc7848c" # github OAuth Token so 
        # we don't have to use plaintext username/password combo

        if not exists(Launcher.WORKSPACE_PATH + "/.git"):
            INITIALIZE_CMD = """
            cd {} && \
            git init && \
            git remote add origin https://{}:@github.com/branson-ml-course/notebooks.git
            """.format(Launcher.WORKSPACE_PATH, PAT)
            Handlers.run_bash_command(INITIALIZE_CMD, mainWindow)
        
    @staticmethod
    def commit_notebook_changes(mainWindow):
        showwarning("Student Backup Service", "Persisting your notebook data to GitHub for durability...")
        if not Handlers.check_for_branch_username(mainWindow) or not \
             Handlers.check_for_workspace_directory():
            return       
        Handlers.check_initialize_git_repository(mainWindow)
        COMMIT_CMD = """
        cd {} && \
        git add . && \
        git commit -m "Student Backup: {}" && \
        git push origin {}
        """.format(Launcher.WORKSPACE_PATH, 
            str(datetime.now().strftime("%m/%d/%y - %I:%M:%S %p")), Launcher.USERNAME) # timestamp
        Handlers.run_bash_command(COMMIT_CMD, mainWindow)

    @staticmethod
    def kill_jupyter(mainWindow, lab):
        """
        Kill Jupyter
        :param mainWindow: the root tkinter window
        :param lab: whether or not we are running jupyter lab
             (false if notebook)
        """
        showwarning("Warning", Messages.JUPYTER_KILL_MSG)
        # so student's are happy
        Handlers.run_bash_command("pkill -f jupyter", mainWindow)
        y = 100 if lab else 225
        notebook_type = "Lab" if lab else "Notebook"
        handler = Handlers.launch_jupyter_lab if lab else Handlers.launch_jupyter_notebook
        Launcher.BUTTONS[(400, y)].config(text="Launch Jupyter " + notebook_type)
        Launcher.BUTTONS[(400, y)].config(command=partial(handler, Launcher.WINDOW))
        showwarning("Done!", "It is now okay to close the notebook window in your browser.")

    @staticmethod
    def launch_jupyter_notebook(mainWindow):
        """
        Handler to launch jupyter notebook server (and commit)
        :param mainWindow: the mainWindow (root) for error dialogs
        """
        if not Handlers.check_for_branch_username(mainWindow) or not \
             Handlers.check_for_workspace_directory():
            return

        NOTEBOOK_CMD = """
        cd {} && \
        jupytenotebook
        """.format(Launcher.WORKSPACE_PATH.replace(" ", "\ "))
        Handlers.run_bash_command(NOTEBOOK_CMD, mainWindow)
        Launcher.BUTTONS[(400, 225)].config(text="Stop Jupyter Notebook and Save")
        Launcher.BUTTONS[(400, 225)].config(command=partial(Handlers.kill_jupyter, mainWindow, False))
    
    @staticmethod
    def launch_jupyter_lab(mainWindow):
        """
        Handler to launch jupyter lab server (and commit)
        :param mainWindow: the mainWindow (root) for error dialogs
        """
        if not Handlers.check_for_branch_username(mainWindow) or not \
             Handlers.check_for_workspace_directory():
            return

        LAB_CMD = """
        cd {} && \
        jupyter lab
        """.format(Launcher.WORKSPACE_PATH)
        Handlers.run_bash_command(LAB_CMD, mainWindow)
        Launcher.BUTTONS[(400, 100)].config(text="Stop Jupyter Lab and Save")
        Launcher.BUTTONS[(400, 100)].config(command=partial(Handlers.kill_jupyter, mainWindow, True))

class Launcher:
    WINDOW = None # main pane
    WORKSPACE_PATH = None
    USERNAME = None
    JUPYTER_LAB_IMG = abspath('./assets/jupyterlab.png')
    JUPYTER_NOTEBOOK_IMG = abspath('./assets/jupyternotebook.png')
    WORKSPACE_FILE = abspath('/tmp/.branson_ml_workspace_directory')
    USERNAME_FILE = abspath('/tmp/.branson_ml_username')
    PERSISTANT_STORAGE = 'https://github.com/{}/{}'
    BUTTONS = {}


    @staticmethod
    def create_main_window():
        """
        Create the main window of the dialog pane
        :param width: the width of the box (in px)
        :param height: the height of the box (in px)
        """
        Launcher.WINDOW = Tk() # create new tkinter dialog
        Launcher.WINDOW.title("Branson ML Course: Notebook Launcher")
        Launcher.WINDOW.configure(background='#EBEBEB')
        # of main pane
        WindowUtilities.center_and_size_window(Launcher.WINDOW, 600, 400)

    @staticmethod
    def construct_items_from_kwargs(data_list, handler_function):
        """
        Add the dict version of namedtuple representation
        of the item metadata
        """
        for data in data_list:
            handler_function(**data._asdict())

    @staticmethod
    def create_labels():
        """
        Create all the text labels in the dialog
        """
        LabelData = namedtuple('LabelData', ['text', 'x', 'y', 'size'])
        labels = [
            LabelData('Please select a notebook environment', 300, 20, 20), # header
            LabelData('(c) Copyright 2019, Amrit Baveja under GNU GPLv3 License', 300, 375, 12), # footer,
            LabelData('Other Options', 300, 316, 15)
        ]
        Launcher.construct_items_from_kwargs(labels, 
            partial(WindowUtilities.add_label, Launcher.WINDOW))
        
    @staticmethod
    def create_images():
        """
        Create all the images in the dialog
        from assets
        """
        ImageData = namedtuple('ImageData', ['image_path', 'x', 'y', 'image'])

        images = [
            ImageData(Launcher.JUPYTER_LAB_IMG, 200, 100, True), # jupyter lab icon
            ImageData(Launcher.JUPYTER_NOTEBOOK_IMG, 200, 225, True) # jupyter notebook icon
        ]
        Launcher.construct_items_from_kwargs(images, 
            partial(WindowUtilities.add_label, Launcher.WINDOW))

    @staticmethod
    def create_buttons():
        """
        Create all buttons in the dialog with
        the appropriate function handlers
        """
        ButtonData = namedtuple('ButtonData', ['x', 'y', 'text', 'action_function'])
        
        lab_handler = partial(Handlers.launch_jupyter_lab, Launcher.WINDOW)
        notebook_handler = partial(Handlers.launch_jupyter_notebook, Launcher.WINDOW)
        change_workspace_handler = partial(Handlers.check_for_workspace_directory, True)
        force_commit_handler = partial(Handlers.commit_notebook_changes, Launcher.WINDOW)

        buttons = [
            ButtonData(400, 100, 'Launch Jupyter Lab', lab_handler),
            ButtonData(400, 225, 'Launch Jupyter Notebook', notebook_handler),
            ButtonData(200, 350, 'Change Workspace Directory', change_workspace_handler),
            ButtonData(400, 350, 'Force Commit', force_commit_handler)
        ]

        Launcher.construct_items_from_kwargs(buttons, 
            partial(WindowUtilities.add_button, Launcher.WINDOW))


    @staticmethod
    def draw_dialog():
        """
        Draw the dialog with elements necessary
        """
        Launcher.create_main_window()
        Launcher.create_labels()
        Launcher.create_images()
        Launcher.create_buttons()

    @staticmethod
    def start_launcher():
        """
        Start the launcher dialog
        """
        Launcher.draw_dialog()
        Launcher.WINDOW.mainloop()
    
if __name__ == '__main__':
    Launcher.start_launcher()

    