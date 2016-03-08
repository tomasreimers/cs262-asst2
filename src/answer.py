import multiprocessing as mp
import Queue
import time
import random

# VM Objects
class VM(object):
    def __init__(self, name, queue):
        self.name = name
        # messages are simply logical clock times
        self.messages = []

        self.Q = queue
        self.VM1Q = None
        self.VM2Q = None

        self.time_for_instruction = None
        self.logical_clock = 1

    def registerVM1Queue(self, vm_queue):
        self.VM1Q = vm_queue

    def registerVM2Queue(self, vm_queue):
        self.VM2Q = vm_queue

    def setClockSpeed(self, cs):
        self.time_for_instruction = 1. / cs

    def log(self, message):
        print "[" + self.name + " | time: " + str(time.time()) + ", lc:" + str(self.logical_clock) + "] " + message

    def execution(self):
        #
        # TODO : Consider adding a barrier here (https://docs.oracle.com/cd/E19120-01/open.solaris/816-5137/gfwek/index.html)
        #

        # simulate execution
        while (True):
            # figure out how long the instruction took
            started = time.time()

            # simulate a thread to read messages
            while self.time_for_instruction > (time.time() - started):
                try:
                    # exit either when there's a message to be processed or it's time for another command
                    message = self.Q.get(True, self.time_for_instruction - (time.time() - started))
                    self.messages.append(message)
                except Queue.Empty:
                    # if blocked for the whole clock cycle, then we must
                    break               

            # simulate a thread to process message or take an action
            if (len(self.messages) > 0):
                # there exist messages
                message = self.messages.pop(0)
                self.logical_clock = max(message, self.logical_clock) + 1
                self.log("Message received, Queue still has " + str(len(self.messages)) + " messages")
            else:
                # roll to figure out instruction
                roll = random.randint(1, 10)
                if (roll == 1):
                    self.VM1Q.put(self.logical_clock)
                    self.log("Sent message to 1")
                elif (roll == 2):
                    self.VM2Q.put(self.logical_clock)
                    self.log("Sent message to 2")
                elif (roll == 3):
                    self.VM1Q.put(self.logical_clock)
                    self.VM2Q.put(self.logical_clock)
                    self.log("Sent message to both")
                else:
                    self.log("Internal event")

                # no messages, increment logical clock
                self.logical_clock += 1

# main thread of execution
if __name__ == "__main__":
    # create Queues for each VM to read from
    queue1 = mp.Queue()
    queue2 = mp.Queue()
    queue3 = mp.Queue()

    # create VMs
    v1 = VM("VM1", queue1)
    v2 = VM("VM2", queue2)
    v3 = VM("VM3", queue3)
    
    # set up the threads
    v1.registerVM1Queue(queue2)
    v1.registerVM2Queue(queue3)
    v1_clock_speed = random.randint(1,6)
    v1.setClockSpeed(v1_clock_speed)

    v2.registerVM1Queue(queue1)
    v2.registerVM2Queue(queue3)
    v2_clock_speed = random.randint(1,6)
    v2.setClockSpeed(v2_clock_speed)

    v3.registerVM1Queue(queue1)
    v3.registerVM2Queue(queue2)
    v3_clock_speed = random.randint(1,6)
    v3.setClockSpeed(v3_clock_speed)

    print ("Clock Speeds: ["
        + "VM1: " + str(v1_clock_speed) 
        + " | VM2: " + str(v2_clock_speed) 
        + " | VM3: " + str(v3_clock_speed) + "]")
    
    # on your mark, get set, go!
    p1 = mp.Process(target=v1.execution)
    p2 = mp.Process(target=v2.execution)
    p3 = mp.Process(target=v3.execution)
    
    p1.start()
    p2.start()
    p3.start()
