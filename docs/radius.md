# Radius

## Settings up

### Test User
To create a test user, add the following line to `/etc/freeradius/users`.

```
testing Cleartext-Password := "password"
```

### Adding a Client
To create a client, add the following lines to `/etc/freeradius/clients.conf`.

```
client p4sec {
        ipaddr = <ip>
        secret = testing123
}
```

Here `<ip>` must be your local ip. If you are not sure which one to use run `ip a`.

### Starting the server

You can start the server by using:

```
sudo service freeradius <start|stop|restart|status>
```

### Testing
Run the following command to make a EAP request.

```
radtest -t eap-md5 -x testing password <ip> 0 testing123
```
