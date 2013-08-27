# Generic Blender Exporter

## A python exporter script made to be generic

This script is made for those who are willing to export data from Blender
but are not willing to learn Python.

The data are currently exported formated in SML (S-expression Markup
Language), but other formats such as XML, JSON or YAML could be added
if there are demands.

SML was chosen because it is small and handy, and every programming
language should have a library to parse it.  If the programming language you
use don't have one, you can send me an email to ask me another formating, or
you can do it yourself while it's mainly a printf issue.

Also this script tries to export most contents of the blend file.  If there
are some contents not exported that you would be willing to use send me an
email to make the demand.

This script is compatible with Blender version 2.49b
(Released-date: 2010-06-16)
 
## Install:

If you don't have root access you can copy this script in the directory:
  ~/.blender/scripts/
otherwise you can install it in the directory:
  /usr/lib/blender/scripts/

