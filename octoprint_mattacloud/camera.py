import requests
import shutil
import cv2


def capture_snapshot(endpoint, path):
    resp = requests.get(
        'http://{}/webcam/?action=snapshot'.format(endpoint),
        stream=True
    )
    if resp.status_code == 200:
        with open(path, 'wb') as f:
            resp.raw.decode_content = True
            shutil.copyfileobj(resp.raw, f)


def list_cameras():
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(index)
        cap.release()
        index += 1
    return arr


def main():
    pass

if __name__ == '__main__':
    main()
