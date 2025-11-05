from djitellopy import Tello
import h264decoder
from PIL import Image
import time
import threading
import socket
import numpy as np

'''
[YES]: stop(void) -> status<OK,FAIL>
freeze(void) -> status<OK,FAIL>
take_frame(void) -> status<frame,NULL>
start(void) -> status<OK,FAIL>
raw(void) -> status<framechunks,NULL>
record(int dur, string loc) -> status<OK,FAIL>
'''


class VideoDriver:
    def __init__(self, config=Tello(), video_ip='0.0.0.0'):
        self.drone = config
        self.frame = None  # frame read from h264decoder
        self.last_frame = None  # last frame when video is frozen

        self.decoder = h264decoder.H264Decoder()
        self.frozen = False

        self.video_port = 11111

        self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for receiving video stream
        self.socket_video.bind((video_ip, self.video_port))

        self.sending_command_thread = threading.Thread(target=self._sendingCommand)
        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True
        self.receive_video_thread.start()

        self.initialized = False

    def __del__(self):
        """Closes the local socket."""
        self.socket_video.close()

    def initialize(self):
        if not self.initialized:
            print("drive: Initializing video driver...")

            # Connect to the drone and start video stream
            self.drone.connect()
            self.drone.streamon()
            self.initialized = True
            print("Video driver initialized.")

        else:
            print("Video driver is already initialized.")

    def shutdown(self):
        if self.initialized:
            print("Shutting down video driver...")

            # Stop the video stream
            self.drone.streamoff()
            self.initialized = False

            print("Video driver shut down.")
        else:
            print("Video driver is not initialized.")

    def read(self):
        if not self.initialized:
            raise Exception("Video driver is not initialized. Cannot render frame.")
        """Return the last frame from camera."""
        if self.frozen:
            return [0, self.last_frame]
        else:
            return [1, self.frame]

    def video_freeze(self, is_frozen=True):
        if not self.initialized:
            raise Exception("Video driver is not initialized. Cannot render frame.")
        """Pause video output -- set is_freeze to True"""
        self.frozen = is_frozen
        if is_frozen:
            self.last_frame = self.frame

    def _receive_video_thread(self):
        """
        Listens for video streaming (raw h264) from the Tello.

        Runs as a thread, sets self.frame to the most recent frame Tello captured.

        """
        packet_data = b""
        while True:
            try:
                res_string, ip = self.socket_video.recvfrom(2048)
                packet_data += res_string
                # end of frame
                if len(res_string) != 1460:
                    for frame in self._h264_decode(packet_data):
                        self.frame = frame
                    packet_data = b""

            except socket.error as exc:
                print("Caught exception socket.error : %s" % exc)

    def _h264_decode(self, packet_data):
        """
        decode raw h264 format data from Tello

        :param packet_data: raw h264 data array

        :return: a list of decoded frame
        """
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for frame_data in frames:
            (frame, w, h, ls) = frame_data
            if frame is not None:
                # print 'frame size %i bytes, w %i, h %i, line_size %i' % (len(frame), w, h, ls)

                frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep='')
                frame = (frame.reshape((h, ls // 3, 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)

        return res_frame_list

    def _sendingCommand(self):
        """
        start a while loop that sends 'command' to tello every 5 second
        """

        while True:
            self.drone.connect()
            time.sleep(5)