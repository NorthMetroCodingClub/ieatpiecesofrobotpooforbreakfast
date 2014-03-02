import rg
import random

class Robot:
    # Default constructor to initialize crap.
    def __init__(self):
        # For realzies with this garbage.
        self._act_attack = 'attack'
        self._act_guard = 'guard'
        self._act_move = 'move'
        self._act_suicide = 'suicide'
        self._suicide_hp = 10
        # Can change this to whatevs...
        self._opp_suicide_hp = 40
        self._opp_suicide_enemy_count = 3
        # We can add more probabilities if we end up with more roles.  And find a tidier way to assign them.
        self._ranger_probability = 0.4
        # Need a better name than this.
        self._ranger_neighborhood_offset = 3
        # Rangers are badasses that will do their toilet business right in the open.
        self._rangers = []
        self._grunts = {}
        # Grunts organize themselves into units at specific locations.
        self._grunt_locations = []

        # Let's figure out some random points for our units to gather at.
        # For simplicity sake, we use an inner grid with the same number of rows and columns.
        # Might even be able to use this for point density analysis at some point to mitigate edge effects.
        sub_grid_start = 4
        sub_grid_end = 14
        grunt_location_count = 5

        # What if there is an enemy or group of enemies at the unit location?
        # I guess we can just keep trying to converge on it.
        while grunt_location_count > 0:
            grunt_location = (random.randrange(sub_grid_start, sub_grid_end), 
                random.randrange(sub_grid_start, sub_grid_end))

            if grunt_location not in self._grunt_locations:
                self._grunt_locations.append(grunt_location)

                grunt_location_count -= 1

    def act(self, game):
        # Make sure all the robots know what their role is.  Can probably optimize this to
        # only fire when we've reached a turn that spawns new robots.
        self.__set_robot_roles(game)

        adjacent_enemies = self.__get_adjacent_enemies(game, self.location)

        # Enemies, sire!
        if len(adjacent_enemies) > 0:
            # 1. Commit desperate suicide - if we're on our last leg.
            # Todo - check how many turns are left and if suicide will actually 
            # take out any enemy robots.  We don't want to sacrifice one of our
            # dudes near the end of the game if it won't reduce the number of enemies
            # by at least one.
            # Also, right now, we are killing ourselves every time we get in a fight to the death.
            # Is that wise?  What if we are the survivor?  Even with a small amount of HP, it is worth staying alive.
            if self.hp <= self._suicide_hp:
                return [self._act_suicide, self.location]

            # 2. Commit opportunistic suicide - if we're surrounded by a bunch of baddies.
            # Not sure how frequently this will occur because if it's 4 dudes grinding on you,
            # they can knock off up to 40 HP in a turn and if we're waiting for a certain amount
            # of health, we could be dead before we get a chance to pull the pin.
            if len(adjacent_enemies) >= self._opp_suicide_enemy_count and \
                self.hp <= self._opp_suicide_hp:
                return [self._act_suicide, self.location]
            
            # 3. Retreat!!
            # If we're in a death slot, get the hell out of there.
            if len(adjacent_enemies) > 1:
                friendly_adjacent_locations = \
                    self.__get_friendly_adjacent_locations(game, self.location)

                if len(friendly_adjacent_locations) > 0:
                    # Move to first friendly location in array.
                    return [self._act_move, friendly_adjacent_locations[0]]
                else:
                    # Get in the fetal position.  Or should we attack and go out gloriously?
                    return [self._act_guard, self.location]

            # 4. Attack!!
            # Sort array on robot HP to attack weakest enemies first.
            # We want to dispatch dudes on their last leg.
            sorted_enemies = sorted(adjacent_enemies.iteritems(), key=lambda x: x[1].hp)

            return [self._act_attack, sorted_enemies[0][0]]

        # 5. Move it!
        if self.robot_id in self._grunts.iterkeys():
            next_location = rg.toward(self.location, self._grunts[int(self.robot_id)])

            return self.__act_cautious_move(game, next_location)
        # Could explicitly check for rangers here, but what if some robots are unaccounted for?
        # Shouldn't happen if i had any talent as a programmer...
        # Anyway, I'd rather they do something than just stand around with their metallic thumbs up their asses.
        else:
            # Find the weakest enemy in our neighbhoorhood and pursue them.
            target_neighborhood = self.__get_neighborhood(
                self.location, self._ranger_neighborhood_offset)

            weakest_enemy = self.__get_weakest_enemy(game, target_neighborhood)

            # If there aren't any enemies in our neighborhood, check the whole arena.
            if weakest_enemy is None:
                weakest_enemy = self.__get_weakest_enemy(game)

            # Should usually expect there to be some enemies on the board, but just in case.
            if weakest_enemy is not None:
                next_location = rg.toward(self.location, weakest_enemy[0])

                if len(self.__get_adjacent_enemies(game, next_location)) <= 1:
                    return self.__act_cautious_move(game, next_location)

            # If our next move is into a death slot or no enemies, let's just chill for a sec and guard.
            return [self._act_guard, self.location]

        # Default behavior.  For now.
        return [self._act_guard, self.location]

    def __set_robot_roles(self, game):
        for robot in game['robots'].itervalues():
            # If if if if... suck it.
            if robot.player_id == self.player_id:
                if self.robot_id not in self._rangers and \
                    self.robot_id not in self._grunts:
                    if random.random() <= self._ranger_probability:
                        self._rangers.append(self.robot_id)
                    else:
                        # Find closest unit and assign robot to it.
                        grunt_location_distances = {}

                        for grunt_location in self._grunt_locations:
                            grunt_location_distances[grunt_location] = \
                                rg.dist(grunt_location, self.location)

                        self._grunts[int(self.robot_id)] = min(grunt_location_distances, 
                            key=lambda key: grunt_location_distances[key])

        # Todo: clean up deceased robots from roles.

    #Todo: resolve idiots constantly trying to enter the same cell.
    def __act_cautious_move(self, game, move_location):
        # First check if there is already someone at the location we want to move into.
        for location, robot in game.robots.iteritems():
            if location == move_location:
                return [self._act_guard, self.location]

        # Next check if the move location is surrounded by at least two enemies.
        if len(self.__get_adjacent_enemies(game, move_location)) > 1:
            return [self._act_guard, self.location]
        else:
            return [self._act_move, move_location]

    def __get_adjacent_enemies(self, game, location):
        adjacent_enemies = {}

        for robot_location, robot in game.robots.iteritems():
            if robot.player_id != self.player_id:
                # Should we use rg.settings.attack_range instead of hardcoding a value of 1 here?
                if rg.dist(robot_location, location) <= 1:
                    adjacent_enemies[robot_location] = robot

        return adjacent_enemies

    def __get_friendly_adjacent_locations(self, game, location, max_adjacent_enemy_count = 1):
        friendly_adjacent_locations = []
        valid_adjacent_locations = rg.locs_around(
            location, filter_out=('invalid', 'obstacle', 'spawn'))

        for adjacent_location in valid_adjacent_locations:
            if adjacent_location not in game.robots.iterkeys():
                # Not in love with this implementation.  What about getting less dangerous locations?
                if len(self.__get_adjacent_enemies(game, adjacent_location)) <= \
                    max_adjacent_enemy_count:
                    friendly_adjacent_locations.append(adjacent_location)

        return friendly_adjacent_locations

    def __get_weakest_enemy(self, game, neighborhood = None):
        if neighborhood is not None:
            neighborhood_enemies = {}
            min_location = neighborhood[0]
            max_location = neighborhood[1]

            for location, robot in game.robots.iteritems():
                if robot.player_id != self.player_id:
                    if location[0] >= min_location[0] and location[0] <= max_location[0] \
                        and location[1] >= min_location[1] and location[1] <= max_location[1]:
                        neighborhood_enemies[location] = robot
            
            if len(neighborhood_enemies) > 0:
                sorted_enemies = sorted(neighborhood_enemies.iteritems(), key=lambda x: x[1].hp)

                return sorted_enemies[0]
        else:
            enemies = {}

            for location, robot in game.robots.iteritems():
                if robot.player_id != self.player_id:
                    enemies[location] = robot

            if len(enemies) > 0:
                sorted_enemies = sorted(enemies.iteritems(), key=lambda x: x[1].hp)

                return sorted_enemies[0]

    # Todo: Get a better name than neighborhood_offset.  Or just make this better in general.
    def __get_neighborhood(self, location, neighborhood_offset):
        location_x = location[0]
        location_y = location[1]
        x_min = location_x - neighborhood_offset
        x_max = location_x + neighborhood_offset
        y_min = location_y - neighborhood_offset
        y_max = location_y + neighborhood_offset

        return ((x_min, y_min), (x_max, y_max))
