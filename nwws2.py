#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import signal
import os
import logging
import json
import time
import sleekxmpp
from datetime import datetime
from xml.dom import minidom

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

def signal_handler(signal, frame):
    print('Caught Ctrl+C. Exiting.')
    file = open('/tmp/exit_nwws2', 'w')
    file.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class MUCBot(sleekxmpp.ClientXMPP):

    """
    A simple SleekXMPP bot that will greets those
    who enter the room, and acknowledge any messages
    that mentions the bot's nickname.
    """

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The groupchat_message event is triggered whenever a message
        # stanza is received from any chat room. If you also also
        # register a handler for the 'message' event, MUC messages
        # will be processed by both handlers.
        self.add_event_handler("groupchat_message", self.muc_message)


    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room, self.nick)

    def muc_message(self, msg):
        """
        Process incoming message stanzas from any chat room. Be aware
        that if you also have any handlers for the 'message' event,
        message stanzas may be processed by both handlers, so check
        the 'type' attribute when using a 'message' event handler.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
	print msg['body']
	xmldoc = minidom.parseString(str(msg));
	itemlist = xmldoc.getElementsByTagName('x')
	ttaaii = itemlist[0].attributes['ttaaii'].value.lower()
	cccc = itemlist[0].attributes['cccc'].value.lower()
	awipsid = itemlist[0].attributes['awipsid'].value.lower()
	id = itemlist[0].attributes['id'].value.lower()
	content = itemlist[0].firstChild.nodeValue
	if awipsid:
	   dayhourmin = datetime.utcnow().strftime("%d%H%M")
	   id = id.replace('.', '')
	   filename = cccc + '_' + ttaaii + '-' + awipsid + '.' + dayhourmin + '_' + id[-6:] + '.txt'
	   #print("INFO\t Writing " + filename)
	   if not os.path.exists(config['archivedir'] + '/' + cccc):
	      os.makedirs(config['archivedir'] + '/' + cccc)
	   # Remove every other line
	   lines = content.splitlines()
	   pathtofile = config['archivedir'] + '/' + cccc + '/' + filename
	   f = open(pathtofile, 'w')
	   count = 0
	   for line in lines:
	      if count == 0 and line == '':
		 continue
	      if count % 2 == 0:
	         f.write(line + "\n")
	      count += 1
	   f.close()
	   # Run a command using the file as the parameter (if pan_run is defined in the config file)
	   if config.has_key('pan_run'):
	      try:
	         os.system(config['pan_run']+' '+pathtofile+' >/dev/null')
	      except OSError as e:
		 print >>sys.stderr, "ERROR    Execution failed:", e


if __name__ == '__main__':
    # Check for command line arguments
    if len(sys.argv) == 1:
       print('Usage: '+sys.argv[0]+' /path/to/config')
       sys.exit(1)

    # Setup logging.
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')

    # Parse JSON config
    config = json.load(open(sys.argv[1]))

    # Create archive directory if it does not exist
    if not os.path.exists(config['archivedir']):
       os.makedirs(config['archivedir'])

    # Start endless loop
    while True:

        # Setup the MUCBot and register plugins. Note that while plugins may
        # have interdependencies, the order in which you register them does
        # not matter.
        xmpp = MUCBot(config['username'] + '@nwws-oi.weather.gov', config['password'], 'nwws@conference.nwws-oi.weather.gov', config['resource'])
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0045') # Multi-User Chat
        xmpp.register_plugin('xep_0199') # XMPP Ping

        # Connect to the XMPP server and start processing XMPP stanzas.
        if xmpp.connect():
            # If you do not have the dnspython library installed, you will need
            # to manually specify the name of the server if it does not match
            # the one in the JID. For example, to use Google Talk you would
            # need to use:
            #
            # if xmpp.connect(('talk.google.com', 5222)):
            #     ...
            xmpp.process(block=True)
            if os.path.isfile('/tmp/exit_nwws2'):
               os.remove('/tmp/exit_nwws2')
               sys.exit(1)
        else:
            print("Unable to connect.")
            sys.exit(1)

        print('Sleeping for 5 seconds..')
        time.sleep(5) 

