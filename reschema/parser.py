# Copyright (c) 2013 Riverbed Technology, Inc.
#
# This software is licensed under the terms and conditions of the
# MIT License set forth at:
#   https://github.com/riverbed/reschema/blob/master/LICENSE ("License").
# This software is distributed "AS IS" as set forth in the License.

import os
import urlparse

from reschema.exceptions import ParseError, InvalidReference
from reschema.util import check_type

import reschema.settings


class Parser(object):
    """ Input object parser. """
    def __init__(self, input, name, obj=None, base_id=None):
        """Create a parser object.

        :param dict input: input to parser
        :param name: name for logging / error
        :param obj: object on which to set attributes

        If obj is None, it may be set later with set_context(), but
        obj may not be altered once set.

        """
        if not isinstance(input, dict):
            raise ParseError('%s: definition should be a dictionary, got: %s' %
                             (name, type(input)), input)

        self.input = input
        self.obj = obj
        self.name = name
        self.parsed_props = set()

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if type is None:
            # parsing was all successful, check that all input keys
            # were parsed
            self.check_input()
            return True

    def set_context(self, name, obj):
        """Set the object to modify when parsing.

        :param name: name for logging / error
        :param obj: object on which to set attributes

        """
        if self.obj is not None:
            raise ParseError('Cannot change object context, '
                             'only set if it was None', input)

        self.obj = obj
        self.name = name

    def parse(self, prop, default_value=None, required=False,
              types=None, save=True, save_as=None):
        """Parse a key from the input dict.

        :param string prop: Property name to extract

        :param default_value: A value to use if the property is missing
            but not required.  Ignored if `required` is True.

        :param bool required: Causes ParseError to be raised if `prop`
            is not in the input

        :param list types: verifies that the property value is an
            instance of at least one of the types passed in this
            parameter.

        :param save: If true, save the property to this parsers
            object, if false, don't save (value is returned)

        :param str save_as: the property name to save as, defaults
            to ``prop``

        :raises reschema.exceptions.ParseError: if the type of the
            data is incorrect or if the property is required but
            missing.

        :return: The parsed value.
        """

        if (  prop == 'description' and
              not reschema.settings.LOAD_DESCRIPTIONS):
            val = ''
            if prop in self.input:
                del(self.input[prop])
                self.parsed_props.add(prop)

        elif prop in self.input:
            val = self.input[prop]
            if types:
                check_type(prop, val, types, self.input)
            self.parsed_props.add(prop)

        elif required:
            raise ParseError(
                "Missing required property '%s'" % prop, self.input)
        else:
            val = default_value

        if save:
            if not self.obj:
                raise ParseError(
                    'Cannot save prop %s, no obj set' % prop, self.input)

            setattr(self.obj, save_as or prop, val)

        return val

    def check_input(self):
        """ Verify that all input properities were parsed. """
        if input is None:
            return

        unparsed = set(self.input.keys()).difference(self.parsed_props)

        if len(unparsed) > 0:
            raise ParseError(
                '%s: unrecognized properties in definition: %s' %
                (self.name, ','.join(unparsed)), list(unparsed)[0])

    @classmethod
    def expand_ref(cls, base_id, ref):
        """ Expand a reference using base_id as a relative base

        Returns a fully qualified reference based.

        :param reference: string reference to resolve

        The `reference` may be one of three supported forms:

           * `<server><path>#<fragment>` - fully qualified reference

           * `<path>#<fragment>` - reference is resolved against the
             same <server> as `base_id`.  <path> starts with '/'

           * `#<fragment>` - reference is resolved against the same
             <server> and <path> as `base_id`

        :raises InvalidReference: `reference` does not appear to
            be to the correct syntax

        """

        parsed_ref = urlparse.urlparse(ref)
        if parsed_ref.netloc:
            # Already a fully qualified address, let urlparse rejoin
            # to normalize it
            return parsed_ref.geturl()

        if ref[0] not in ['/', '#']:
            raise InvalidReference("relative references should "
                                   "start with '#' or '/'",
                                   ref)

        # urljoin will take care of the rest
        return urlparse.urljoin(base_id, ref)

    def preprocess_input(self, base_id):
        """Perform some input preprocessing."""

        self.expand_refs(base_id, self.input)

    def expand_refs(self, base_id, input):
        """ Replace all relative refs in input with absolute refs"""

        if input:
            if isinstance(input, dict):
                if '$ref' in input and isinstance(input['$ref'], basestring):
                    # replace relative refs with fully expanded refs
                    oldref = input['$ref']
                    newref = self.expand_ref(base_id, oldref)
                    input['$ref'] = newref

                elif len(input.keys()) > 0:
                    for k, v in input.iteritems():
                        self.expand_refs(base_id, v)

            elif isinstance(input, list):
                for v in input:
                    self.expand_refs(base_id, v)
