# Simple Video Cropper

Simple Video Cropper is lightweight python app designed to process small-scale video dataset items, for example those expected by [diffusion-pipe](https://github.com/tdrussell/diffusion-pipe).

<img width="1470" height="977" alt="Снимок экрана 2025-11-21 232507" src="https://github.com/user-attachments/assets/a3b08e84-cf7b-46b1-bf59-f25e6fd2d28c" />

## Usage

You can use the program to make spatio-temporal crops of videos.

The program itself is simply launched with "python simple-video-cropper.py".

The program has an intuitive graphic interface made with python's embedded tkinter.

The video is loaded with Load Video. Then you can create a thin red frame with two mouse clicks. The red frame can be moved by dragging its corners with the mouse, the top corner guides its position on the frame and the bottom corner sets up the frame's size. If you click "Maintain Aspect Ratio", the frame will have the same proportions as you move or resize it. For precision, the crop region can be set manually.

The timeline slider and the start-end-frame boxes is used to encase the video's temporal segment. The "Play" / "Stop" buttons can be used for quick preview.

After the region has been confirmed, you can select to rescale the final output video to target dimensions and to downsample its frames, so it will match precise frame targets. "Pad Last Frame" can optionally repeat the last frame of the video, as diffusion-pipe has a bug that it discards the last frame, though it is needed for Wan total frame calculation. The output video FPS can also be forced.

In the end the "Crop Video" button will save the resulting video to a location.

Before usage make sure to install dependencies via "python -m pip install requirements.txt". All video IO operations come through OpenCV, so ffmpeg installation is not needed.

## License

Copyright Artem Khrapov, 2025.

For usage terms, see LICENSE.
