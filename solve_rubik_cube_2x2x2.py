#!/usr/bin/env python3

'''
Colors: yellow (Y), green (G), blue (B), red (R), orange (O), white (W)

Let's look at the cube from the front:

     +-+-+
     |1|2|
     +-+-+
     |3|4|
     +-+-+

Data entry:

    1) enter colors (in the order as above) from the front side
    2) rotate cube - bring right side to the front
    3) enter colors
    4) rotate cube - bring (the now) right side to the front
    5) enter colors
    6) rotate cube - bring (the now) right side to the front
    7) enter colors
    8) rotate cube - bring (the now) right side to the front
       - you should be looking at the same side as in 1)
    9) rotate cube - bring the top side to the front
    10) enter colors
    11) rotate cube - bring the bottom side to the front
       - you should be looking at the same side as in 1) and 8)
    12) rotate cube - bring the bottom side to the front
    13) enter colors
        - now all sides should be entered

Usage:

    $ ./solve_rubik_cube_2x2x2.py   w b g y  o y r w  o g r g  o b r w  y b r w  o b y g
    ...
    Actions: twist_to_left rotate_to_left rotate_down twist_to_right rotate_to_left
    rotate_up twist_to_left twist_to_left rotate_down twist_to_right rotate_down
    rotate_to_right twist_to_left rotate_down rotate_to_left rotate_up twist_to_left
    twist_to_left rotate_to_left rotate_down twist_to_left rotate_up twist_to_right
    rotate_to_right rotate_down twist_to_left rotate_up twist_to_left rotate_down
    twist_to_right rotate_down rotate_to_left rotate_down twist_to_left rotate_down
    twist_to_left twist_to_left rotate_down twist_to_left twist_to_left rotate_down
    twist_to_left rotate_to_left rotate_down twist_to_left twist_to_left rotate_down
    twist_to_left twist_to_left
    Result: BBBBRRRRGGGGOOOOYYYYWWWW
'''


import argparse
from collections import Counter
import sys

all_colors = tuple('YGBROW')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max-depth', '-d', type=int, default=200)
    p.add_argument('color', nargs=24)
    args = p.parse_args()
    colors = normalize_entered_colors(args.color)
    try:
        check_entered_colors(colors)
    except Exception as e:
        sys.exit(str(e))
    try_solve(colors, max_depth=args.max_depth)


def try_solve(start_colors, max_depth):
    # Inspired by Dijkstra algorithm. But the edge weights are not always positive
    # so I guess it does not produce globally optimal (shortest path) output.
    from heapq import heappop, heappush
    actions = [
        ('rotate_to_left', rotate_to_left),
        ('rotate_to_right', rotate_to_right),
        ('rotate_up', rotate_up),
        ('rotate_down', rotate_down),
        ('twist_to_left', twist_to_left),
        ('twist_to_right', twist_to_right),
    ]
    start_colors = ''.join(start_colors)
    heap = []
    heappush(heap, (int(10**9), tuple(), start_colors))
    already_processed = set()
    n = 0
    while True:
        priority, path, colors = heappop(heap)
        if colors in already_processed:
            continue
        already_processed.add(colors)
        for name, action in actions:
            if len(path) >= 2 and name == path[-1] and name == path[-2]:
                continue
            next_colors = action(colors)
            next_path = path + (name, )
            if is_final(next_colors):
                print('Actions:', ' '.join(next_path))
                print('Result:', next_colors)
                return
            next_priority = min(priority, chaos_level(next_colors) * 25) + len(next_path)
            heappush(heap, (next_priority, next_path, next_colors))
        n += 1
        if n % 5000 == 0:
            print(n, len(heap), len(already_processed), heap[0][0], len(heap[0][1]), file=sys.stderr)


def is_final(colors):
    for i in range(0, 24, 4):
        for k in range(i+1, i+4):
            if colors[i] != colors[k]:
                return False
    return True


def chaos_level(colors):
    front = colors[:4]
    right = colors[4:8]
    back = colors[8:12]
    left = colors[12:16]
    top = colors[16:20]
    bottom = colors[20:24]
    return sum([
        len(set(front)),
        len(set(right)),
        len(set(back)),
        len(set(left)),
        len(set(top)),
        len(set(back)),
    ])


def normalize_entered_colors(colors):
    return ''.join(c.upper()[0] for c in colors)


