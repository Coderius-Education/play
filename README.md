# coderius-play
The goal of coderius-play is to help starting programmers to become more capable in programming Python.

## Installation
```bash
pip install coderius-play
```

coderius-play runs on Python 3.11 to 3.15, on Windows, macOS and Linux.

### Raspberry Pi
On a Raspberry Pi with 64-bit Raspberry Pi OS (Bookworm or Trixie), install it
in a virtual environment with the Python that comes with the system:
```bash
python3 -m venv ~/play-env
~/play-env/bin/pip install coderius-play
```

### In the browser
With [pygbag](https://pypi.org/project/pygbag/) a play game runs in the
browser. Name the file `main.py`, put it in a folder of its own and list
coderius-play and pygame-ce at the top, so pygbag loads them:
```python
# /// script
# dependencies = ["coderius-play", "pygame-ce"]
# ///
import play

play.new_text(words="Hello from the browser!")

play.start_program()
```
Then run `pygbag my_game_folder` and open http://localhost:8000. In the
browser `play.start_program()` returns straight away and the page keeps the
game running. Videos are not available there.

## Usage
Please visit [the documentation](https://play.coderius.nl/).

### Playing video
`play.new_video()` shows an `.mp4` on screen, with built-in controls that appear
when the mouse is over it:

```python
import play

video = play.new_video("clip.mp4", width=480, autoplay=True)

@video.when_video_ends
def finished():
    print("that's all folks")

play.start_program()
```

The video can also be driven from code with `video.play()`, `video.pause()`,
`video.seek(10)`, `video.time`, `video.volume`, `video.speed` and `video.loop`.
Video decoding uses [PyAV](https://pypi.org/project/av/), which is installed
along with coderius-play and brings its own FFmpeg, so nothing else is needed.

## Testing
Install the runtime and development dependencies, then run the suite:
```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests
```

CI gates on formatting and linting as well as the tests. To run exactly what
it runs before you open a pull request:
```bash
black --check ./play ./tests
pylint $(git ls-files 'play/*.py' 'play/**/*.py')
pytest ./tests -n auto --runslow --durations=10
```
Tests marked slow (and everything under `tests/stress/`) are skipped unless you
pass `--runslow`.

## Contributing
We welcome contributions! If you'd like to contribute, please follow these steps:

- Fork the repository.

- Create a new branch (git checkout -b feature/your-feature-name).

- Commit your changes (git commit -m 'feat: Add a new feature').

- Push to the branch (git push origin feature/your-feature-name).

- Open a Pull Request.

Good luck and happy coding!

## License
This project is licensed under the [MIT License](LICENSE)

## Acknowledgements
- [Koen](https://github.com/koen1711)
- [Marten Postma](https://github.com/MartenPostma)
