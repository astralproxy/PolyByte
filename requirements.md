# Requirements for Adding a Library Game

These instructions are for an agent implementing a new PolyByte library game. Add a complete, playable game; do not stop at a proposal or placeholder.

## Files to change

1. Add one self-contained game file under `Library/`, using a unique lowercase kebab-case filename such as `my-game.html`.
2. Put its metadata in the `microfeed` HTML comment described below.
3. Do not edit `Library/manifest.json` or modify the host/shared API unless the request explicitly requires it.

Before editing, inspect at least one existing game to follow the current format and conventions.

## Metadata for manifest sync

At the top of the game file, add a valid JSON metadata comment for the post-integration manifest sync:

```html
<!-- microfeed: {"title":"My Game","icon":"M","description":"A short, clear description of the game.","tags":{"Puzzle":1,"Precision":0.4}} -->
```

- The filename stem becomes the game ID; choose a unique filename.
- Keep the comment's title identical to `window.GameMeta.title`.
- Use a concise description under 140 characters and a suitable icon.
- Use only these tag names: `Asymmetric`, `Chance`, `Competitive`, `Cooperative`, `Endless`, `Endurance`, `Memory`, `Minimal`, `Physics`, `Precision`, `Puzzle`, `Racing`, `Reflex`, `Rhythm`, `Sorting`, `Spatial`, `Sports`, `Strategy`, `Survival`, and `Turn-Based`.
- Tag weights must be numbers in `(0, 1]`. Use only the few tags that meaningfully describe the game.

After integration, the maintainer syncs `Library/manifest.json` by running `python update_manifest.py` from the repository root. Do not perform this integration step as part of implementing the game.

## Game file and sandbox

- Keep the game self-contained in its HTML file; do not add dependencies or make network requests.
- The host loads the file into a sandboxed iframe and injects `window.PARAMS`, the SDK, and a 360 x 640 canvas with id `c`. Do not add a second canvas or replace the injected host setup.
- `window.PARAMS` contains `hue`, `seed`, and `theme`. Use the seed for repeatable randomness and the theme values where appropriate.
- Do not access the parent window, host DOM, cookies, or storage. Do not use `postMessage` directly; the host SDK handles communication.
- Do not start a separate animation loop. The host calls the update and render functions.

## Required API

Define `window.GameMeta` and all four required global functions before the file finishes loading:

```js
window.GameMeta = {title: 'My Game', gameLength: 15000};

function updateGame(dt) { /* advance game state; dt is seconds */ }
function handleInput(event) { /* process normalized host input */ }
function renderAll(ctx) { /* draw one frame using the supplied canvas context */ }
function getResult() {
  return {
    score: 0,
    timeElapsed: 0,
    completionPercent: 0,
    customData: {}
  };
}
```

- `gameLength` is in milliseconds. Design for 10-30 seconds; the host defaults to 15 seconds and clamps the declared value to that range.
- `updateGame(dt)` receives elapsed time in seconds. Use it for simulation and game timers rather than a separate interval or animation loop.
- `handleInput(event)` receives one of:
  - `{type: 'ACTION_PRIMARY', x, y}` for tap/primary action.
  - `{type: 'ACTION_SECONDARY', x, y}` for hold/secondary action.
  - `{type: 'DIRECTIONAL_VECTOR', x, y, active}` for drag or directional input; `x` and `y` are in `-1..1`.
  - For the two action events, `x` and `y` are normalized to `0..1`.
- `renderAll(ctx)` must draw the current state to the supplied 2D context. It should not advance game state.
- `getResult()` must always return an object with finite numeric `score`, `timeElapsed`, and `completionPercent` values, plus an object-valued `customData`. Report `timeElapsed` in seconds and `completionPercent` in `0..100`.

## Lifecycle and ending

- `initGame(params)` is optional. If defined, the host calls it once at game start with `window.PARAMS`.
- `onEndGame()` is optional. The host calls it when the session timer expires or the game requests an early end; use it to finalize state before results are read.
- To end early, call `window.Platform.endGame()` (or its `window.endGame()` alias). The host then calls `onEndGame()`, reads `getResult()`, and shows the result card. Avoid repeatedly requesting the end.
- The host automatically ends the game at its declared session limit. Keep the game in a valid final state so `getResult()` works both after an early end and a timeout.
- The host treats missing required functions, uncaught errors, initialization timeout, frozen updates, or a missing final result as failures. Handle expected edge cases explicitly and avoid throwing during update, input, render, or result calculation.

## Validation checklist

- Confirm the metadata comment is valid JSON and matches the game title and supported tag names.
- Confirm the file defines all four required functions; `update_manifest.py` skips files that are missing them.
- Serve the repository over HTTP (for example, `python -m http.server` from the repository root) and load the host page; do not test by opening `index.html` directly as a `file://` URL.
- Launch the game from the library and from the random-play control.
- Exercise primary, secondary, and directional input where the game uses them.
- Verify the early-end path, timer-expiry path, result values, and any replay behavior.
- Check the browser console for errors and confirm the game does not require network access or host-page changes.
