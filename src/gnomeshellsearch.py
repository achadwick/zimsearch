# -*- coding: utf-8 -*-

# Copyright 2014 Davi da Silva Böger <dsboger@gmail.com>

'''Zim plugin to display Zim pages in GNOME Shell search results.
'''

import json
import logging

logger = logging.getLogger('zim.plugins.gnomeshellsearch')


from zim.main import NotebookCommand

class GnomeShellSearchPluginCommand(NotebookCommand):
	'''Class to handle "zim --plugin GnomeShellSearch [NOTEBOOK]".'''
	
	arguments = ('[NOTEBOOK]',)

	def run(self):
		from zim.config import ConfigManager
		
		notebook, _ = self.build_notebook()
		config_manager = ConfigManager()
		preferences = config_manager.get_config_dict('preferences.conf')['GnomeShellSearch']
		preferences.setdefault('search_all', True)
		Provider(notebook, preferences['search_all']).main()

		
from zim.plugins import PluginClass
		
class GnomeShellSearch(PluginClass):

	plugin_info = {
		'name': _('GNOME Shell Search'),  # T: plugin name
		'description': _('''\
This plugin provides search results for GNOME Shell.

Disabling this plugin has no effect. Please, use the "System Settings > Search" to disable Zim search results.
'''),  # T: plugin description
		'author': 'Davi da Silva Böger',
	}
	
	plugin_preferences = (
		('search_all', 'bool', \
			_('Search all notebooks, instead of only the default'), True),
	)
	
	def __init__(self, config=None):
		PluginClass.__init__(self, config)

		
import dbus.service

SEARCH_IFACE = 'org.gnome.Shell.SearchProvider2'
BUS_NAME = 'net.launchpad.zim.plugins.gnomeshellsearch.provider'
OBJECT_PATH = '/net/launchpad/zim/plugins/gnomeshellsearch/provider'

class Provider(dbus.service.Object):

	def __init__(self, notebook=None, search_all=True):
		import dbus.mainloop.glib
		
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
		name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name=name, object_path=OBJECT_PATH)
		
		self.notebook = notebook
		self.notebook_cache = {}
		self.search_all = search_all
		
	def main(self):
		import gtk
		
		gtk.main()
		
	def quit(self):
		import gtk
		
		gtk.main_quit()

	@dbus.service.method(dbus_interface=SEARCH_IFACE,
				in_signature='as', out_signature='as',
				async_callbacks=('reply_handler', 'error_handler'))
	def GetInitialResultSet(self, terms, reply_handler, error_handler):
		"""Handles the initial search."""
		notebook_terms, normal_terms = self._process_terms(terms)
		search_notebooks = self._get_search_notebooks(notebook_terms)
		result = []
		if search_notebooks:
			for search_notebook in search_notebooks:
				result.extend(self._search_notebook(search_notebook, normal_terms))
		self._process_results(result, terms)
		reply_handler(result)
	
	@dbus.service.method(dbus_interface=SEARCH_IFACE,
				in_signature='asas', out_signature='as',
				async_callbacks=('reply_handler', 'error_handler'))
	def GetSubsearchResultSet(self, prev_results, terms, reply_handler, error_handler):
		"""Handles searches within sets of previously returned results."""
		notebook_terms, normal_terms = self._process_terms(terms)
		results = []
		for result_id in prev_results:
			notebook_id, page_id, create = self._from_result_id(result_id)
			if create:
				continue
				# It will be added later, on the end, by _process_results().
			if notebook_terms and not self._contains_all_terms(notebook_id, notebook_terms):
				continue
			if self._contains_all_terms(page_id, normal_terms):
				results.append(result_id)
		self._process_results(results, terms)
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
				"description": description
			}
			metas.append(meta)
		return metas
		
	@dbus.service.method(dbus_interface=SEARCH_IFACE,
						in_signature='sasu', out_signature='')
	def ActivateResult(self, identifier, terms, timestamp):
		"""Handles the user choosing a search result from those offered."""
		notebook_id, page_id, create = self._from_result_id(identifier)
		server = self._get_server()
		notebook = self._load_notebook(notebook_id)
		gui = server.get_notebook(notebook)
		gui.present(page=page_id)
		# for the create case,
		# could also do
		# gui.new_page_from_text(" ".join(terms), open_page=True)
	
	@dbus.service.method(dbus_interface=SEARCH_IFACE,
						in_signature='asu', out_signature='')
	def LaunchSearch(self, terms, timestamp):
		"""Handles the user choosing the app icon on the left of the results.

		This is supposed to launch the application itself, with the search terms already typed in.

		"""
		server = self._get_server()
		gui = server.get_notebook(self.notebook)
		gui.present()
		gui.show_search(" ".join(terms))
		# FIXME: is it possible to make the GUI search all notebooks too?

	def _process_results(self, results, terms):
		"""Post-processing of the results set.

		This adds extra "New page" results for all matching notebooks, or the default notebook if there were no notebook terms.

		The new-page results are only appended if there are no preexising entries in the results.

		"""

		if len(results) > 0:
			return

		if not self.notebook:
			return

		notebook_terms, normal_terms = self._process_terms(terms)
		page_id = " ".join(normal_terms)

		if notebook_terms:
			import zim.notebook
			notebook_list = zim.notebook.get_notebook_list()
			for notebook_info in notebook_list:
				notebook_id = notebook_info.name
				if self._contains_all_terms(notebook_id, notebook_terms):
					result_id = self._to_result_id(notebook_id, page_id, create=True)
					results.append(result_id)
			return

		notebook_id = self.notebook.name
		result_id = self._to_result_id(notebook_id, page_id, create=True)
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
				if self._contains_all_terms(notebook_info.name, notebook_terms):
					search_notebooks_info.append(notebook_info)
		elif self.search_all:
			search_notebooks_info.extend(notebook_list)
		else:
			search_notebooks_info.append(self.notebook.info)
			
		for notebook_info in search_notebooks_info:
			yield self._load_notebook(notebook_info.name)

	def _search_notebook(self, search_notebook, terms):
		for page in search_notebook.index.walk():
			if self._contains_all_terms(page.basename, terms):
				yield self._to_result_id(search_notebook.name, page.name)
	
	def _load_notebook(self, notebook_id):
		if notebook_id in self.notebook_cache:
			notebook = self.notebook_cache[notebook_id]
		else:
			import zim.notebook
				
			notebook_list = zim.notebook.get_notebook_list()
			notebook_info = notebook_list.get_by_name(notebook_id)
			if notebook_info:
				notebook, _ = zim.notebook.build_notebook(notebook_info)
				self.notebook_cache[notebook_id] = notebook
		return notebook
			
	def _get_server(self):
		import zim.ipc
		
		zim.ipc.start_server_if_not_running()
		return zim.ipc.ServerProxy()
	
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
			# Py3: use str(x), x.casefold()
			if unicode(term).lower() not in unicode(contents).lower():
				return False
		return True
	
	def _contains_any_term(self, contents, terms):
		for term in terms:
			if unicode(term).lower() in unicode(contents).lower():
				return True
		return False
