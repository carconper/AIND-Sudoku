#from utils import *
import logging

logging.basicConfig(level=logging.ERROR)

assignments = []
rows = 'ABCDEFGHI'
cols = '123456789'

def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [row + col for row in A for col in B]

# boxes contains all the coordenates of our 9x9 grid
boxes = cross(rows, cols)
# row_units contains all the row units
row_units = [[boxes[i + j * 9] for i in range(9)] for j in range(9)]
# col_units contains all the column units
col_units = [[boxes[i * 9 + j] for i in range(9)] for j in range(9)]
# sq_units contains all the 3x3 square units
sq_units = [cross(rg, cg) for rg in ['ABC', 'DEF', 'GHI'] for cg in ('123', '456', '789')]
# diag_units contains the 2 big diagonal units
diag_units = [[row + col for row, col in zip(rows, cols)], [row + col for row, col in zip(rows, cols[::-1])]]
# all_units contains all the units in our 9x9 grid
all_units = row_units + col_units + sq_units + diag_units
# box_units is a dictionary in which the key references each box
#   and the value represents a list of lists containing all the units
#   that box is part of. Used to build the peers data structure
box_units = dict((box, [unit for unit in all_units if box in unit] )for box in boxes)
# peers is a dictionary in which the key references each box in the grid
#   and the value is a list of peer boxes of the key box
peers = dict((box, set(sum(box_units[box], [])) - set([box])) for box in boxes)


def assign_value(values, box, value):
    """
    Please use this function to update your values dictionary!
    Assigns a value to a given box. If it updates the board record it.
    """
    # Don't waste memory appending actions that don't actually change any values
    if values[box] == value:
        return values
    values[box] = value
    if len(value) == 1:
        assignments.append(values.copy())
    return values


def display(values):
    """
    Display the values as a 2-D grid.
    Args:
        values(dict): The sudoku in dictionary form
    """
    width = 1+max(len(values[s]) for s in boxes)
    line = '+'.join(['-'*(width*3)]*3)
    for r in rows:
        print(''.join(values[r+c].center(width)+('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF': print(line)
    return


def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    Args:
        grid(string) - A grid in string form.
    Returns:
        A grid in dictionary form
            Keys: The boxes, e.g., 'A1'
            Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """
    assert len(grid) == 81, 'Input grid must be a string of lenght 81 (9x9)'
    values = {}
    for i, box in enumerate(boxes):
        values[box] = (grid[i] if grid[i] != '.' else '123456789')
    return values


def eliminate(values):
    """
    Strategy that eliminates possibilities from peers for the boxes with final value
    Args:
        values(dict): The sudoku in dictionary form
    Returns:
        values(dict): The reduced sudoku in dictionary form
    """
    solved_values = [box for box in values.keys() if len(values[box]) == 1]
    for box in solved_values:
        digit = values[box]
        for peer in peers[box]:
            values[peer] = values[peer].replace(digit,'')
    return values


def only_choice(values):
    """
    Strategy that finds the final value for the boxes with multiple possibilities
        that are the only ones within a given unit that can have that value
    Args:
        values(dict): The sudoku in dictionary form
    Returns:
        values(dict): The reduced sudoku in dictionary form
    """
    digits = '123456789'
    for unit in all_units:
        for digit in digits:
            dboxes = [box for box in unit if digit in values[box]]
            if len(dboxes) == 1:
                values = assign_value(values, dboxes[0], digit)
    return values


def find_naked_twins(values):
    """Find all the naked_twins within the values dictionary
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
    Returns:
        naked_twins_list: A list containing the naked_twins found
    """
    naked_twins_list = []
    for unit in all_units:
        for unit_peer in unit:
            if len(values[unit_peer]) == 2:
                for up in unit:
                    if values[up] == values[unit_peer]:
                        if up != unit_peer:
                            naked_twins_list.append((unit_peer, up, unit))
                            break
    return naked_twins_list


def eliminate_naked_twins(values, naked_twins_list):
    """Eliminate the naked_twins from the values dictionary
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
        naked_twins_list: a list containing the naked_twins to be removed
    Returns:
        the values dictionary with the naked twins eliminated from peers
    """
    for nt in naked_twins_list:
        if len(values[nt[0]]) == 2 and len(values[nt[1]]) == 2:
            for peer in nt[2]:
                if peer != nt[0] and peer != nt[1]:
                    values[peer] = values[peer].replace(values[nt[0]][0], '')
                    values[peer] = values[peer].replace(values[nt[0]][1], '')
    return values


def naked_twins(values):
    """Eliminate values using the naked twins strategy.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}
    Returns:
        the values dictionary with the naked twins eliminated from peers.
    """
    # Find all instances of naked twins
    naked_twins_list = find_naked_twins(values)
    # Eliminate the naked twins as possibilities for their peers
    values = eliminate_naked_twins(values, naked_twins_list)
    return values


def reduce_puzzle(values):
    """
    A wrapping method that takes care of calling all the reduction strategies implemented
    Args:
        values(dict): The sudoku in dictionary form
    Returns:
        values(dict): The reduced sudoku in dictionary form
    """
    # The reduction consist now on 3 strategies:
    #   1. Elimination
    #   2. Naked Twins strategy
    #   3. Only choice

    # Reduce the puzzle as much as possible by making sure we stop
    #   when no more reductions can be performed
    stalled = False
    while not stalled:
        # Compute number of boxes with final values before reduction
        before = len([box for box in boxes if len(values[box]) == 1])
        # STEP1. Eliminate possibilities from peer boxes
        values = eliminate(values)
        # STEP2. Apply the naked_twins strategy
        values = naked_twins(values)
        # STEP3. Determine if there is any box that can be set as final
        values = only_choice(values)
        # Compute number of boxes with final value after reduction
        after = len([box for box in boxes if len(values[box]) == 1])
        # If before is equal to after (no reduction has happened in this iteration)
        #   we are stalled and we have to exit the while loop
        if before == after:
            stalled = True
        # If at any point any of the values in a box is empty (len == 0)
        #   it means we selected a value for a box (within the search
        #   strategy) that didnt led to a valid solution, so we need to 
        #   exit recursion by returning False
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values


def search(values):
    # First call the strategies to reduce our puzzle
    values = reduce_puzzle(values)
    # If the value returned from reduction is False, we hit a non valid
    #   solution, so exit recursion
    if values is False:
        return False
    # If we managed to solve the puzzle by the reduction, return the solution
    if all(len(values[box]) == 1 for box in boxes):
        return values
    # If we havent found a solution yet, find one of the boxes with less 
    #   possibilities left
    n, box = min((len(values[box]), box) for box in boxes if len(values[box]) > 1)
    # And enter the recursion for each of the possibilities within that box
    for value in values[box]:
        new_values = values.copy()
        new_values[box] = value
        attempt = search(new_values)
        if attempt:
            return attempt


def solve(grid):
    """
    Find the solution to a Sudoku grid.
    Args:
        grid(string): a string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        The dictionary representation of the final sudoku grid. False if no solution exists.
    """
    # 1. Setting up and Encoding the input grid into the board 
    values = grid_values(grid)
    # 2. Explore all the options by calling the search recursive method 
    #   (This method will be responsible of calling the reduce_puzzle
    #    strategies)
    values = search(values)
    # We finally return the solved puzzle
    return values


if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    diag_sudoku_grid = '9.1....8.8.5.7..4.2.4....6...7......5..............83.3..6......9................'
    diag_sudoku_grid = '......9.....6.....3.........91.2..7....1.....5.....2.1......4..2..4..5...7.....1.'
    display(solve(diag_sudoku_grid))

    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
