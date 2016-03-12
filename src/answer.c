#include <stdlib.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <fcntl.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/time.h>

#define MAX( a, b ) ( ( a > b) ? a : b )


// I truly hate C.


struct queue_node {
        struct queue_node *next;
        int val;
};

struct queue {
        struct queue_node *head;
        pthread_mutex_t mutex;
        int num;
};

struct logical_clock
{
        pthread_mutex_t mutex;
        int num;
};

struct reader_args
{
        struct queue *queue;
        int listen_queue;
        struct logical_clock *lc;
        int vmnum;
};

struct writer_args
{
        struct queue *queue;
        int send_queue_1;
        int send_queue_2;
        struct logical_clock *lc;
        int vmnum;
        int clockspeed;
};


long
get_microseconds(void)
{
        struct timeval ts;
        gettimeofday(&ts, NULL);
        return (ts.tv_sec * 1e6) + ts.tv_usec;
}


void *
reader(void *args)
{
        struct reader_args *ra = (struct reader_args *)args;

        while (true) {
                int data;
                read(ra->listen_queue, &data, sizeof(data));
                pthread_mutex_lock(&ra->queue->mutex);

                struct queue_node *newqnode = malloc(sizeof(newqnode));
                assert(newqnode != NULL);

                newqnode->val = data;
                newqnode->next = NULL;

                struct queue_node **tail = &ra->queue->head;

                while (*tail != NULL) {
                        tail = &(*tail)->next;
                }
                *tail = newqnode;

                ra->queue->num += 1;

                pthread_mutex_unlock(&ra->queue->mutex);
        }
}


void *
writer(void *args)
{
        struct writer_args *wa = (struct writer_args *)args;

        // initialize, in microseconds
        long clockspeed = (1. / wa->clockspeed) * 1e6;

        while (true) {
                struct queue_node *curr = NULL;
                int total_on_queue = 0;
                int newlc;

                long tstart = get_microseconds();

                pthread_mutex_lock(&wa->queue->mutex);
                if (wa->queue->num > 0) {
                        // pop top of queue
                        curr = wa->queue->head;
                        wa->queue->head = wa->queue->head->next;
                        wa->queue->num--;
                        total_on_queue = wa->queue->num;
                        pthread_mutex_unlock(&wa->queue->mutex);
                        pthread_mutex_lock(&wa->lc->mutex);
                        newlc = MAX(wa->lc->num, curr->val) + 1;
                        wa->lc->num = newlc;
                        pthread_mutex_unlock(&wa->lc->mutex);
                        printf("[VM %d | time: %u, lc:%d] Message received, Queue still has %d messages\n", wa->vmnum, (unsigned)time(NULL), newlc, total_on_queue);
                        free(curr);
                } else {
                        pthread_mutex_unlock(&wa->queue->mutex);
                        int n = rand() % 10;
                        switch(n) {
                                case 0:
                                        pthread_mutex_lock(&wa->lc->mutex);
                                        newlc = wa->lc->num;
                                        pthread_mutex_unlock(&wa->lc->mutex);

                                        write(wa->send_queue_1, &newlc, sizeof(int));
                                        printf("[VM %d | time: %u, lc:%d] Sent message to 1\n", wa->vmnum, (unsigned)time(NULL), newlc);

                                        break;
                                case 1:
                                        pthread_mutex_lock(&wa->lc->mutex);
                                        newlc = wa->lc->num;
                                        pthread_mutex_unlock(&wa->lc->mutex);

                                        write(wa->send_queue_2, &newlc, sizeof(int));
                                        printf("[VM %d | time: %u, lc:%d] Sent message to 2\n", wa->vmnum, (unsigned)time(NULL), newlc);

                                        break;
                                case 2:
                                        pthread_mutex_lock(&wa->lc->mutex);
                                        int newlc = wa->lc->num;
                                        pthread_mutex_unlock(&wa->lc->mutex);

                                        write(wa->send_queue_1, &newlc, sizeof(int));
                                        write(wa->send_queue_2, &newlc, sizeof(int));
                                        printf("[VM %d | time: %u, lc:%d] Sent message to both\n", wa->vmnum, (unsigned)time(NULL), newlc);

                                        break;
                                default:
                                        pthread_mutex_lock(&wa->lc->mutex);
                                        newlc = wa->lc->num;
                                        pthread_mutex_unlock(&wa->lc->mutex);
                                        printf("[VM %d | time: %u, lc:%d] Internal event\n", wa->vmnum, (unsigned)time(NULL), newlc);
                        }

                        // increment the logical clock
                        pthread_mutex_lock(&wa->lc->mutex);
                        wa->lc->num++;
                        pthread_mutex_unlock(&wa->lc->mutex);
                }


                long tend = get_microseconds();
                long duration = tend - tstart;
                long time_to_wait = clockspeed - duration;

                if (time_to_wait > 0){
                        usleep(time_to_wait);
                }
        }
}


// need to pass randseed or they all have the same random
int
VM(int vmnum, int clockspeed, int listen_queue, int send_queue_1, int send_queue_2, int randseed)
{
        int child = fork();
        assert(child != -1);

        if (child == 0) {
                srand(randseed);

                // in child, simulate VM
                pthread_t t1, t2;

                struct queue *q = malloc(sizeof(struct queue));
                assert(q != NULL);
                q->head = NULL;
                q->num = 0;
                pthread_mutex_init(&q->mutex, NULL);

                struct logical_clock *lc = malloc(sizeof(struct logical_clock));
                lc->num = 0;
                pthread_mutex_init(&lc->mutex, NULL);

                struct reader_args r;
                r.queue = q;
                r.listen_queue = listen_queue;
                r.lc = lc;
                r.vmnum = vmnum;

                struct writer_args w;
                w.queue = q;
                w.send_queue_1 = send_queue_1;
                w.send_queue_2 = send_queue_2;
                w.lc = lc;
                w.vmnum = vmnum;
                w.clockspeed = clockspeed;

                assert(-1 != pthread_create(&t1, NULL, reader, (void *)&r));
                assert(-1 != pthread_create(&t2, NULL, writer, (void *)&w));

                pthread_join(t1, NULL);
                pthread_join(t2, NULL);

                // never return
                exit(0);
        } else {
                // in parent, return child PID
                return child;
        }

        // should never get here
        return -1;
}


int
main(void)
{

        // Create queues, [0] for reading and [1] for writing
        int vm1_pipe[2];
        int vm2_pipe[2];
        int vm3_pipe[2];

        assert(-1 != pipe(vm1_pipe));
        assert(-1 != pipe(vm2_pipe));
        assert(-1 != pipe(vm3_pipe));

        // create clockspeed
        int cs1 = ((rand() % 6) + 1);
        int cs2 = ((rand() % 6) + 1);
        int cs3 = ((rand() % 6) + 1);

        printf("Clock Speeds: [VM1: %d | VM2: %d | VM3: %d]\n", cs1, cs2, cs3);

        // create VMs
        int vm1 = VM(1, cs1, vm1_pipe[0], vm2_pipe[1], vm3_pipe[1], rand());
        int vm2 = VM(2, cs2, vm2_pipe[0], vm1_pipe[1], vm3_pipe[1], rand());
        int vm3 = VM(3, cs3, vm3_pipe[0], vm1_pipe[1], vm2_pipe[1], rand());

        // spin until done
        waitpid(vm1, NULL, 0);
        waitpid(vm2, NULL, 0);
        waitpid(vm3, NULL, 0);

        return 0;
}
