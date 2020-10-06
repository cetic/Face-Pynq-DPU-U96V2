import time
import cv2
import screeninfo


if __name__ == "__main__":
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    if not (cam.isOpened()):
        print("[ERROR] Failed to open camera ")
        exit()
    window_name = 'main'
    screen_id = 0
    screen = screeninfo.get_monitors()[screen_id]
    width, height = screen.width, screen.height
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.moveWindow(window_name, screen.x - 1, screen.y - 1)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    font = cv2.FONT_HERSHEY_SIMPLEX
    prev_frame_time = 0
    new_frame_time = 0
    while True:
        new_frame_time = time.time()
        ret,frame = cam.read()
        fps = 1/(new_frame_time-prev_frame_time)
        prev_frame_time = new_frame_time
        fps = int(fps)
        cv2.putText(frame, "fps:"+str(fps), (7, 20), font, 0.5, (100, 255, 0), 1, cv2.LINE_AA)
        cv2.imshow(window_name, frame)
        cv2.waitKey(1)
    cv2.destroyAllWindows()
