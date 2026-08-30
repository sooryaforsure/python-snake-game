# Snake Game 🐍

![Gameplay Screenshot](assets\screenshot1.png)
![Gameplay Screenshot](screenshot2.png)

A polished, fully featured classic Snake Game built with Python and Pygame Community Edition (`pygame-ce`).

## How to Play

**Objective:** Guide the snake to eat food, grow as long as possible, and achieve the highest score without running into the walls or your own tail!

### Controls
*   **Arrow Keys (↑ ↓ ← →):** Move the snake
*   **SPACE:** Start Game / Pause & Resume / Play Again

### Items & Mechanics
*   🍎 **Regular Apple:** Grants +1 Score and +1 Length. Increases your movement speed slightly.
*   ✨ **Golden Apple:** A rare, pulsing treat that lasts for only 4 seconds. Grants +3 Score and +3 Length. Triggers a larger speed boost and a special particle burst!
*   🧊 **Ice Cube:** A lifesaver that only appears once you reach a score of 15. Lasts for 5 seconds. Eating it doesn't give you points, but it significantly **slows down** the snake, buying you precious reaction time.

---

## Technical Details

### $O(1)$ Time Complexity Movement with `deque`

To ensure the game runs blazingly fast and scales without lag, the snake's body is implemented using a Double-Ended Queue (`collections.deque`), alongside a Hash Set (`set`).

**Why a Deque?**
If we used a standard Python list (array) to represent the snake's body, every time the snake moved forward, we would have to shift the position of *every single segment* in memory. As the snake gets longer, this operations becomes increasingly slow ($O(N)$ time complexity).

By using a `deque`, we completely avoid shifting elements. When the snake moves, we simply:
1. Calculate the new coordinate for the head.
2. Push the new head to the front of the queue using `appendleft()` (an **$O(1)$** operation).
3. If no food was eaten, we remove the tail from the back using `pop()` (another **$O(1)$** operation).

This guarantees that movement takes the exact same amount of computing time regardless of whether the snake is 3 segments long or 3,000 segments long!

**Hash Set for Collision:**
We also maintain a `set` of the snake's currently occupied coordinates. This allows us to perform self-collision checks and find valid empty spaces for food spawns in **$O(1)$** average time, completely avoiding expensive linear scans.

