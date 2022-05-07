# -*- coding: utf-8 -*-
# Copyright 2016-2017 Andrew Chadwick <a.t.chadwick@gmail.com>
# Copyright 2014-2015 Davi da Silva Böger <dsboger@gmail.com>
"""Zim plugin to display Zim pages in GNOME Shell search results."""

import os
import json
import logging
import textwrap
from gettext import gettext as _
import subprocess

import dbus.service
from zim.main import NotebookCommand
from zim.plugins import PluginClass
from zim.search import SearchSelection
from zim.search import Query

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

logger = logging.getLogger(__name__)
ZIM_COMMAND = "zim"


# Zim plugin integration:

class GnomeShellSearchPluginCommand (NotebookCommand):
    """Class to handle "zim --plugin GnomeShellSearch [NOTEBOOK]"."""

    arguments = ('[NOTEBOOK]',)

    def run(self):
        from zim.config import ConfigManager
        import zim.notebook

        notebook_info = self.get_default_or_only_notebook()
        if not notebook_info:
            logger.error("No notebooks?")
            return
        notebook, _junk = zim.notebook.build_notebook(notebook_info)
        config_manager = ConfigManager
        config_dict = config_manager.preferences
        preferences = config_dict['GnomeShellSearch']
        preferences.setdefault('search_all', True)
        Provider.main()


