# coderius-play
The goal of coderius-play is to help starting programmers to become more capable in programming Python.

## Installation
```bash
pip install coderius-play
```

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
