import threading
import time
import random

# VM Objects
class VM(object):
    def __init__(self, name):
        self.name = name
        # messages are simply logical clock times
        self.messages = [] # python lists are thread safe, so no lock needed
        self.VM1 = None
        self.VM2 = None
        self.time_for_instruction = None
        self.logical_clock = 1

    def registerVM1(self, vm):
        self.VM1 = vm

    def registerVM2(self, vm):
        self.VM2 = vm

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

            # see if any messages in the queue
            if (len(self.messages) > 0):
                # there exist messages
                message = self.messages.pop(0)
                self.logical_clock = max(message, self.logical_clock) + 1
                self.log("Message received, Queue still has " + str(len(self.messages)) + " messages")
            else:

                #
                # TODO : Do we update the logical clock before or after the send?
                #

                # no messages, increment logical clock
                self.logical_clock += 1

                # roll to figure out instruction
                roll = random.randint(1, 10)
                if (roll == 1):
                    self.VM1.messages.append(self.logical_clock)
                    self.log("Sent message to 1")
                if (roll == 2):
                    self.VM2.messages.append(self.logical_clock)
                    self.log("Sent message to 2")
                if (roll == 3):
                    self.VM1.messages.append(self.logical_clock)
                    self.VM2.messages.append(self.logical_clock)
                    self.log("Sent message to 3")

            # sleep for remaining amount of time
            time_taken = time.time() - started
            time_remaining = self.time_for_instruction - time_taken
            if time_remaining > 0:
                time.sleep(time_remaining)


# main thread of execution
if __name__ == "__main__":
    # create VMs
    v1 = VM("VM 1")
    v2 = VM("VM 2")
    v3 = VM("VM 3")

    # set up the threads
    v1.registerVM1(v2)
    v1.registerVM2(v3)
    v1.setClockSpeed(random.randint(1, 6))

    v2.registerVM1(v1)
    v2.registerVM2(v3)
    v2.setClockSpeed(random.randint(1, 6))

    v3.registerVM1(v1)
    v3.registerVM2(v2)
    v3.setClockSpeed(random.randint(1, 6))

    # on your mark, get set, go!
    t1 = threading.Thread(target=v1.execution)
    t2 = threading.Thread(target=v2.execution)
    t3 = threading.Thread(target=v3.execution)

    t1.setDaemon(True)
    t2.setDaemon(True)
    t3.setDaemon(True)

    t1.start()
    t2.start()
    t3.start()

    # wait for them all -- not joining so ctrl-C remains active
    while threading.active_count() > 0:
        time.sleep(0.1)
