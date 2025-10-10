# Hamster Pixel Art Specifications

## Overview
Create 16 pixel art images of a hamster for a running animation on a circular track. The hamster should be depicted in a retro, blocky black and white pixel art style suitable for a dashboard interface.

## Technical Requirements
- **Format**: PNG with transparent background
- **Size**: 32x32 pixels (or 48x48 for higher detail)
- **Style**: Black and white only (no grayscale)
- **Animation**: 16 frames for smooth running motion
- **Naming**: `hamster_01.png` through `hamster_16.png`

## Art Style Guidelines
- **Retro 8-bit aesthetic**: Think classic arcade games
- **High contrast**: Pure black (#000000) on transparent background
- **Blocky pixels**: No anti-aliasing, crisp pixel edges
- **Simple but recognizable**: Clear hamster silhouette
- **Consistent proportions**: Same size hamster across all frames

## Animation Sequence (16 Frames)

### Frames 1-4: Right Leg Forward Cycle
1. **Frame 1**: Starting position - right front paw forward, left back paw forward
2. **Frame 2**: Mid-stride - right front paw touching ground, body slightly compressed
3. **Frame 3**: Push-off - right front paw pushing back, body extended
4. **Frame 4**: Transition - preparing for left leg cycle

### Frames 5-8: Left Leg Forward Cycle  
5. **Frame 5**: Left front paw forward, right back paw forward
6. **Frame 6**: Mid-stride - left front paw touching ground, body slightly compressed
7. **Frame 7**: Push-off - left front paw pushing back, body extended
8. **Frame 8**: Transition - preparing for next right leg cycle

### Frames 9-12: Right Leg Forward Cycle (Variation)
9. **Frame 9**: Similar to Frame 1 but with slight body position variation
10. **Frame 10**: Similar to Frame 2 with body bounce
11. **Frame 11**: Similar to Frame 3 with extended stride
12. **Frame 12**: Transition with slight head bob

### Frames 13-16: Left Leg Forward Cycle (Variation)
13. **Frame 13**: Similar to Frame 5 with body variation
14. **Frame 14**: Similar to Frame 6 with bounce
15. **Frame 15**: Similar to Frame 7 with extended stride  
16. **Frame 16**: Return to starting position (loops back to Frame 1)

## Hamster Features to Include
- **Body**: Rounded, chubby hamster silhouette
- **Head**: Large relative to body, with small ears
- **Eyes**: Simple black dots (2-3 pixels)
- **Paws**: Four legs with simple paw shapes
- **Tail**: Small, stubby tail
- **Posture**: Running/trotting position

## Animation Notes
- The hamster should appear to be running clockwise around a circular track
- Body should have subtle up-down bouncing motion
- Legs should show clear running gait pattern
- Head can have slight bobbing motion for personality
- Ears may flutter slightly with movement

## Usage Context
These sprites will be used in a web dashboard where the hamster runs around a circular track. Every minute (when the hamster crosses the start line), a screenshot is taken. The animation should loop smoothly and be visible against a retro black and white dashboard background.

## Reference Style
Think of classic games like:
- Original Super Mario Bros sprites
- Pac-Man character design
- Early arcade game aesthetics
- 1-bit art style (pure black and white)

The hamster should be cute and recognizable while maintaining the stark, high-contrast retro pixel aesthetic.

