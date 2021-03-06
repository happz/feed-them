"""
Logging support.

Sets up logging environment for use by ``gluetool`` and modules. Based
on standard library's :py:mod:`logging` module, augmented a bit to
support features loke colorized messages and stackable context information.

Example usage:

.. code-block:: python

   # initialize logger as soon as possible
   logger = Logging.create_logger()

   # now it's possible to use it for logging:
   logger.debug('foo!')

   # or connect it with current instance (if you're doing all this
   # inside some class' constructor):
   logger.connect(self)

   # now you can access logger's methods directly:
   self.debug('foo once again!')

   # find out what your logging should look like, e.g. by parsing command-line options
   ...

   # tell logger about the final setup
   logger = Logging.create_logger(output_file='/tmp/foo.log', level=..., colors=True)

   # and, finally, create a root context logger - when we create another loggers during
   # the code flow, this context logger will be in the root of this tree of loggers.
   logger = ContextAdapter(logger)

   # don't forget to re-connect with the context logger if you connected your instance
   # with previous logger, to make sure helpers are set correctly
   logger.connect(self)
"""

import atexit
import json
import logging
import traceback

import click
import jinja2


BLOB_HEADER = '---v---v---v---v---v---'
BLOB_FOOTER = '---^---^---^---^---^---'


_TRACEBACK_TEMPLATE = """
{%- set label = '{}:'.format(label) %}
---v---v---v---v---v--- {{ label | center(10) }} ---v---v---v---v---v---

{{ exception.__class__.__module__ }}.{{ exception.__class__.__name__ }}: {{ exception.message }}

{{ traceback }}
---^---^---^---^---^---^----------^---^---^---^---^---^---
"""


