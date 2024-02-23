# SimPy model for the Reliable Data Transport (rdt) Protocol 2.0 (Using ACK and NAK)

#
# Sender-side (rdt_Sender)
#	- receives messages to be delivered from the upper layer 
#	  (SendingApplication) 
#	- Implements the protocol for reliable transport
#	 using the udt_send() function provided by an unreliable channel.
#
# Receiver-side (rdt_Receiver)
#	- receives packets from the unrealible channel via calls to its
#	rdt_rcv() function.
#	- implements the receiver-side protocol and delivers the collected
#	data to the receiving application.

# Author: Akshad Vivek Gajbhiye


import simpy
import random
from Packet import Packet
import sys

# the sender can be in one of these two states:
WAITING_FOR_CALL_0_FROM_ABOVE =0
WAIT_FOR_ACK_0=1
WAITING_FOR_CALL_1_FROM_ABOVE =2
WAIT_FOR_ACK_1=3

WAIT_FOR_0_FROM_BELOW=4
WAIT_FOR_1_FROM_BELOW=5

class rdt_Sender(object):

	def __init__(self,env):
		# Initialize variables
		self.env=env 
		self.channel=None
		
		# some state variables
		self.state = WAITING_FOR_CALL_0_FROM_ABOVE
		self.seq_num=0
		self.packet_to_be_sent=None
		# self.ack_num=1

	
	def rdt_send(self,msg):

		if self.state==WAITING_FOR_CALL_0_FROM_ABOVE:
			# This function is called by the 
			# sending application.
			
			# create a packet, and save a copy of this packet
			# for retransmission, if needed
			self.packet_to_be_sent = Packet(seq_num=self.seq_num, payload=msg)
			self.seq_num=1
			# send it over the channel
			print("TIME:",self.env.now,"RDT_SENDER: Sending packet on data channel", self.packet_to_be_sent)
			self.channel.udt_send(self.packet_to_be_sent)
			# wait for an ACK or NAK
			self.state=WAIT_FOR_ACK_0

			return True 
		elif self.state==WAITING_FOR_CALL_1_FROM_ABOVE:
			# This function is called by the 
			# sending application.
			
			# create a packet, and save a copy of this packet
			# for retransmission, if needed
			self.packet_to_be_sent = Packet(seq_num=self.seq_num, payload=msg)
			self.seq_num=0
			# send it over the channel
			self.channel.udt_send(self.packet_to_be_sent)
			# wait for an ACK or NAK
			self.state=WAIT_FOR_ACK_1
			return True 
		else:
			return False
	
	def rdt_rcv(self,packt):
		# This function is called by the lower-layer 
		# when an ACK/NAK packet arrives
		#assert(self.state==(WAIT_FOR_ACK_0 or WAIT_FOR_ACK_1))
		if(packt.payload=="ACK0"):
			# self.ack_num+=1
			# Received an ACK 0. Everything's fine. Change to state 2
			self.state=WAITING_FOR_CALL_1_FROM_ABOVE
			# if(self.ack_num==1000):
			# 	print("TIME:",self.env.now,"RDT_SENDER: We have successfully sent 1000 packets.")
			# 	print("We are halting now")
			# 	sys.exit(0)
			return True
		elif(packt.payload=="ACK1"):
			# self.ack_num+=1
			# Received an ACK 1. Everything's fine. Change to state 0
			self.state=WAITING_FOR_CALL_0_FROM_ABOVE
			# if(self.ack_num==1000):
			# 	print("TIME:",self.env.now,"RDT_SENDER: We have successfully sent 1000 packets.")
			# 	print("We are halting now")
			# 	sys.exit(0)
			return True
		elif(packt.payload=="$H!T"):
			# Received a NAK. Need to resend packet.
			self.channel.udt_send(self.packet_to_be_sent)
			return False
		else:
			print("ERROR! rdt_rcv() was expecting an ACK0 or ACK1. Received a corrupted packet.")
			print("Halting simulation...")
			sys.exit(0)

			

class rdt_Receiver(object):
	def __init__(self,env):
		# Initialize variables
		self.env=env 
		self.receiving_app=None
		self.channel=None

		self.state = WAIT_FOR_0_FROM_BELOW
		self.packet_to_be_sent=None
		

	def rdt_rcv(self,packt):
		# This function is called by the lower-layer when a packet arrives
		# at the receiver
		
		# check whether the packet is corrupted
		print("TIME:",self.env.now,"RDT_RECEIVER: Received packet", packt.payload)

		if self.state==WAIT_FOR_0_FROM_BELOW:
			if(packt.corrupted==True or packt.seq_num==1):
				# send a NAK and discard this packet.
				response1 = Packet(seq_num=0, payload="ACK1") #Note: seq_num for the response can be arbitrary. It is ignored.
				# send it over the channel
				self.channel.udt_send(response1)
			elif(packt.corrupted==False and packt.seq_num==0):
				# The packet is not corrupted.
				# Send an ACK and deliver the data.
				response2 = Packet(seq_num=0, payload="ACK0") 
				# send it over the channel
				self.channel.udt_send(response2)
				self.receiving_app.deliver_data(packt.payload)
				self.state=WAIT_FOR_1_FROM_BELOW
				#print("change")
			else:
				print("Error hogya shit.")

		elif self.state==WAIT_FOR_1_FROM_BELOW:
			if(packt.corrupted==True or packt.seq_num==0):
				# send a NAK and discard this packet.
				response3 = Packet(seq_num=0, payload="ACK0") #Note: seq_num for the response can be arbitrary. It is ignored.
				# send it over the channel
				self.channel.udt_send(response3)
			elif(packt.corrupted==False and packt.seq_num==1):
				# The packet is not corrupted.
				# Send an ACK and deliver the data.
				response4 = Packet(seq_num=0, payload="ACK1") 
				# send it over the channel
				self.channel.udt_send(response4)
				self.receiving_app.deliver_data(packt.payload)
				self.state=WAIT_FOR_0_FROM_BELOW
			else:
				print("Error hogya shit.")
		else:
			print("Error hogya shit")

