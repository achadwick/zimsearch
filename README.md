# Zimsearch

Authors: Davi da Silva Böger, Andrew Chadwick  
GitHub: <https://github.com/achadwick/zimsearch>

Zimsearch is a simple proof-of-concept implementation of a GNOME Shell
search provider for Zim pages.

**THIS IS VERY EARLY ALPHA SOFTWARE. USE AT YOUR OWN RISK**

## Installation

See [INSTALL][] for installation instructions.

## Usage

Search terms typed in the GNOME Shell overview are used to look up Zim
pages from your notebooks. Page titles are matched against the search
terms and only pages that contain all the terms are shown. By default,
all notebooks are searched, but there is a plugin setting to limit the
search to the default notebook only.

It is also possible to limit the search to a certain notebook by adding
a term preceded by a hash sign (`#`). Only notebooks whose names contain
all the `#` terms are searched.

New pages can be created by typing a complete page title, a little like
[nvPY][]. By default the new page goes into your default notebook, but you
can select others with `#` terms as above.

## Bugs

Please file bug reports or feature requests in github issue tracker.

[INSTALL]: INSTALL
[nvPY]: https://github.com/cpbotha/nvpy

