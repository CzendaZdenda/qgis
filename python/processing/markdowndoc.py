#! /usr/bin/env python

"""
markdowndoc.py

Written by Patrick Laban and Geremy Condra

Licensed under GPLv3

Released 28 April 2009

This module contains a simple class to output Markdown-style
pydocs.

Modified to "work" under python 2.6
"""

import pydoc, inspect, re
import future_builtins as builtins

class MarkdownDoc(pydoc.TextDoc):

	underline = "*" * 40

	def process_docstring(self, obj):
		"""Get the docstring and turn it into a list."""
		docstring = pydoc.getdoc(obj)
		if docstring:
			return docstring + "\n\n"
		return ""

	def process_class_name(self, name, bases, module):
		"""Format the class's name and bases."""
		title = "## class " + self.bold(name)
		if bases:
			# get the names of each of the bases
			base_titles = [pydoc.classname(base, module) for base in bases]
			# if its not just object
			if len(base_titles) > 1:
				# append the list to the title
				title += "(%s)" % ", ".join(base_titles)
		return title

	def process_subsection(self, name):
		"""format the subsection as a header"""
		return "### " + name

	def docclass(self, cls, name=None, mod=None):
		"""Produce text documentation for the class object cls."""

		# the overall document, as a line-delimited list
		document = []

		# get the object's actual name, defaulting to the passed in name
		name = name or cls.__name__

		# get the object's bases
		bases = cls.__bases__

		# get the object's module
		mod = cls.__module__

		# get the object's MRO
		mro = [pydoc.classname(base, mod) for base in inspect.getmro(cls)]

		# get the object's classname, which should be printed
		classtitle = self.process_class_name(name, bases, mod)
		document.append(classtitle)
		document.append(self.underline)

		# get the object's docstring, which should be printed
		docstring = self.process_docstring(cls)
		document.append(docstring)

		# get all the attributes of the class
		attrs = []
		for name, kind, classname, value in pydoc.classify_class_attrs(cls):
			if pydoc.visiblename(name):
                    #if kind is not builtins.object:
					if classname == cls:
						obj = (name, kind, classname, value)
						attrs.append(obj)
		
		# sort them into categories
		data = [attr for attr in attrs if attr[1] == "data"]
		descriptors = [attr for attr in attrs if attr[1] == "data descriptor"]
		methods = [attr for attr in attrs if "method" in attr[1]]

		# start the data section
		document.append(self.process_subsection("data"))
		document.append(self.underline)

		# process your attributes
		for name, kind, classname, value in data:
			document.append(self.document(getattr(cls, name), name, mod, cls))

		# start the descriptors section
		document.append(self.process_subsection("descriptors"))
		document.append(self.underline)

		# process your descriptors
		for desc in descriptors:
			document.append(self._docdescriptor(name, value, mod))

		# start the methods section
		document.append(self.process_subsection("methods"))
		document.append(self.underline)

		# process your methods
		for f in methods:
			if not f[0].startswith("__"):
				document.append(self.docroutine(f[-1]))

		return "\n".join(document)		

	def bold(self, text):
		""" Formats text as bold in markdown. """
		if text.startswith('_') and text.endswith('_'):
			return "__\%s\__" %text
		elif text.startswith('_'):
			return "__\%s__" %text
		elif text.endswith('_'):
			return "__%s\__" %text
		else:
			return "__%s__" %text

	def indent(self, text, prefix=''):
		"""Indent text by prepending a given prefix to each line."""
		return text
    
	def section(self, title, contents):
		"""Format a section with a given heading."""
		clean_contents = self.indent(contents).rstrip()
		return "# " + self.bold(title) + '\n\n' + clean_contents + '\n\n'

	def docroutine(self, object, name=None, mod=None, cl=None):
		"""Produce text documentation for a function or method object."""
		realname = object.__name__
		name = name or realname
		note = ''
		skipdocs = 0
		if inspect.ismethod(object):
			object = object.__func__
		if name == realname:
			title = self.bold(realname)
		else:
			if (cl and realname in cl.__dict__ and cl.__dict__[realname] is object):
				skipdocs = 1
			title = self.bold(name) + ' = ' + realname
		if inspect.isfunction(object):
			argspec = inspect.formatargspec(inspect.getargspec(object))
			if realname == '<lambda>':
				title = self.bold(name) + ' lambda '
				# XXX lambda's won't usually have func_annotations['return']
				# since the syntax doesn't support but it is possible.
				# So removing parentheses isn't truly safe.
				argspec = argspec[1:-1] # remove parentheses
		else:
			argspec = '(...)'
		decl = "#### " + "def " + title + argspec + ':' + '\n' + note

		if skipdocs:
			return decl + '\n'
		else:
			doc = pydoc.getdoc(object) or ''
			return decl + '\n' + (doc and self.indent(doc).rstrip() + '\n')
