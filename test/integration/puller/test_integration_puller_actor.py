# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Integration test of the puller actor
"""
import pickle

import pytest
import zmq
from mock import patch, Mock

from smartwatts.message import OKMessage, StartMessage, ErrorMessage
from smartwatts.filter import Filter
from smartwatts.dispatcher import DispatcherActor
from smartwatts.database import BaseDB, MongoDB
from smartwatts.puller import PullerActor
from smartwatts.actor import Actor
from test.integration.integration_utils import *

SOCKET_ADDRESS = 'ipc://@test_puller'



@pytest.fixture()
def context():
    return zmq.Context()

##################
# Initialisation #
##################

@patch('smartwatts.database.base_db.BaseDB.load', side_effect=gen_side_effect(
    SOCKET_ADDRESS, "load"))
@patch('smartwatts.puller.puller_actor.PullerActor._read_behaviour', side_effect=Actor._initial_behaviour)
@patch('smartwatts.dispatcher.dispatcher_actor.DispatcherActor.connect_data', side_effect=gen_side_effect(
    SOCKET_ADDRESS, 'connect_data'))
def test_start_msg_db_ok(a, b, c, context):
    """
    Send a start message to a PullerActor

    After sending the message test :
      - if the actor is alive
      - if the init method of the database object was called
      - if the actor send a OkMessage to the test process
      - if the actor call the dispatcher.connect method
    """

    db = BaseDB(Mock())
    dispatcher = DispatcherActor('dispatcher_test', Mock(), Mock())
    filt = Filter()
    filt.filter(lambda msg: True, dispatcher)

    
    puller = PullerActor("puller_test", db, filt, 0, timeout=500)
    puller.start()
    puller.connect_control(context)

    puller.send_control(StartMessage())
    assert is_log_ok(SOCKET_ADDRESS, ['load', 'connect_data'], context)
    assert puller.is_alive()
    assert isinstance(puller.receive_control(), OKMessage)

    puller.kill()

#################
# Mongo DB Test #
#################


# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Integration test of the puller actor
"""
import pickle

import pytest
import zmq
from mock import patch, Mock

from smartwatts.message import OKMessage, StartMessage
from smartwatts.filter import Filter
from smartwatts.dispatcher import DispatcherActor
from smartwatts.database import BaseDB
from smartwatts.puller import PullerActor
from smartwatts.actor import Actor

SOCKET_ADDRESS = 'ipc://@test_puller'


def gen_side_effect(address, msg):
    def log_side_effect(*args, **kwargs):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect(address)
        socket.send(pickle.dumps(msg))
        socket.close()

    return log_side_effect


def is_log_ok(address, validation_msg_list, context):
    socket = context.socket(zmq.PULL)
    socket.bind(address)

    result_list = []
    for _ in range(len(validation_msg_list)):
        event = socket.poll(500)
        if event == 0:
            return False
        msg = pickle.loads(socket.recv())
        result_list.append(msg)
    socket.close()

    result_list.sort()
    validation_msg_list.sort()

    return result_list == validation_msg_list

@pytest.fixture()
def context():
    return zmq.Context()

##################
# Initialisation #
##################


@patch('smartwatts.database.base_db.BaseDB.load', side_effect=gen_side_effect(
    SOCKET_ADDRESS, "load"))
@patch('smartwatts.puller.puller_actor.PullerActor._read_behaviour', side_effect=Actor._initial_behaviour)
@patch('smartwatts.dispatcher.dispatcher_actor.DispatcherActor.connect_data', side_effect=gen_side_effect(
    SOCKET_ADDRESS, 'connect_data'))
def test_start_msg_db_ok(a, b, c, context):
    """
    Send a start message to a PullerActor

    After sending the message test :
      - if the actor is alive
      - if the init method of the database object was called
      - if the actor send a OkMessage to the test process
      - if the actor call the dispatcher.connect method
    """

    db = BaseDB(Mock())
    dispatcher = DispatcherActor('dispatcher_test', Mock(), Mock())
    filt = Filter()
    filt.filter(lambda msg: True, dispatcher)

    
    puller = PullerActor("puller_test", db, filt, 0, timeout=500)
    puller.start()
    puller.connect_control(context)

    puller.send_control(StartMessage())
    assert is_log_ok(SOCKET_ADDRESS, ['load', 'connect_data'], context)
    assert puller.is_alive()
    assert isinstance(puller.receive_control(), OKMessage)

    puller.kill()

################
# MongoDB Test #
################

def test_start_msg_db_bad_hostname(context):
    """
    Send a start message to a PullerActor with a DB with a bad configuration

    After sending the message test :
      - if the actor is alive
      - if the init method of the database object was called
      - if the actor send a OkMessage to the test process
      - if the actor call the dispatcher.connect method
    """

    db = MongoDB('toto', 27017, 'test_monggodb', 'test_monggodb1',
                 report_model=Mock())

    puller = PullerActor("puller_test", db, Mock(), 0, timeout=500)
    puller.start()
    puller.connect_control(context)

    puller.send_control(StartMessage())
    puller.join()
    assert not puller.is_alive()
    assert isinstance(puller.receive_control(), ErrorMessage)
