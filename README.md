# PraatKatili
A praat mockup aimed at being hackable by mere mortals. Based on pyAudioAnalysis, IPython, Qt and god knows what else at this point. 

## What is this, and why
Everybody loves Praat. But everybody also hates Praat. Especially the hundreds of developers who tried to hack Praat into something else in endless frustration. While the magnitude of Paul's work requries no endorsement at this point, it is not secret that his... idiosyncratic use of C++ has destroyed many a hopeful PhD student's plans of an easily hackable pipeline. To that end, I decided, out of completely personal needs, to try and develop a cross between RStudio and Praat, with IPython thrown in the middle and see what comes out. 

This is strictly Python 3. The GUI library is PyQt5. Naturally, we use numpy for arrays and such. pyAudioAnalysis handles the signal processing (through other libraries), although this will definitely be extended if this thing sees enough use. Mostly because I am having to port that library to Python 3 and I am not known for seeing things through. It would be particularly fitting if somebody could take a chair and tame some of them underlying Praat goodies and expose them to Python. 

## Features
* Integrated IPython shell. You can interact with everything, Blender style. 
* File browser.
* Resource browser. Holds files, arrays of interest, and so on. A bit like Praat. Linked to both the file browser *and* the IPython shell.
* Matplotlib integration. Plot various styles, tinker with them if you want. 
* Session support. All resources and plots as well as window state can be saved/restored.
* Everything is a dock widget. Meaning they can be docked, they can float, they can be hidden, they can be arbitrarily tabbed. All this is saved along with the session. 

## Todo
* Shortcut buttons for common tasks
* Perhaps a menu that isn't a context menu.
* Save/restore multiple sessions
* Spreadsheet view as an alternative to plotting, like Praat's draw function.
* Drag and drop for stuff? Meh. 