class BlobLogger(object):
    """
    Context manager to help with "real time" logging - some code may produce output continuously,
    e.g. when running a command and streaming its output to our stdout, and yet we still want to
    wrap it with boundaries and add a header.

    This code:

    .. code-block:: python

       with BlobLogger('ls of root', outro='end of ls'):
           subprocess.call(['ls', '/'])

    will lead to the output similar to this:


    .. code-block:: bash

       [20:30:50] [+] ---v---v---v---v---v--- ls of root
       bin  boot  data  dev ...
       [20:30:50] [+] ---^---^---^---^---^--- end of ls

    .. note::

       When you already hold the data you wish to log, please use :py:func:`gluetool.log.log_blob`
       or :py:func:`gluetool.log.log_dict`. The example above could be rewritten using ``log_blob``
       by using :py:meth:`subprocess.check_output` and passing its return value to ``log_blob``.
       ``BlobLogger`` is designed to wrap output whose creation caller don't want to (or cannot)
       control.

    :param str intro: Label to show what is the meaning of the logged data.
    :param str outro: Label to show by the final boundary to mark the end of logging.
    :param callable on_finally: When set, it will be called in ``__exit__`` method. User of
        this context manager might need to flush used streams or close resources even in case
        the exception was raised while inside the context manager. ``on_finally`` is called
        with all arguments the ``__exit__`` was called, and its return value is returned by
        ``__exit__`` itself, therefore it can examine possible exceptions, and override them.
    :param callable writer: A function which is used to actually log the text. Usually a one of some logger methods.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, intro, outro=None, on_finally=None, writer=None):
        self.writer = Logging.get_logger().info if writer is None else writer

        self.intro = intro
        self.outro = outro
        self.on_finally = on_finally

    def __enter__(self):
        self.writer('{} {}'.format(BLOB_HEADER, self.intro))

    def __exit__(self, *args, **kwargs):
        self.writer('{} {}'.format(BLOB_FOOTER, self.outro or ''))

        if self.on_finally:
            return self.on_finally(*args, **kwargs)


def format_dict(dictionary):
    """
    Format a Python data structure for printing. Uses :py:func:`json.dumps` formatting
    capabilities to present readable representation of a given structure.
    """

    # Use custom "default" handler, to at least encode obj's repr() output when
    # json encoder does not know how to encode such class
    def default(obj):
        return repr(obj)

    return json.dumps(dictionary, sort_keys=True, indent=4, separators=(',', ': '), default=default)


def log_dict(writer, intro, data):
    """
    Log structured data, e.g. JSON responses or a Python ``list``.

    .. note::

       For logging unstructured "blobs" of text, use :py:func:`gluetool.log.log_blob`. It does not
       attempt to format the output, and wraps it by header and footer to mark its boundaries.

    .. note::

       Using :py:func:`gluetool.log.format_dict` directly might be shorter, depending on your your code.
       For example, this code:

       .. code-block:: python

          self.debug('Some data:\\n{}'.format(format_dict(data)))

       is equivalent to:

       .. code-block:: python

          log_dict(self.debug, 'Some data', data)

       If you need more formatting, or you wish to fit more information into a single message, using
       logger methods with ``format_dict`` is a way to go, while for logging a single structure ``log_dict``
       is more suitable.

    :param callable writer: A function which is used to actually log the text. Usually a one of some logger methods.
    :param str intro: Label to show what is the meaning of the logged structure.
    :param str blob: The actual data to log.
    """

    writer('{}:\n{}'.format(intro, format_dict(data)))


def log_blob(writer, intro, blob):
    """
    Log "blob" of characters of unknown structure, e.g. output of a command or response
    of a HTTP request. The blob is preceded by a header and followed by a footer to mark
    exactly the blob boundaries.

    .. note::

       For logging structured data, e.g. JSON or Python structures, use :py:func:`gluetool.log.log_dict`. It will
       make structure of the data more visible, resulting in better readability of the log.

    :param callable writer: A function which is used to actually log the text. Usually a one of some logger methods.
    :param str intro: Label to show what is the meaning of the logged blob.
    :param str blob: The actual blob of text.
    """

    writer("{}:\n{}\n{}\n{}".format(intro, BLOB_HEADER, blob, BLOB_FOOTER))


def log_xml(writer, intro, element):
    """
    Log an XML element, e.g. Beaker job description.

    :param callable writer: A function which is used to actually log the text. Usually a one of some logger methods.
    :param str intro: Label to show what is the meaning of the logged blob.
    :param element: XML element to log.
    """

    writer("{}:\n{}".format(intro, element.prettify(encoding='utf-8')))


class ContextAdapter(logging.LoggerAdapter):
    """
    Generic logger adapter that collects "contexts", and prepends them
    to the message.

    "context" is any key in ``extra`` dictionary starting with ``ctx_``,
    whose value is expected to be tuple of ``(priority, value)``. Contexts
    are then sorted by their priorities before inserting them into the message
    (lower priority means context will be placed closer to the beggining of
    the line - highest priority comes last.

    :param logging.Logger logger: parent logger this adapter modifies.
    :param dict extras: additional extra keys passed to the parent class.
        The dictionary is then used to update messages' ``extra`` key with
        the information about context.
    """

    def __init__(self, logger, extra=None):
        super(ContextAdapter, self).__init__(logger, extra or {})

        self.warn = self.warning

    def process(self, msg, kwargs):
        """
        Original ``process`` overwrites ``kwargs['extra']`` which doesn't work
        for us - we want to chain adapters, getting more and more contexts
        on the way. Therefore ``update`` instead of assignment.
        """

        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        kwargs['extra'].update(self.extra)
        return msg, kwargs

    def connect(self, parent):
        """
        Create helper methods in ``parent``, by assigning adapter's methods to its
        attributes. One can then call ``parent.debug`` and so on, instead of less
        readable ``parent.logger.debug``.

        Simply instantiate adapter and call its ``connect`` with an object as
        a ``parent`` argument, and the object will be enhanced with all these
        logging helpers.

        :param parent: object to enhance with logging helpers.
        """

        parent.debug = self.debug
        parent.info = self.info
        parent.warn = self.warning
        parent.error = self.error
        parent.exception = self.exception


class ModuleAdapter(ContextAdapter):
    """
    Custom logger adapter, adding module name as a context.

    :param logging.Logger logger: parent logger this adapter modifies.
    :param gluetool.glue.Module module: module whose name is added as a context.
    """

    def __init__(self, logger, module):
        super(ModuleAdapter, self).__init__(logger, {'ctx_module_name': (10, module.unique_name)})


class LoggingFormatter(logging.Formatter):
    """
    Custom log record formatter. Produces output in form of:

    ``[stamp] [level] [ctx1] [ctx2] ... message``

    :param bool log_tracebacks: if set, add tracebacks to the message. By default,
        we don't need tracebacks on the terminal, unless its loglevel is verbose enough,
        but we want them in the debugging file.
    """

    #: Tags used to express loglevel.
    _level_tags = {
        logging.DEBUG: 'D',
        logging.INFO: '+',
        logging.WARNING: 'W',
        logging.ERROR: 'E',
        logging.CRITICAL: 'C'
    }

    #: Colors assigned to loglevels
    _level_color = {
        logging.INFO: dict(fg='green'),
        logging.WARNING: dict(fg='yellow'),
        logging.ERROR: dict(fg='red'),
        logging.CRITICAL: dict(fg='red')
    }

    def __init__(self, log_tracebacks=False):
        super(LoggingFormatter, self).__init__()

        self.log_tracebacks = log_tracebacks

    @staticmethod
    def _format_exception_chain(exc_info):
        tmpl = jinja2.Template(_TRACEBACK_TEMPLATE)

        output = ['']

        def _add_block(label, exc, trace):
            output.append(tmpl.render(label=label, exception=exc, traceback=''.join(traceback.format_tb(trace))))

        # don't unpack traceback - it might lead to a circular reference, leaving this frame
        # uncollectable
        _add_block('Exception', exc_info[1], exc_info[2])

        while getattr(exc_info[1], 'caused_by', None) is not None:
            exc_info = exc_info[1].caused_by

            _add_block('Caused by', exc_info[1], exc_info[2])

        return '\n'.join(output)

    def format(self, record):
        """
        Format a logging record. It puts together pieces like time stamp,
        log level, possibly also different contexts if there are any stored
        in the record, and finally applies colors if asked to do so.

        :param logging.LogRecord record: record describing the event.
        :rtype: str
        :returns: string representation of the event record.
        """

        fmt = ['[{stamp}]', '[{level}]', '{msg}']
        values = {
            'stamp': self.formatTime(record, datefmt='%H:%M:%S'),
            'level': LoggingFormatter._level_tags[record.levelno],
            'msg': record.getMessage()
        }

        if record.exc_info \
                and (self.log_tracebacks is True or Logging.stderr_handler.level == logging.DEBUG):
            fmt.append('{exc_text}')
            values['exc_text'] = LoggingFormatter._format_exception_chain(record.exc_info)

        # List all context properties of record
        ctx_properties = [prop for prop in dir(record) if prop.startswith('ctx_')]

        if ctx_properties:
            # Sorting them in reverse order of priorities - we're goign to insert
            # their values into `fmt`, so the highest priority context must be
            # inserted as the last one.
            sorted_ctxs = sorted(ctx_properties, key=lambda x: getattr(record, x)[0], reverse=True)

            for name in sorted_ctxs:
                _, value = getattr(record, name)

                fmt.insert(2, '[{%s}]' % name)
                values[name] = value

        return click.style(' '.join(fmt).format(**values), **self._level_color[record.levelno])


class Logging(object):
    """
    Container wrapping configuration and access to :py:mod:`logging` infrastructure ``gluetool``
    uses for logging.
    """

    #: Logger singleton - if anyone asks for a logger, they will get this one. Needs
    #: to be properly initialized by calling :py:meth:`create_logger`.
    logger = None

    #: Stream handler printing out to stderr.
    stderr_handler = None

    #: If enabled, handles output to catch-everything file.
    output_file = None
    output_file_handler = None

    @staticmethod
    def _close_output_file():
        """
        If opened, close output file used for logging.

        This method is registered with :py:mod:`atexit`.
        """

        if Logging.output_file_handler is None:
            return

        Logging.get_logger().debug("closing output file '{}'".format(Logging.output_file))

        Logging.output_file_handler.flush()
        Logging.output_file_handler.close()
        Logging.output_file_handler = None

    @staticmethod
    def get_logger():
        """
        Returns a logger instance.

        Expects there was a call to :py:meth:`create_logger` method before calling this method
        that would actually create and set up the logger.

        :rtype: logging.Logger
        :returns: a :py:class:`logging.Logger` instance, set up for logging, or ``None`` when there's
            no logger yet.
        """

        return Logging.logger

    @staticmethod
    def create_logger(output_file=None, level=logging.INFO):
        """
        Create and setup logger.

        This method is called at least twice:

          - when :py:class:`gluetool.glue.Glue` is instantiated: only a ``stderr`` handler is set up,
            with loglevel being ``INFO``;
          - when all arguments and options are processed, and Glue instance can determine desired
            log level, whether it's expected to stream debugging messages into a file, etc. This
            time, method only modifies propagates necessary updates to already existing logger.

        :param str output_file: if set, new handler will be attached to the logger, streaming
            messages of **all** log levels into this this file.
        :param int level: desired log level. One of constants defined in :py:mod:`logging` module,
            e.g. :py:data:`logging.DEBUG` or :py:data:`logging.ERROR`.
        :rtype: logging.Logger
        :returns: a :py:class:`logging.Logger` instance, set up for logging.
        """

        level = level or logging.INFO

        if Logging.logger is None:
            logger = Logging.logger = logging.getLogger('gluetool')

            logger.propagate = False

            # logger actually emits everything, handlers do filtering
            logger.setLevel(logging.DEBUG)

            # stderr handler
            Logging.stderr_handler = handler = logging.StreamHandler()
            handler.setLevel(level)
            handler.setFormatter(LoggingFormatter())
            logger.addHandler(handler)

        else:
            logger = Logging.logger

            # set log level to new value
            Logging.stderr_handler.setLevel(level)
            Logging.stderr_handler.setFormatter(LoggingFormatter())

        if output_file is not None:
            # catch-everything file requested
            handler = logging.FileHandler(output_file, 'w')
            handler.setLevel(logging.DEBUG)

            formatter = LoggingFormatter(log_tracebacks=True)
            formatter.log_tracebacks = True
            handler.setFormatter(formatter)

            logger.addHandler(handler)

            # Overwrites previously set output files (not our case but worth mentioning...)
            Logging.output_file = output_file
            Logging.output_file_handler = handler

            logger.debug("created output file '{}'".format(output_file))

            atexit.register(Logging._close_output_file)

        logger.debug("logger set up: output_file='{}', level={}".format(output_file, level))

        return logger
