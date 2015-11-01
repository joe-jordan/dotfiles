dotfiles
========

To avoid the complication of having a git repo in my home folder directly, 
this repo can be checked out and "installed" (the contents symlinked).

    create/
      # files to be "created" (symlinked), overwriting any existing file.

    append/
      # files to be appended (if the contents not already present) into existing files.
      # e.g. each distro has a default .bashrc, don't clobber it.

The installation system assumes that dotfiles are organised into discrete stanzas, which
are delimited by a blank line (`"\n\n"`). If you want similar (but distinct) versions of 
the same stanza to be identified, give them a separated header comment like:

    # rgrep - bash shortcut for recursive grep
    
    function rgrep {
        ...
    }

TODO
----

 * *(done, except uninstall)* write the `makefile` / python script to install the dotfiles automagically.
 * import .bashrc and other snippets from all my machines.