def check_entered_colors(colors):
    for c in colors:
        if c not in all_colors:
            raise Exception('Unknown color: {}'.format(c))
    counter = dict(Counter(colors))
    expected_counts = {c: 4 for c in all_colors}
    if counter != expected_counts:
        raise Exception('Count mismatch: {} != {}'.format(counter, expected_counts))


def rotate_side_cw(side):
    '''
    Rotate: 0 1 -> 2 0
            2 3    3 1
    '''
    assert len(side) == 4
    return side[2] + side[0] + side[3] + side[1]


assert rotate_side_cw('1234') == '3142'


def rotate_side_ccw(side):
    '''
    Rotate: 0 1 -> 1 3
            2 3    0 2
    '''
    assert len(side) == 4
    return side[1] + side[3] + side[0] + side[2]


assert rotate_side_ccw('1234') == rotate_side_cw(rotate_side_cw(rotate_side_cw('1234')))


def rotate_to_left(colors):
    front = colors[:4]
    right = colors[4:8]
    back = colors[8:12]
    left = colors[12:16]
    top = colors[16:20]
    bottom = colors[20:24]
    assert front + right + back + left + top + bottom == colors
    return (
        # front side
        right +
        # right side
        back +
        # back side
        left +
        # left side
        front +
        # top side
        rotate_side_cw(top) +
        # bottom side
        rotate_side_ccw(bottom)
    )

def rotate_to_right(colors):
    front = colors[:4]
    right = colors[4:8]
    back = colors[8:12]
    left = colors[12:16]
    top = colors[16:20]
    bottom = colors[20:24]
    assert front + right + back + left + top + bottom == colors
    return (
        # front side
        left +
        # right side
        front +
        # back side
        right +
        # left side
        back +
        # top side
        rotate_side_ccw(top) +
        # bottom side
        rotate_side_cw(bottom)
    )


def side_upside_down(side):
    '''
    0 1 -> 3 2
    2 3    1 0
    '''
    assert len(side) == 4
    return side[3] + side[2] + side[1] + side[0]


def rotate_up(colors):
    front = colors[:4]
    right = colors[4:8]
    back = colors[8:12]
    left = colors[12:16]
    top = colors[16:20]
    bottom = colors[20:24]
    assert front + right + back + left + top + bottom == colors
    return (
        # front side
        bottom +
        # right side
        rotate_side_cw(right) +
        # back side
        side_upside_down(top) +
        # left side
        rotate_side_ccw(left) +
        # top side
        front +
        # bottom side
        side_upside_down(back)
    )


def rotate_down(colors):
    front = colors[:4]
    right = colors[4:8]
    back = colors[8:12]
    left = colors[12:16]
    top = colors[16:20]
    bottom = colors[20:24]
    assert front + right + back + left + top + bottom == colors
    return (
        # front side
        top +
        # right side
        rotate_side_ccw(right) +
        # back side
        side_upside_down(bottom) +
        # left side
        rotate_side_cw(left) +
        # top side
        side_upside_down(back) +
        # bottom side
        front
    )


def twist_to_left(colors):
    '''
    Twist top side to the left.
        +-+-+
    <-- |1|2| <--
        +-+-+
        |3|4|
        +-+-+
    '''
    assert len(colors) == 24
    front = colors[:4]
    right = colors[4:8]
    back = colors[8:12]
    left = colors[12:16]
    top = colors[16:20]
    bottom = colors[20:24]
    assert front + right + back + left + top + bottom == colors
    return (
        # front side
        right[:2] +
        front[2:] +
        # right side
        back[:2] +
        right[2:] +
        # back side
        left[:2] +
        back[2:] +
        # left side
        front[:2] +
        left[2:] +
        # top side
        rotate_side_cw(top) +
        # bottom side
        bottom
    )


def test_twist_to_left():
    before = ''.join('g o w y y g b b y y r o b w b o r r r g g o w w'.upper().split())
    after = ''.join('y g w y y y b b b w r o g o b o r r g r g o w w'.upper().split())
    check_entered_colors(before)
    check_entered_colors(after)
    assert twist_to_left(before) == after


test_twist_to_left()


def twist_to_right(colors):
    return twist_to_left(twist_to_left(twist_to_left(colors)))


if __name__ == '__main__':
    main()
