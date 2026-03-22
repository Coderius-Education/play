# Bug Audit — Coderius-Education/play

> Automated scan performed March 2026. All bugs verified against source at HEAD (master).

## Critical

### BUG 13 & 14 — `callback/collision_callbacks.py` — KeyError on unregistered shapes
`_handle_collision` accesses `self.shape_registry[shape_a.collision_type]` without checking if the key exists. Any shape not registered (e.g. wall segments) causes a `KeyError` crash. The wall-detection logic is entirely broken because the crash happens before the `is None` check ever runs.
**Fix:** use `.get()` instead of direct dict access.

### BUG 15 — `objects/components.py` — Negated condition disables ALL software collision callbacks
```python
if sprite.physics and shape_b.physics:
    continue   # skips when BOTH have physics — i.e. always, after init
```
This skips all entries in `_update_sprite_collisions` once sprites are initialised, making `when_touching` dead code in the software path.
**Fix:** flip to `if not sprite.physics or not shape_b.physics`.

---

## High

### BUG 5–10 — `objects/sound.py` — Multiple crashes
- `volume` getter: calls `self.sound.get_volume()` after logging a warning when `self.sound is None` — crashes with `AttributeError`.
- `volume` setter: called in `__init__` before `load()` — `self.sound` is `None`, crashes on `set_volume`.
- `play()`: no `return` after "no sound loaded" warning; also crashes if `find_channel()` returns `None`.
- `play()` resume logic: calls `find_channel()` (returns a *free* channel) even when resuming a paused sound — the paused channel is lost, unpause fires on the wrong channel.
- `pause()` / `stop()`: call `self.channel.get_busy()` / `self.channel.stop()` without guarding against `self.channel is None`.
- `length` property: calls `self.channel.get_sound()` when channel may be `None`.

### BUG 11 & 12 — `core/__init__.py` + `io/screen.py` — `when_resized` is dead code
`pygame.VIDEORESIZE` is never handled in `_handle_pygame_events`, so `CallbackType.WHEN_RESIZED` is never dispatched. The `when_resized` decorator registers callbacks that can never fire.

### BUG 18 — `io/controllers.py` — Wrong argument passed to button callback
`wrapper` calls `run_async_callback(async_callback, [], [], ["button"], button_cb)` — passes the literal list `["button"]` as the first arg instead of the actual button value. The `any_wrapper` path does this correctly.

### BUG 3 — `core/sprites_loop.py` — Hidden sprites lose `stopped_touching` callbacks
When `sprite.is_hidden`, `run_sprite_callbacks` is skipped entirely. If a sprite is touching something and then hidden, the `when_stopped_touching` callback is silently dropped forever.

---

## Medium

### BUG 24 — `api/utils.py` — `WHEN_PROGRAM_START` fires after first game frame
`run_callbacks(WHEN_PROGRAM_START)` creates tasks before `loop.run_forever()` is called. These tasks execute after the first game loop tick, so sprites positioned in `@when_program_starts` flash at their default position for one frame.

### BUG 27 — `api/utils.py` — `pygame.quit()` called twice on `stop_program()`
`stop_program()` calls `pygame.display.quit()` + `pygame.quit()`, and then the `finally` block in `start_program()` calls `pygame.quit()` again. This can corrupt re-initialisation attempts.

### BUG 31 — `objects/components.py` — Dual dispatch may fire `when_touching` callback twice
Both the physics path (`collision_registry`) and software path (`callback_manager`) dispatch the same callback. On a physics collision, the callback may fire twice per frame.

### BUG 34 — `io/keypress.py` — Held keys fire `when_key_pressed` every frame
`KeyboardState.pressed` is never cleared, so held keys fire callbacks at the game loop rate (~60/s) rather than the pygame key-repeat rate. `when_key_pressed` behaves as "while key held" rather than "on key press".

### BUG 19 — `core/controller_loop.py` — `buttons_released` cleared twice; `buttons_pressed` never cleared on disconnect
`buttons_released.clear()` is called at frame start (in `clear()`) and again at the end of `handle_controller`. `buttons_pressed` is never cleared on controller disconnect/game reset.

### BUG 20 — `db/__init__.py` — `set_data` raises KeyError for new nested keys
`set_data("new:nested:key", value)` raises `KeyError` if any intermediate key doesn't exist. `get_data` silently creates missing keys.
**Fix:** replace `raise KeyError` with `target[k] = {}`.

### BUG 1 — `core/mouse_loop.py` — No guaranteed ordering between global and sprite click callbacks
`WHEN_CLICKED` (global) and `WHEN_CLICKED_SPRITE` are dispatched via different code paths with no defined ordering guarantee.

---

## Low

### BUG 35 — `objects/image.py` — `image_filename` getter always returns `None`
The getter unconditionally returns `None`. The original filename is discarded after load.

### BUG 16 — `loop.py` — Wrong Python version bracket for event loop policy
`asyncio.set_event_loop_policy(DefaultEventLoopPolicy())` is applied for `>= 3.14`, where it's deprecated. Should be applied for `< 3.14`.

### BUG 17 — `io/controllers.py` — Dict used where tuple intended
`buttons = {"any": None}` then `*buttons` unpacks dict keys. Works accidentally but is misleading. Should be `buttons = ("any",)`.

### BUG 28 — `core/game_loop_wrapper.py` — `raise e` loses traceback
`listen_to_failure` uses `raise e` instead of bare `raise`, dropping the original traceback context.

### BUG 26 — `objects/sprite.py` — `width`/`height` return 0 before first `update()`
`self.rect` is `pygame.Rect(0,0,0,0)` until the first game loop iteration. `left`, `right`, `top`, `bottom` are all incorrect before then.

### BUG 33 — `setup.py` — Classifier claims Python 3.7, requires 3.10+
```python
"Programming Language :: Python :: 3.7"  # wrong
python_requires=">=3.10"
```

### BUG 22 — `objects/box.py` — Mismatched corner radius on inner fill rect
For `border_radius < border_width`, the inner rect gets `border_radius=0` (sharp corners) while the outer border is rounded.

### BUG 29 — `utils/__init__.py` — Dual transparency systems conflict
`color_name_to_rgb` accepts a `transparency` parameter that conflicts with the per-sprite `set_alpha()` system.

### BUG 30 — `utils/async_helpers.py` — Warning object logged instead of string
`play_logger.warning(warning.message)` passes a `Warning` object; original stacklevel info is also lost.

### BUG 21 — `objects/circle.py` — Redundant field init inconsistent with `Box`
`Circle.__init__` manually sets `_is_clicked`, `_is_hidden`, `physics = None` which `Sprite.__init__` already does. `Box` doesn't do this — diverging subclass implementations.
