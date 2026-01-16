import pytest

num_frames = 0
max_frames = 100

expected = [0, 128, 255]
actual = []


def test_set_alpha():
    import sys

    sys.path.insert(0, ".")
    import play

    image1 = play.new_image(
        image="tests/objects_attributes/yellow.jpg", size=10, transparency=0
    )
    image2 = play.new_image(
        image="tests/objects_attributes/yellow.jpg", size=10, transparency=50
    )
    image3 = play.new_image(
        image="tests/objects_attributes/yellow.jpg", size=10, transparency=100
    )

    @play.repeat_forever
    def move():
        global num_frames
        global actual
        num_frames += 1

        if num_frames == max_frames:
            actual = [
                image1.image.get_alpha(),
                image2.image.get_alpha(),
                image3.image.get_alpha(),
            ]
            play.stop_program()

    play.start_program()

    for expected_value, actual_value in zip(expected, actual):
        if expected_value != actual_value:
            pytest.fail(
                f"expected alpha to be {expected_value} but the actual value is {actual_value}"
            )


if __name__ == "__main__":
    test_set_alpha()
