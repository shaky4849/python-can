#!/usr/bin/env python
# coding: utf-8

"""
This module contains the implementation of :class:`can.Message`.

.. note::
    Could use `@dataclass <https://docs.python.org/3.7/library/dataclasses.html>`__
    starting with Python 3.7.
"""

import logging


class Message(object):
    """
    The :class:`~can.Message` object is used to represent CAN messages for
    sending, receiving and other purposes like converting between different
    logging formats.

    Messages can use extended identifiers, be remote or error frames, contain
    data and can be associated to a channel.

    When testing for equality of messages, the timestamp and the channel
    are not used for comparing.
    """

    def __init__(self, timestamp=0.0, arbitration_id=0, extended_id=True,
                 is_remote_frame=False, is_error_frame=False, channel=None,
                 dlc=None, data=None,
                 is_fd=False, bitrate_switch=False, error_state_indicator=False,
                 check=False):
        """
        To create a message object, simply provide any of the below attributes
        toghether with additional parameters as keyword arguments to the constructor.

        :param bool check: By default, the constructor of this class does not strictly check the input.
                           Thus, the caller must prevent the creation of invalid messages or
                           set this parameter to `True`, to raise an Error on invalid inputs.
                           Possible problems include the `dlc` field not matching the length of `data`
                           or creating a message with both `is_remote_frame` and `is_error_frame` set to `True`.

        :raises ValueError: iff `check` is set to `True` and one or more arguments were invalid
        """

        self.timestamp = timestamp
        self.arbitration_id = arbitration_id
        self.id_type = extended_id  # deprecated
        self.is_extended_id = extended_id

        self.is_remote_frame = is_remote_frame
        self.is_error_frame = is_error_frame
        self.channel = channel

        self.is_fd = is_fd
        self.bitrate_switch = bitrate_switch
        self.error_state_indicator = error_state_indicator

        if data is None or is_remote_frame:
            self.data = bytearray()
        elif isinstance(data, bytearray):
            self.data = data
        else:
            try:
                self.data = bytearray(data)
            except TypeError:
                err = "Couldn't create message from {} ({})".format(data, type(data))
                raise TypeError(err)

        if dlc is None:
            self.dlc = len(self.data)
        else:
            self.dlc = dlc

        if check:
            self._check()

    def __str__(self):
        field_strings = ["Timestamp: {0:>15.6f}".format(self.timestamp)]
        if self.is_extended_id:
            arbitration_id_string = "ID: {0:08x}".format(self.arbitration_id)
        else:
            arbitration_id_string = "ID: {0:04x}".format(self.arbitration_id)
        field_strings.append(arbitration_id_string.rjust(12, " "))

        flag_string = " ".join([
            "X" if self.is_extended_id else "S",
            "E" if self.is_error_frame else " ",
            "R" if self.is_remote_frame else " ",
            "F" if self.is_fd else " ",
            "BS" if self.bitrate_switch else "  ",
            "EI" if self.error_state_indicator else "  "
        ])

        field_strings.append(flag_string)

        field_strings.append("DLC: {0:d}".format(self.dlc))
        data_strings = []
        if self.data is not None:
            for index in range(0, min(self.dlc, len(self.data))):
                data_strings.append("{0:02x}".format(self.data[index]))
        if data_strings: # if not empty
            field_strings.append(" ".join(data_strings).ljust(24, " "))
        else:
            field_strings.append(" " * 24)

        if (self.data is not None) and (self.data.isalnum()):
            try:
                field_strings.append("'{}'".format(self.data.decode('utf-8')))
            except UnicodeError:
                pass

        if self.channel is not None:
            field_strings.append("Channel: {}".format(self.channel))

        return "    ".join(field_strings).strip()

    def __len__(self):
        return len(self.data)

    def __bool__(self):
        return True

    def __nonzero__(self):
        return self.__bool__()

    def __repr__(self):
        args = ["timestamp={}".format(self.timestamp),
                "arbitration_id={:#x}".format(self.arbitration_id),
                "extended_id={}".format(self.is_extended_id)]

        if self.is_remote_frame:
            args.append("is_remote_frame={}".format(self.is_remote_frame))

        if self.is_error_frame:
            args.append("is_error_frame={}".format(self.is_error_frame))

        if self.channel is not None:
            args.append("channel={!r}".format(self.channel))                

        data = ["{:#02x}".format(byte) for byte in self.data]
        args += ["dlc={}".format(self.dlc),
                "data=[{}]".format(", ".join(data))]

        if self.is_fd:
            args.append("is_fd=True")
            args.append("bitrate_switch={}".format(self.bitrate_switch))
            args.append("error_state_indicator={}".format(self.error_state_indicator))

        return "can.Message({})".format(", ".join(args))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                #self.timestamp == other.timestamp and # allow the timestamp to differ
                self.arbitration_id == other.arbitration_id and
                self.is_extended_id == other.is_extended_id and
                self.is_remote_frame == other.is_remote_frame and
                self.is_error_frame == other.is_error_frame and
                self.channel == other.channel and
                self.dlc == other.dlc and
                self.data == other.data and
                self.is_fd == other.is_fd and
                self.bitrate_switch == other.bitrate_switch and
                self.error_state_indicator == other.error_state_indicator
            )
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        else:
            return NotImplemented

    def __hash__(self):
        return hash((
            self.arbitration_id,
            # self.timestamp # excluded, like in self.__eq__(self, other)
            self.is_extended_id,
            self.dlc,
            self.data,
            self.is_fd,
            self.bitrate_switch,
            self.is_remote_frame,
            self.is_error_frame
        ))

    def __format__(self, format_spec):
        if not format_spec:
            return self.__str__()
        else:
            raise ValueError('non empty format_specs are not supported')

    def __bytes__(self):
        return bytes(self.data)

    def _check(self):
        """Checks if the message parameters are valid.

        :raises ValueError: iff one or more attributes are invalid
        """
        # TODO add checks
        if is_fd and self.dlc > 64:
            logger.warning("data link count was %d but it should be less than or equal to 64", self.dlc)
        if not is_fd and self.dlc > 8:
            logger.warning("data link count was %d but it should be less than or equal to 8", self.dlc)