class GnomeShellSearch (PluginClass):
    """Plugin description and user options."""

    plugin_info = {
        'name': _('GNOME Shell Search'),  # T: plugin name
        'description': textwrap.dedent(_("""
            This plugin provides search results in GNOME Shell.

            Disabling this plugin has no effect.
            Please use “System Settings → Search” in GNOME
            to disable Zimsearch results.
            Changing the settings may require killing running 
            "zim --plugin gnomeshellsearch" instances
            and quit zim for the changes to be enacted.
            """)),  # T: plugin description
        'author': 'Davi da Silva Böger',
        }

    plugin_preferences = (
        (
            'search_all', 'bool',
            _('Search all notebooks, instead of only the default'),
            True,
        ),
        (
            'search_names_only', 'bool',
            _('Search only names, instead off full text search (Name:*query*).  MUCH faster'),
            True,
        ),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        notebook = self.get_default_or_only_notebook()
        logger.debug(
            "{} notebook is set as default in shell search.".format(notebook))
        if not Provider.run_flag:
            Provider(notebook=notebook,
                     search_all=self.preferences['search_all'],
                     search_names_only=self.preferences['search_names_only'])

    @staticmethod
    def get_default_or_only_notebook():
        """
        Most of this method is copied from
        `zim.main.NotebookCommand.get_default_or_onlly_notebook`.

        But this method return a notebook directly instead
        (just like `GnomeShellSearchPlugin.run` did).
        """
        from zim.notebook import (get_notebook_list, resolve_notebook,
                                  build_notebook)
        notebooks = get_notebook_list()
        uri = None
        if notebooks.default:
            uri = notebooks.default.uri
        elif len(notebooks) == 1:
            uri = notebooks[0].uri
        else:
            return None
        # The `pwd` is default value of `zim.main.Command.pwd`
        notebook_info = resolve_notebook(uri, pwd=os.getcwd())
        result, _ = build_notebook(notebook_info)
        return result

# Dbus activation and search provider:

SEARCH_IFACE = 'org.gnome.Shell.SearchProvider2'
BUS_NAME = 'net.launchpad.zim.plugins.gnomeshellsearch.provider'
OBJECT_PATH = '/net/launchpad/zim/plugins/gnomeshellsearch/provider'


class Provider(dbus.service.Object):
    """
    The main search provider.
    To ensure that the provider does not started before,
    check `Provider.run_flag` before to construct the class.
    For example:

        if not Provider.run_flag:
            Provider(...)
    """
    run_flag = False

    def __init__(self, notebook=None, search_all=True, search_names_only=True):
        # make sure the Provider does not run twice or more in one application
        assert (not self.run_flag)
        self.run_flag = True
        import dbus.mainloop.glib

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(
            self,
            bus_name=name,
            object_path=OBJECT_PATH,
            )

        self.notebook = notebook
        self.notebook_cache = {}
        self.search_all = search_all
        self.search_names_only = search_names_only

    @staticmethod
    def main():
        from gi.repository import GLib
        GLib.MainLoop().run()

    @staticmethod
    def quit():
        from gi.repository import GLib
        GLib.MainLoop().quit()

    @dbus.service.method(dbus_interface=SEARCH_IFACE,
                         in_signature='as', out_signature='as',
                         async_callbacks=('reply_handler', 'error_handler'))
    def GetInitialResultSet(self, terms, reply_handler, error_handler):
        """Handles the initial search."""
        results = self._get_search_results(terms)
        reply_handler(results)

    @dbus.service.method(dbus_interface=SEARCH_IFACE,
                         in_signature='asas', out_signature='as',
                         async_callbacks=('reply_handler', 'error_handler'))
    def GetSubsearchResultSet(self, prev_results, terms,
                              reply_handler, error_handler):
        """Handles searches within sets of previously returned results."""
        results = self._get_search_results(terms)
        reply_handler(results)

    @dbus.service.method(dbus_interface=SEARCH_IFACE,
                         in_signature='as', out_signature='aa{sv}')
    def GetResultMetas(self, identifiers):
        """Gets detailed metadata about identified search results."""
        metas = []
        for result_id in identifiers:
            notebook_id, page_id, create = self._from_result_id(result_id)
            path = page_id.split(":")
            name = path[-1]
            if self.search_all:
                template = "(#{notebook}) {path}"
            else:
                template = "{path}"
            description = template.format(
                notebook=notebook_id,
                path="/".join(path[0:-1]),
                )
            icon = "text-x-generic"
            if create:
                name = _(u"New page: “{}”").format(name)
                icon = "text-x-generic-template"
            meta = {
                "id": result_id,
                "name": name,
                "gicon": icon,
                "description": description,
                }
            metas.append(meta)
        return metas

    @dbus.service.method(dbus_interface=SEARCH_IFACE,
                         in_signature='sasu', out_signature='')
    def ActivateResult(self, identifier, terms, timestamp):
        """Handles the user choosing a search result from those offered."""
        try:
            notebook_id, page_id, create = self._from_result_id(identifier)
            logger.debug("ActivateResult: notebook: %r", notebook_id)
            logger.debug("ActivateResult: page: %r", page_id)
            proc = subprocess.Popen(
                args=[ZIM_COMMAND, notebook_id, page_id],
                close_fds=True,
                cwd="/",
                )
            logger.debug("ActivateResult: done (rc=%r)", proc.returncode)
        except:
            logger.exception("ActivateResult failed")

    @dbus.service.method(dbus_interface=SEARCH_IFACE,
                         in_signature='asu', out_signature='')
    def LaunchSearch(self, terms, timestamp):
        """
        Handles the user choosing the app icon on the left of the results.

        This is supposed to launch the application itself, with the
        search terms already typed in.
        After upstream's changes for 0.67, we cannot do this without
        reimplementing as an GApplication and zim-plugin pair.
        While we're in transition, just show the list.
        """
        sw = SearchWindow(self.results)
        Gtk.main()

    def _get_search_results(self, terms):
        try:
            notebook_terms, normal_terms = self._process_terms(terms)
            notebooks = list(self._get_search_notebooks(notebook_terms))
            self.results = []
            query_str = u" ".join(normal_terms)
            query_str_name_only = u"Name:*" + u"* Name:*".join(normal_terms) + "*"
            if not query_str.isspace():
                if self.search_names_only:
                    query = Query(query_str_name_only)
                else:
                    query = Query(query_str)
                for notebook in notebooks:
                    logger.debug('Searching %r for %r', notebook, query)
                    selection = SearchSelection(notebook)
                    selection.search(query)
                    for path in selection:
                        rid = self._to_result_id(notebook.name, path.name)
                        self.results.append(rid)
            self._process_results(self.results, notebook_terms, normal_terms)
            return self.results
        except:
            logger.exception("_get_search_results() failed")

    def _process_results(self, results, notebook_terms, normal_terms):
        """
        Post-processing of the results set.

        This adds extra "New page" results for all matching notebooks,
        or the default notebook if there were no notebook terms.

        The new-page results are only appended if there are no
        preexisting entries in the results.
        """

        if len(results) > 0:
            return

        if not self.notebook:
            return

        page_name = " ".join(normal_terms)

        if notebook_terms:
            import zim.notebook
            notebook_list = zim.notebook.get_notebook_list()
            for notebook_info in notebook_list:
                notebook_id = notebook_info.name
                if self._contains_all_terms(notebook_id, notebook_terms):
                    result_id = self._to_result_id(notebook_id, page_name,
                                                   create=True)
                    results.append(result_id)
        else:
            notebook_id = self.notebook.name
            result_id = self._to_result_id(notebook_id, page_name, create=True)
            results.append(result_id)

    def _process_terms(self, terms):
        """Pre-processing of search terms."""
        notebook_terms = []
        normal_terms = []
        for term in terms:
            if term.startswith("#"):
                notebook_term = term[1:]
                if len(notebook_term) > 0:
                    notebook_terms.append(notebook_term)
            else:
                normal_terms.append(term)
        return notebook_terms, normal_terms

    def _get_search_notebooks(self, notebook_terms):
        import zim.notebook

        search_notebooks_info = []
        notebook_list = zim.notebook.get_notebook_list()
        if notebook_terms:
            for notebook_info in notebook_list:
                if self._contains_all_terms(notebook_info.name,
                                            notebook_terms):
                    search_notebooks_info.append(notebook_info)
        elif self.search_all:
            search_notebooks_info.extend(notebook_list)
        else:
            search_notebooks_info.append(self.notebook.info)

        for notebook_info in search_notebooks_info:
            yield self._load_notebook(notebook_info.name)

    def _load_notebook(self, notebook_id):
        if notebook_id in self.notebook_cache:
            notebook = self.notebook_cache[notebook_id]
        else:
            import zim.notebook

            notebook_list = zim.notebook.get_notebook_list()
            notebook_info = notebook_list.get_by_name(notebook_id)
            if notebook_info:
                notebook, _junk = zim.notebook.build_notebook(notebook_info)
                self.notebook_cache[notebook_id] = notebook
        return notebook

    def _to_result_id(self, notebook_id, page_id, create=False):
        result_dict = {
            "notebook": notebook_id,
            "page": page_id,
            "create": create,
            }
        return json.dumps(result_dict)

    def _from_result_id(self, result_id):
        result_dict = json.loads(result_id)
        return (
            result_dict.get("notebook", self.notebook.name),
            result_dict.get("page", "New Page"),
            result_dict.get("create", False),
            )

    def _contains_all_terms(self, contents, terms):
        for term in terms:
            if str(term).casefold() not in str(contents).casefold():
                return False
        return True


class SearchWindow(Gtk.Window):
    """
    Search result window.
    """
    def __init__(self, results):
        Gtk.Window.__init__(self, title=_("Zim search"))
        self.connect("delete-event", self.exit_app)

        # build GUI
        # ====================================================================
        win_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(win_box)

        # Next step is to add search to this window...
        #self.search_box = Gtk.Entry()
        #win_box.add(self.search_box)

        self.box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_min_content_width(200)
        scroll_window.set_min_content_height(200)
        scroll_window.set_vexpand(True)
        scroll_window.set_propagate_natural_width(True)
        scroll_window.set_propagate_natural_height(True)

        scroll_window.add(self.box)

        win_box.pack_start(scroll_window, True, True, 0)
        # ====================================================================

        self.results_dict = self.convert_to_dict(results)

        for notebook_name in self.results_dict:
            lbl = Gtk.Label(notebook_name)
            lbl.set_margin_top(10)
            self.box.add(lbl)
            pages = self.results_dict.get(notebook_name)
            for page in pages:
                btn = Gtk.Button(page)
                btn.connect("clicked", self.open_result,
                            (notebook_name, page))
                self.box.add(btn)

        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

    def _from_result_id(self, result_id):
        """
        Convert result_id to item as list.
        """
        result_dict = json.loads(result_id)
        return (
            result_dict.get("notebook"),
            result_dict.get("page"),
            result_dict.get("create", False),
            )

    def convert_to_dict(self, results):
        """
        Convert results from search provider to dict.
           {notebook1: [page1, page2, ...],
            ...
            notebookN: [pageX, pageY, ...]}
        """
        result_dict = {}
        for item in results:
            result_item = self._from_result_id(item)
            if result_dict.get(result_item[0]) is None:
                result_dict[result_item[0]] = [result_item[1],]
            else:
                result_dict.get(result_item[0]).append(result_item[1])

        return result_dict

    def open_result(self, btn, result_item):
        """
        Activate some result.
        Open this page in Zim.
        """
        proc = subprocess.Popen(
            args=[ZIM_COMMAND, result_item[0], result_item[1]],
            close_fds=True,
            cwd="/",
            )
        self.exit_app()

    def exit_app(self, *args):
        """
        Exit search window.
        """
        Gtk.main_quit()
