import builtins

from shapely.extension.functional.execution import ExecutionEngine
from shapely.extension.functional.pipeline import Sequence
from shapely.extension.functional.util import is_primitive


class Stream(object):
    """
    Represents and implements a stream which separates the responsibilities of Sequence and
    ExecutionEngine.

    An instance of Stream is normally accessed as `seq`
    """

    def __init__(self, disable_compression=False, max_repr_items=100):
        """
        Default stream constructor.
        :param disable_compression: Disable file compression detection
        """
        self.disable_compression = disable_compression
        self.max_repr_items = max_repr_items

    def __call__(self, *args, **kwargs):
        """
        Create a Sequence using a sequential ExecutionEngine.

        If args has more than one argument then the argument list becomes the sequence.

        If args[0] is primitive, a sequence wrapping it is created.

        If args[0] is a list, tuple, iterable, or Sequence it is wrapped as a Sequence.

        :param args: Sequence to wrap
        :return: Wrapped sequence
        """
        # pylint: disable=no-self-use
        engine = ExecutionEngine()
        return self._parse_args(
            args, engine, "seq() takes at least 1 argument ({0} given)"
        )

    def _parse_args(self, args, engine, error_message):
        if len(args) == 0:
            raise TypeError(error_message.format(len(args)))
        if len(args) == 1:
            try:
                if type(args[0]).__name__ == "DataFrame":
                    import pandas

                    if isinstance(args[0], pandas.DataFrame):
                        return Sequence(
                            args[0].values,
                            engine=engine,
                            max_repr_items=self.max_repr_items,
                        )
            except ImportError:  # pragma: no cover
                pass

        if len(args) > 1:
            return Sequence(
                list(args), engine=engine, max_repr_items=self.max_repr_items
            )
        elif is_primitive(args[0]):
            return Sequence(
                [args[0]], engine=engine, max_repr_items=self.max_repr_items
            )
        else:
            return Sequence(args[0], engine=engine, max_repr_items=self.max_repr_items)

    def range(self, *args):
        """
        Alias to range function where seq.range(args) is equivalent to seq(range(args)).

        >>> seq.range(1, 8, 2)
        [1, 3, 5, 7]

        :param args: args to range function
        :return: range(args) wrapped by a sequence
        """
        return self(builtins.range(*args))  # pylint: disable=no-member


# pylint: disable=invalid-name
seq = Stream()

