import logging
from typing import (
    Dict,
    List,
    Optional,
    TextIO,
    Union,
)

from .bus import Bus
from .formats import arxml
from .formats import dbc
from .formats import kcd
from .formats import sym
from .formats.arxml import AutosarDatabaseSpecifics
from .formats.dbc import DbcSpecifics
from .internal_database import InternalDatabase
from .message import Message
from .node import Node
from ...compat import fopen
from ...typechecking import StringPathLike

LOGGER = logging.getLogger(__name__)


class Database(object):
    """This class contains all messages, signals and definitions of a CAN
    network.

    The factory functions :func:`load()<cantools.database.load()>`,
    :func:`load_file()<cantools.database.load_file()>` and
    :func:`load_string()<cantools.database.load_string()>` returns
    instances of this class.

    If `strict` is ``True`` an exception is raised if any signals are
    overlapping or if they don't fit in their message.

    """

    def __init__(self,
                 messages: Optional[List[Message]] = None,
                 nodes: Optional[List[Node]] = None,
                 buses: Optional[List[Bus]] = None,
                 version: Optional[str] = None,
                 dbc_specifics: Optional[DbcSpecifics] = None,
                 autosar_specifics: Optional[AutosarDatabaseSpecifics] = None,
                 frame_id_mask: Optional[int] = None,
                 strict: bool = True,
                 ) -> None:
        self._messages = messages or []
        self._nodes = nodes or []
        self._buses = buses or []
        self._name_to_message: Dict[str, Message] = {}
        self._frame_id_to_message: Dict[int, Message] = {}
        self._version = version
        self._dbc = dbc_specifics
        self._autosar = autosar_specifics

        if frame_id_mask is None:
            frame_id_mask = 0xffffffff

        self._frame_id_mask = frame_id_mask
        self._strict = strict
        self.refresh()

    @property
    def messages(self) -> List[Message]:
        """A list of messages in the database.

        Use :meth:`.get_message_by_frame_id()` or
        :meth:`.get_message_by_name()` to find a message by its frame
        id or name.

        """

        return self._messages

    @property
    def nodes(self) -> List[Node]:
        """A list of nodes in the database.

        """

        return self._nodes

    @property
    def buses(self) -> List[Bus]:
        """A list of CAN buses in the database.

        """

        return self._buses

    @property
    def version(self) -> Optional[str]:
        """The database version, or ``None`` if unavailable.

        """

        return self._version

    @version.setter
    def version(self, value: Optional[str]) -> None:
        self._version = value

    @property
    def dbc(self) -> Optional[DbcSpecifics]:
        """An object containing dbc specific properties like e.g. attributes.

        """

        return self._dbc

    @dbc.setter
    def dbc(self, value: Optional[DbcSpecifics]) -> None:
        self._dbc = value

    @property
    def autosar(self) -> Optional[AutosarDatabaseSpecifics]:
        """An object containing AUTOSAR specific properties like e.g. attributes.

        """

        return self._autosar

    @autosar.setter
    def autosar(self, value: Optional[AutosarDatabaseSpecifics]) -> None:
        self._autosar = value

    def add_arxml(self, fp: TextIO) -> None:
        """Read and parse ARXML data from given file-like object and add the
        parsed data to the database.

        """

        self.add_arxml_string(fp.read())

    def add_arxml_file(self,
                       filename: StringPathLike,
                       encoding: str = 'utf-8') -> None:
        """Open, read and parse ARXML data from given file and add the parsed
        data to the database.

        `encoding` specifies the file encoding.

        """

        with fopen(filename, 'r', encoding=encoding) as fin:
            self.add_arxml(fin)

    def add_arxml_string(self, string: str) -> None:
        """Parse given ARXML data string and add the parsed data to the
        database.

        """

        database = arxml.load_string(string, self._strict)

        self._messages += database.messages
        self._nodes = database.nodes
        self._buses = database.buses
        self._version = database.version
        self._dbc = database.dbc
        self._autosar = database.autosar
        self.refresh()

    def add_dbc(self, fp: TextIO) -> None:
        """Read and parse DBC data from given file-like object and add the
        parsed data to the database.

        >>> db = cantools.database.Database()
        >>> with open ('foo.dbc', 'r') as fin:
        ...     db.add_dbc(fin)

        """

        self.add_dbc_string(fp.read())

    def add_dbc_file(self,
                     filename: StringPathLike,
                     encoding: str = 'cp1252') -> None:
        """Open, read and parse DBC data from given file and add the parsed
        data to the database.

        `encoding` specifies the file encoding.

        >>> db = cantools.database.Database()
        >>> db.add_dbc_file('foo.dbc')

        """

        with fopen(filename, 'r', encoding=encoding) as fin:
            self.add_dbc(fin)

    def add_dbc_string(self, string: str) -> None:
        """Parse given DBC data string and add the parsed data to the
        database.

        >>> db = cantools.database.Database()
        >>> with open ('foo.dbc', 'r') as fin:
        ...     db.add_dbc_string(fin.read())

        """

        database = dbc.load_string(string, self._strict)

        self._messages += database.messages
        self._nodes = database.nodes
        self._buses = database.buses
        self._version = database.version
        self._dbc = database.dbc
        self.refresh()

    def add_kcd(self, fp: TextIO) -> None:
        """Read and parse KCD data from given file-like object and add the
        parsed data to the database.

        """

        self.add_kcd_string(fp.read())

    def add_kcd_file(self,
                     filename: StringPathLike,
                     encoding: str = 'utf-8') -> None:
        """Open, read and parse KCD data from given file and add the parsed
        data to the database.

        `encoding` specifies the file encoding.

        """

        with fopen(filename, 'r', encoding=encoding) as fin:
            self.add_kcd(fin)

    def add_kcd_string(self, string: str) -> None:
        """Parse given KCD data string and add the parsed data to the
        database.

        """

        database = kcd.load_string(string, self._strict)

        self._messages += database.messages
        self._nodes = database.nodes
        self._buses = database.buses
        self._version = database.version
        self._dbc = database.dbc
        self.refresh()

    def add_sym(self, fp: TextIO) -> None:
        """Read and parse SYM data from given file-like object and add the
        parsed data to the database.

        """

        self.add_sym_string(fp.read())

    def add_sym_file(self,
                     filename: StringPathLike,
                     encoding: str = 'utf-8') -> None:
        """Open, read and parse SYM data from given file and add the parsed
        data to the database.

        `encoding` specifies the file encoding.

        """

        with fopen(filename, 'r', encoding=encoding) as fin:
            self.add_sym(fin)

    def add_sym_string(self, string: str) -> None:
        """Parse given SYM data string and add the parsed data to the
        database.

        """

        database = sym.load_string(string, self._strict)

        self._messages += database.messages
        self._nodes = database.nodes
        self._buses = database.buses
        self._version = database.version
        self._dbc = database.dbc
        self.refresh()

    def _add_message(self, message: Message) -> None:
        """Add given message to the database.

        """

        if message.name in self._name_to_message:
            LOGGER.warning("Overwriting message '%s' with '%s' in the "
                           "name to message dictionary.",
                           self._name_to_message[message.name].name,
                           message.name)

        masked_frame_id = (message.frame_id & self._frame_id_mask)

        if masked_frame_id in self._frame_id_to_message:
            LOGGER.warning(
                "Overwriting message '%s' with '%s' in the frame id to message "
                "dictionary because they have identical masked frame ids 0x%x.",
                self._frame_id_to_message[masked_frame_id].name,
                message.name,
                masked_frame_id)

        self._name_to_message[message.name] = message
        self._frame_id_to_message[masked_frame_id] = message

    def as_dbc_string(self) -> str:
        """Return the database as a string formatted as a DBC file.

        """

        return dbc.dump_string(InternalDatabase(self._messages,
                                                self._nodes,
                                                self._buses,
                                                self._version,
                                                self._dbc))

    def as_kcd_string(self) -> str:
        """Return the database as a string formatted as a KCD file.

        """

        return kcd.dump_string(InternalDatabase(self._messages,
                                                self._nodes,
                                                self._buses,
                                                self._version,
                                                self._dbc))

    def get_message_by_name(self, name: str) -> Message:
        """Find the message object for given name `name`.

        """

        return self._name_to_message[name]

    def get_message_by_frame_id(self, frame_id: int) -> Message:
        """Find the message object for given frame id `frame_id`.

        """

        return self._frame_id_to_message[frame_id & self._frame_id_mask]

    def get_node_by_name(self, name: str) -> Node:
        """Find the node object for given name `name`.

        """

        for node in self._nodes:
            if node.name == name:
                return node

        raise KeyError(name)

    def get_bus_by_name(self, name: str) -> Bus:
        """Find the bus object for given name `name`.

        """

        for bus in self._buses:
            if bus.name == name:
                return bus

        raise KeyError(name)

    def encode_message(self,
                       frame_id_or_name: Union[int, str],
                       data: Dict[str, float],
                       scaling: bool = True,
                       padding: bool = False,
                       strict: bool = True,
                       ) -> bytes:
        """Encode given signal data `data` as a message of given frame id or
        name `frame_id_or_name`. `data` is a dictionary of signal
        name-value entries.

        If `scaling` is ``False`` no scaling of signals is performed.

        If `padding` is ``True`` unused bits are encoded as 1.

        If `strict` is ``True`` all signal values must be within their
        allowed ranges, or an exception is raised.

        >>> db.encode_message(158, {'Bar': 1, 'Fum': 5.0})
        b'\\x01\\x45\\x23\\x00\\x11'
        >>> db.encode_message('Foo', {'Bar': 1, 'Fum': 5.0})
        b'\\x01\\x45\\x23\\x00\\x11'

        """

        if isinstance(frame_id_or_name, int):
            message = self._frame_id_to_message[frame_id_or_name]
        elif isinstance(frame_id_or_name, str):
            message = self._name_to_message[frame_id_or_name]
        else:
            raise ValueError(f"Invalid frame_id_or_name '{frame_id_or_name}'")

        return message.encode(data, scaling, padding, strict)

    def decode_message(self,
                       frame_id_or_name: Union[int, str],
                       data: bytes,
                       decode_choices: bool = True,
                       scaling: bool = True,
                       ) -> Dict[str, Union[float, str]]:
        """Decode given signal data `data` as a message of given frame id or
        name `frame_id_or_name`. Returns a dictionary of signal
        name-value entries.

        If `decode_choices` is ``False`` scaled values are not
        converted to choice strings (if available).

        If `scaling` is ``False`` no scaling of signals is performed.

        >>> db.decode_message(158, b'\\x01\\x45\\x23\\x00\\x11')
        {'Bar': 1, 'Fum': 5.0}
        >>> db.decode_message('Foo', b'\\x01\\x45\\x23\\x00\\x11')
        {'Bar': 1, 'Fum': 5.0}

        """

        if isinstance(frame_id_or_name, int):
            message = self._frame_id_to_message[frame_id_or_name]
        elif isinstance(frame_id_or_name, str):
            message = self._name_to_message[frame_id_or_name]
        else:
            raise ValueError(f"Invalid frame_id_or_name '{frame_id_or_name}'")

        return message.decode(data, decode_choices, scaling)

    def refresh(self) -> None:
        """Refresh the internal database state.

        This method must be called after modifying any message in the
        database to refresh the internal lookup tables used when
        encoding and decoding messages.

        """

        self._name_to_message = {}
        self._frame_id_to_message = {}

        for message in self._messages:
            message.refresh(self._strict)
            self._add_message(message)

    def __repr__(self) -> str:
        lines = ["version('{}')".format(self._version), '']

        if self._nodes:
            for node in self._nodes:
                lines.append(repr(node))

            lines.append('')

        for message in self._messages:
            lines.append(repr(message))

            for signal in message.signals:
                lines.append('  ' + repr(signal))

            lines.append('')

        return '\n'.join(lines)
