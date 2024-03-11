import cv2
from PIL import Image
import PIL.PngImagePlugin
from picamera2 import Picamera2

cam = Picamera2()
config = cam.create_still_configuration(main={"size": (2304, 1296)})
cam.configure(config)


def take_pic_windows() -> Image.Image | None:
    # Initialize the webcam
    cap = cv2.VideoCapture(0)

    ret = False
    counter = 0

    # Try to capture a frame from the webcam
    while not ret and counter < 10:
        ret, frame = cap.read()
        counter += 1

    # Release the webcam
    cap.release()

    if ret:
        # Create a PIL.Image object from the frame
        # Note that we pass (frame width, frame height) to the size parameter
        return Image.frombuffer(
            "RGB", (frame.shape[1], frame.shape[0]), frame, "raw", "BGR", 0, 1
        )
    else:
        print("Failed to capture frame")


def take_pic() -> Image.Image | None:
    """
    Takes a photo using the webcam and returns a PIL.Image object.

    Returns:
        Image.Image | None: The photo from the webcam, if successful.
    """
    cam.start()
    image = cam.capture_image("main")
    cam.stop()
    return image


if __name__ == "__main__":
    from time import sleep

    sleep(3)
    img = take_pic()
    if img:
        ...
        img.show()
    else:
        print("Failed to capture image")
