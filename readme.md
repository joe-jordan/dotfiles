dotfiles
========

To avoid the complication of having a git repo in my home folder directly, 
this repo can be checked out and "installed" (the contents symlinked).

    create/
      # files to be "created" (symlinked), overwriting any existing file.

    append/
      # files to be appended (if the contents not already present) into existing files.
      # e.g. each distro has a default .bashrc, don't clobber it.

TODO
----

 * write the `makefile` / python script to install the dotfiles automagically.
 * import .bashrc and other snippets from all my machines.
