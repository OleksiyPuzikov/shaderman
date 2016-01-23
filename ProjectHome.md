The initial ShaderMan was a visual Renderman shader building tool, made in spirit of ShadeTree, Slim and XSI - a free software package I've prepared for Renderman community.

But it has it's obvious problems:

  * Delphi codebase restricted the porting to Linux - and it was the most wanted new feature.
  * I haven't really touched that code since December 2003.
  * Even thought ShaderMan was extensible behind the original Renderman SL code generation, in practice it was almost impossible to do since lots of stuff was just hardcoded.

Thus ShaderMan.Next was born with a different set of features and goals:
  * Easily extensible. Whenever it's Renderman SL, Cg, GLSL, Python, C++, scene graph, particle system, Unix shell or a UI for a scientific data flow system - it's easy to implement or already implemented.
  * Portable between Windows, Linux and Mac OS X from the very beginning.
  * New nice code. Yes, it's a complete rewrite using the different programming language - but it really makes it graspable. It's only ~~2k~~ 2.2k lines!

![http://shaderman.googlecode.com/files/shaderman_next_snapshot1.gif](http://shaderman.googlecode.com/files/shaderman_next_snapshot1.gif)

You can download the stable build using the link at your right, or just get the most recent source code snapshot at http://shaderman.googlecode.com/svn/trunk/.

Make sure to download and install:
  * [Python](http://www.python.org/)
  * ctypes
  * [wxPython](http://www.wxpython.org/)
  * [PyOpenGL](http://pyopengl.sourceforge.net/)

Windows users might found [this page](http://www.visionegg.org/Download_and_Install/Install_on_Windows) pretty useful.