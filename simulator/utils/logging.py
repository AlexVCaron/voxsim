from queue import Queue
from threading import Thread
import pathlib
import time


class RTLogging:
    def __init__(self, process, log_file_path: pathlib.Path, log_tag=""):
        self._process = process
        self._log: pathlib.Path = log_file_path
        self._tag = log_tag
        self._thread = None

    def start(self, logging_args=()):
        self._thread = Thread(target=self._read_output, args=logging_args)
        self._thread.daemon = True
        self._thread.start()

    def join(self):
        self._thread.join()

    def _read_output(self, poll_timer=4, logging_callback=lambda a: None):
        stdout_queue = Queue()
        stderr_queue = Queue()
        t1 = Thread(
            target=self._enqueue_thread_output,
            args=(self._process.stdout, stdout_queue),
        )
        t1.daemon = True
        t1.start()
        t2 = Thread(
            target=self._enqueue_thread_output,
            args=(self._process.stderr, stderr_queue),
        )
        t2.daemon = True
        t2.start()

        with open(self._log, "a+") as log_file:
            while self._process.poll() is None:
                self._dequeue_output(log_file, stdout_queue, "STD")
                self._dequeue_output(log_file, stderr_queue, "ERR")

                logging_callback(self._log)
                time.sleep(poll_timer)

            self._dequeue_output(log_file, stdout_queue, "STD")
            self._dequeue_output(log_file, stderr_queue, "ERR")

            logging_callback(self._log)
            time.sleep(poll_timer)

    def _enqueue_thread_output(self, pipe, queue):
        while self._process.poll() is None:
            ln = pipe.readline()
            queue.put(ln)

    def _dequeue_output(self, log_file, queue, tag):
        try:
            while not queue.empty():
                ln = queue.get_nowait()
                if ln:
                    log_file.write(
                        "\n".join(
                            [
                                "{}[{}] {}".format(self._tag, tag, l)
                                for l in ln.decode("ascii").strip().split("\n")
                            ]
                        )
                        + "\n"
                    )
                    log_file.flush()
        except:
            pass
