This is a collection of time baseded side-channel tools.

Enum-OpenSSH.py is a file that enumerates OpenSSH 5.x and 6.X users. The bug was
discovered back in 2006 by Marco Ivaldi, and I read about it here:

https://cureblog.de/2013/07/openssh-user-enumeration-time-based-attack/

I chose to write my own code for learning purposes.

Initially it works from a list of common users, and if it finds one, it appends
that user back to the top of the list when it write back out. This keeps the list
of users loosely ranked over multiple runs. Then it moves on to brute forcing if
the user wishes to do so. Again if auser is found it is added to the list.

The vulnerability is hardware dependant. I have found that an old machine on a local
lan works well, but a remote machine on a VM does not exhibit the bug despite being
the correct versions of OpenSSH. Obviously, latency is an issue as well, which can
affect the accuracy.

Future improvement will be to remove the hardcoding of the timeout, and produce a
test of latency and detection of the two mean RTTs.

