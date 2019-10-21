import requests
import shutil
import subprocess


def capture_snapshot(endpoint, path):
    resp = requests.get(
        'http://{}/webcam/?action=snapshot'.format(endpoint),
        stream=True
    )
    if resp.status_code == 200:
        with open(path, 'wb') as f:
            resp.raw.decode_content = True
            shutil.copyfileobj(resp.raw, f)


def fswebcam_snapshot(device, img_path, x=1280, y=720):
    cmd_str = 'fswebcam -d {} -r {}x{} --no-banner'.format(
        device,
        x,
        y,
    )
    cmd = cmd_str.split()
    subprocess.call(cmd + [img_path])


def main():
    pass


if __name__ == '__main__':
    main()
