from djitellopy import Tello
import h264decoder
import logging
import time
import threading
import socket
import numpy as np
import cv2

# Disable logging for the decoder and tello python driver
Tello.LOGGER.setLevel(logging.ERROR)  # Suppress djitellopy info logs
h264decoder.disable_logging()         # Supress decoder messages

'''
[YES - Implemented]:                     stop(void) -> status<OK,FAIL>
[YES - Through set_freeze]:              freeze(void) -> status<OK,FAIL>
[YES - Through camera.frame]:            take_frame(void) -> status<frame,NULL>
[YES - Through initialize]:              start(void) -> status<OK,FAIL>
[YES - Through read]:                    raw(void) -> status<framechunks,NULL>
[NO  - Not Implemented/Not needed]:      record(int dur, string loc) -> status<OK,FAIL>
'''


class VideoDriver:
    def __init__(self, config=Tello(), video_ip='0.0.0.0'):
        self.drone = config
        self.platform = "DRONE"  # For compatibility with other drivers
        self.frame = None  # frame read from h264decoder
        self.last_frame = None  # last frame when video is frozen

        self.decoder = h264decoder.H264Decoder()
        self.frozen = False

        self.video_port = 11111

        self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket for receiving video stream
        self.socket_video.bind((video_ip, self.video_port))

        self.sending_command_thread = threading.Thread(target=self._send_keepalive)
        self.sending_command_thread.daemon = True

        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True

        self.sending_command_thread.start()
        self.receive_video_thread.start()

        self.initialized = False

    def __del__(self):
        """Closes the local socket."""
        self.socket_video.close()
        self.shutdown()

    def initialize(self):
        if not self.initialized:
            print("driver: Initializing video driver...")

            # Connect to the drone and start video stream
            self.drone.connect()
            self.drone.streamon()
            self.initialized = True
            print("driver: initialized.")

        else:
            print("driver: already initialized.")

    def shutdown(self):
        if self.initialized:
            print("driver: shutting down...")

            # Stop the video stream
            self.drone.streamoff()
            self.initialized = False

            print("driver: closed.")
        else:
            print("driver: not initialized.")

    def release(self):
        self.shutdown()

    def read(self):
        if not self.initialized:
            raise Exception("driver: not initialized. Cannot render frame.")
        """Return the last frame from camera."""
        if self.frozen:
            return [2, self.last_frame]
        else:
            if self.frame is None:
                # This is the standard way to indicate no frame available yet
                return [0, 0]
            # Return the frame
            return [1, self.frame]

    def set_freeze(self, is_frozen=True):
        if not self.initialized:
            raise Exception("driver: not initialized. Cannot render frame.")
        """Pause video output -- set is_freeze to True"""
        self.frozen = is_frozen
        if is_frozen:
            print("driver: freezing camera")
            self.last_frame = self.frame
        else:
            print("driver: unfreezing camera")

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

                # Convert from RGB to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                res_frame_list.append(frame)

        return res_frame_list

    def _send_keepalive(self):
        """
        start a while loop that sends 'command' to tello every 5 second
        """

        while True:
            self.drone.connect()
            time.sleep(5)
            print("driver: Sent keepalive command to Tello")
