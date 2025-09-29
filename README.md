ClueBot NG - IRC Relay
======================

The IRC relay dispatches messages (1 way) to IRC channels.

Listeners:

* UDP - line separated formatted as `<channel>:<message>`
* TCP - connection separated formatted as `<channel>:<message>`

Supports:

* Multiple destination channels
* Multiple message sources
* IRC server reconnection handling
* IRC server authentication via SASL

## Basic local testing

Start the server
```
$ IRC_RELAY_CLIENT_CHANNELS=#wikipedia-en-cbng-debug ./irc_relay/server.py
INFO:irc_relay.listeners.udp:Starting UDP Listener
INFO:irc_relay.listeners.tcp:Starting TCP Listener
INFO:irc_relay.senders.irc:Starting IRC Client
INFO:irc_relay.senders.irc:No credentials, skipping SASL
```

In another terminal execute the client
```
$ ./irc_relay/client.py 
```

In the first terminal observe the messages where handled
```
INFO:irc_relay.senders.irc:Sending [#wikipedia-en-cbng-debug] Hello World
INFO:irc_relay.senders.irc:Sending [#wikipedia-en-cbng-debug] Hello World
```
