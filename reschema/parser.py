from reschema.exceptions import ParseError
from reschema.util import check_type


class Parser(object):
    """ Input object parser. """
    def __init__(self, input, name, obj=None):
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

        if prop in self.input:
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
