# Zim Search plugin for GNOME

[![Build Status](https://travis-ci.org/achadwick/zimsearch.svg?branch=master)](https://travis-ci.org/achadwick/zimsearch)

Zimsearch lets you search through your [Zim][] Desktop Wiki pages
comfortably from the Activities Overview search box of the GNOME 3
Shell. It acts as a GNOME [desktop search provider][], and also as a
[Zim plugin][].

## Features

* Fast incremental search of existing Zim pages.
* Immediate note creation by typing in a new title.
* Like [nvPY][] or [Notational Velocity][], but feels like part of GNOME.
* Optionally limit searches to the default notebook only.
* Select notebooks with special search terms.

## Screenshots

TBD

## Setup

If you have all the dependencies already:

* Run “`sudo pip install .`” or “`pip install --system .`”
* Log out and back in again

For detailed instructions, see the [Installation Guide][].

## Using Zimsearch

### Search for pages

Search terms typed in the GNOME Shell overview are used to look up Zim
pages from your notebooks. To find an existing page, click on
<samp>Activities</samp> in GNOME or press the key that's often decorated
with a Windows logo. We'll call it <kbd>Meta</kbd> for short. If you
have a Zim page called “Recipes for Goulash”, you can search for it by typing…

> <kbd>Meta</kbd> `Recip`

You might not need to type it all out. Once it's the only matched item
in all of your the search results, you can press <kbd>Return</kbd>
to open the page in Zim.

Page titles are matched against the search terms and only pages that
contain all the terms are shown. By default, all notebooks are searched,
but there's a setting in the Zim plugin to limit the search to the
default notebook only.

It is also possible to limit the search to a certain notebook by adding
a term preceded by a hash sign (`#`). Only notebooks whose names contain
all the `#` terms are searched.

> <kbd>Meta</kbd> `Pancake batter #Recipes` <kbd>Return</kbd>

### Creating pages

New pages can be created by typing a complete page title, a little like
[nvPY][]. When there are no real results, Zimsearch adds some extra
"<samp>New Page …</samp>" results. By default a new page goes into your
default notebook, but you can select others with `#` terms as above.

## Development

### Authors

* Andrew Chadwick (current maintainer)
* Davi da Silva Böger (original author)

### Contributing

GitHub: <https://github.com/achadwick/zimsearch>

Please file bug reports or feature requests in the GitHub issue tracker.

[Installation Guide]: INSTALL.md
[Zim]: http://zim-wiki.org/
[nvPY]: https://github.com/cpbotha/nvpy
[Notational Velocity]: http://notational.net
[desktop search provider]: https://developer.gnome.org/SearchProvider/
[Zim plugin]: https://github.com/jaap-karssenberg/zim-wiki/wiki/Plugins
