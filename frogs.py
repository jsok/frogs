import os
from copy import deepcopy

from PIL import Image, ImageDraw, ImageFont


GGH = ' GreenHead '
GGL = ' GreenLegs '

YYH = 'Yellow Head'
YYL = 'Yellow Legs'

STH = 'StripeyHead'
STL = 'StripeyLegs'

SPH = 'Spotty Head'
SPL = 'Spotty Legs'

# Tiles are clockwise
# Tile = (top, right, bottom, left)

TILES = {
    1: (GGH, GGL, YYL, STH),
    2: (STH, GGH, YYH, YYH),
    3: (SPL, STL, YYH, SPH),
    4: (SPH, GGL, SPL, STL),
    5: (YYL, GGL, SPL, YYL),
    6: (SPH, GGH, SPH, STL),
    7: (YYH, STL, YYL, GGL),
    8: (YYH, SPL, GGH, STH),
    9: (SPL, STL, STH, GGH)
}

PAIRS = [
    {GGH, GGL},
    {YYH, YYL},
    {STH, STL},
    {SPH, SPL}
]

TOP = 'top'
BOTTOM = 'bottom'
LEFT = 'left'
RIGHT = 'right'


class Board(object):
    def __init__(self):
        self.state = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
        ]

    def get_index_matrix(self):
        matrix = []
        for row in self.state:
            matrix.append(map(lambda t: t.number, row))
        return matrix

    def get_tile(self, x, y):
        if 0 <= x < 3 and 0 <= y < 3:
            return self.state[2-y][x]
        else:
            return None

    def set_tile(self, x, y, tile):
        self.state[2-y][x] = tile

    def place_tile(self, tile, x, y):
        for col in self.state:
            for row in col:
                if row and row.number == tile.number:
                    raise Exception("Tile already placed")
        if self.get_tile(x, y):
            raise Exception("Position taken")
        else:
            self.set_tile(x, y, tile)

    def remove_tile(self, x, y):
        self.set_tile(x, y, None)

    def draw(self, filename):
        board = Image.new("RGB", (1500, 1500))

        for y in xrange(2, -1, -1):
            for x in xrange(0, 3, 1):
                tile = self.state[y][x]
                if not tile:
                    img = Image.open('images/Blank.jpg')
                else:
                    img = tile.image()

                pos = (500 * x, 500 * y)
                board.paste(img, box=pos)
        board.save(filename)

    def validate(self):
        invalid = set()
        for y in xrange(0, 3, 1):
            for x in xrange(0, 3, 1):
                if not self.quick_validate_tile(x, y):
                    return False
        return True

    def quick_validate_tile(self, x, y):
        tile = self.get_tile(x, y)
        if not tile:
            return True

        neighbours = [
            # Edge: ((neighbour coords), neighbour edge)
            (TOP, (x, y + 1), BOTTOM),
            (RIGHT, (x + 1, y), LEFT),
            (BOTTOM, (x, y - 1), TOP),
            (LEFT, (x - 1, y), RIGHT)
        ]

        for edge, coords, neighbour_edge in neighbours:
            neighbour = self.get_tile(*coords)
            if not self.is_pair_valid(tile, edge, neighbour, neighbour_edge):
                return False

        return True

    def is_pair_valid(self, tile1, edge1, tile2, edge2):
        if not tile1 or not tile2:
            return True
        return {tile1.edge(edge1), tile2.edge(edge2)} in PAIRS


class Tile(object):
    def __init__(self, number, symbols, rotation=None):
        self.number = number
        self.symbols = symbols
        self.rotation = 0 if rotation is None else rotation

    def __repr__(self):
        return "<Tile %d: rotation=%d symbols=%s>" % (self.number, self.rotation, self.symbols)

    def reset(self):
        self.rotation = 0

    def rotate(self):
        self.rotation += 90

    def edge(self, name):
        lookup = {
            TOP: 0,
            RIGHT: 1,
            BOTTOM: 2,
            LEFT: 3
        }

        rotation_offset = self.rotation / 90
        idx = (lookup[name] - rotation_offset) % 4
        return self.symbols[idx]

    def filename(self):
        return os.path.join('images', "%s.JPG" % self.number)

    def image(self):
        img = Image.open(self.filename())
        img = img.rotate(360 - self.rotation)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(filename='/System/Library/Fonts/Thonburi.ttf', size=100)

        draw.text((200, 200), "[%s]" % self.number, "black", font)

        return img


def solve(board, tiles):
    coords = []
    for y in xrange(0, 3, 1):
        for x in xrange(0, 3, 1):
            coords.append((x, y))

    solved_board = try_tiles_at(board, tiles, coords)
    return solved_board


iterations = 0


def try_tiles_at(board, tiles, coords):
    global iterations

    solutions = []

    if not tiles:
        if board.validate():
            solutions.append(board)
            return solutions
        else:
            return []

    x, y = coords.pop()

    discard = []
    while tiles:
        tile = tiles.pop()
        board.place_tile(tile, x, y)

        # Try all rotations
        for _ in xrange(4):
            tile.rotate()

            #board.draw('iterations/frame%06d.jpg' % iterations)
            iterations += 1

            if board.quick_validate_tile(x, y):
                remaining_tiles = deepcopy(tiles) + deepcopy(discard)
                map(lambda t: t.reset(), remaining_tiles)

                solns = try_tiles_at(deepcopy(board), remaining_tiles, deepcopy(coords))
                if solns:
                    solutions.extend(solns)
                    continue
        else:
            # Tile did not fit regardless of rotation
            board.remove_tile(x, y)
            discard.append(tile)

    return solutions


def build_tiles():
    tiles = []
    for num, symbols in TILES.iteritems():
        tile = Tile(num, symbols)
        tiles.append(tile)

    return tiles


def unique_solutions(solutions):
    from numpy import rot90, array_equal

    matches = {}

    for board1 in solutions:
        m1 = board1.get_index_matrix()

        for board2 in solutions:
            if board1 == board2:
                continue

            m2 = board2.get_index_matrix()

            for _ in range(4):
                m2 = rot90(m2)
                if array_equal(m1, m2):
                    same = matches.get(board1, set())
                    same.add(board2)
                    matches.update({board1: same})

                    same = matches.get(board2, set())
                    same.add(board1)
                    matches.update({board2: same})

    uniques = []
    ignores = set()
    for board, sames in matches.iteritems():
        if board not in ignores:
            uniques.append(board)
        ignores.update(sames)

    return uniques


def main():
    tiles = build_tiles()
    board = Board()
    solutions = solve(board, tiles)

    if solutions:
        print "Total iterations: %d" % iterations
        solutions = unique_solutions(solutions)

        print "Found %d unique solutions" % len(solutions)
        for i, board in enumerate(solutions):
            filename = 'solutions/board%02d.jpg' % i
            print "Drawing to %s" % filename
            board.draw(filename)
    else:
        print "Failed to find solutions"


if __name__ == "__main__":
    main()