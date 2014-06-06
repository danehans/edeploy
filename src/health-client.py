#!/usr/bin/python2

from socket import socket, AF_INET, SOCK_STREAM
from health_messages import Health_Message as HM
from health_bench import Health_Bench as HB
from health_bench import Health_CPU as HCPU
import atexit
import health_protocol as HP
import logging
import time
import sys

s = socket(AF_INET, SOCK_STREAM)

def invalid_message(msg):
    HP.logger.error("%s is not a valid message for a client" % msg.get_message_type())

def none(socket, msg):
    invalid_message(msg)

def start(socket, msg):
    HP.logger.info("Recevied START")

def stop(socket, msg):
    return

def completed(socket, msg):
    return

def connect(socket, msg):
    invalid_message(msg)

def disconnect(socket, msg):
    HP.logger.info("Disconnecting based on server request")
    cleanup()

def ack(socket, msg):
    return

def nack(socket, msg):
    return

def cpu(socket, msg):
    HP.logger.info("Module CPU (%d sec)" % msg.running_time)
    action(socket, msg, HCPU(msg, socket, HP.logger))
    return

def storage(socket, msg):
    return

def memory(socket, msg):
    return

def network(socket, msg):
    return

def action(socket, msg, hb):
    handlers = { HM.NONE     : hb.none,
                HM.STOP      : hb.stop,
                HM.START     : hb.start,
                HM.COMPLETED : hb.completed,
                HM.NOTCOMPLETED : hb.notcompleted,
    }
    
    HP.logger.info("Received action %s (%d)" % (msg.get_action_type(), msg.action)) 
    handlers[msg.action]()

def module(socket, msg):
    handlers = { HM.NONE    : none, 
                HM.CPU      : cpu,
                HM.STORAGE  : storage,
                HM.MEMORY   : memory,
                HM.NETWORK  : network,
    }
    
    HP.logger.info("Received module %s (%d)" % (msg.get_module_type(), msg.module)) 
    handlers[msg.module](socket, msg)


def connect_to_server(hrdw, hostname):
    global s
    s.connect((hostname, 20000))
    HP.send_hm_message(s, HM(HM.CONNECT), True)
    while True:
        msg = HP.recv_hm_message(s)

        if not msg:
            continue;

        if msg.message == HM.INVALID:
            HP.logger.error("Ignoring invalid message")
            continue;

        msg.hw = hrdw

        handlers = { HM.NONE      : none, 
                    HM.CONNECT    : connect,
                    HM.DISCONNECT : disconnect,
                    HM.ACK        : ack,
                    HM.NACK       : nack,
                    HM.MODULE     : module,
        }

        HP.logger.info("Received %d" % msg.message) 
        HP.logger.info(handlers)
        handlers[msg.message](s,msg)


def cleanup():
    global s
    HP.send_hm_message(s, HM(HM.DISCONNECT), False)
    s.shutdown(1)
    s.close()

if __name__ == '__main__':
    HP.start_log('/var/tmp/health-client.log', logging.DEBUG)
    atexit.register(cleanup)
    hrdw = eval(open(sys.argv[1]).read(-1))
    connect_to_server(hrdw, 'localhost')