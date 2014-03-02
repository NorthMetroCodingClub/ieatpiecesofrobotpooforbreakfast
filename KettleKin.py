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
        # Need to have half health or less for opportunistic suicide.  Can change this.
        self._opp_suicide_hp = 25
        self._opp_suicide_enemy_count = 4
        # We can add more probabilities if we end up with more roles.
        self._ranger_probability = 0.2
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

        adjacent_enemies = []

        for location, robot in game.robots.iteritems():
            if robot.player_id != self.player_id:
                # Should we use rg.settings.attack_range instead of hardcoding a value of 1 here?
                if rg.dist(location, self.location) <= 1:
                    adjacent_enemies.append((location, robot))
 
        # Enemies, sire!
        if len(adjacent_enemies) > 0:
            # 1. Commit desperate suicide - if we're on our last leg.
            # Todo - check how many turns are left and if suicide will actually 
            # take out any enemy robots.  We don't want to sacrifice one of our
            # dudes near the end of the game if it won't reduce the number of enemies
            # by at least one.
            if self.hp <= self._suicide_hp:
                return [self._act_suicide, self.location]

            # 2. Commit opportunistic suicide - if we're surrounded by a bunch of baddies.
            if len(adjacent_enemies) >= self._opp_suicide_enemy_count and \
                self.hp <= self._opp_suicide_hp:
                return [self._act_suicide, self.location]
            
            # 3. Attack!!
            # Sort array on robot HP to attack weakest enemies first.
            # We want to dispatch dudes on their last leg.
            sorted_enemies = sorted(adjacent_enemies, key=lambda enemy: enemy[1].hp)

            return [self._act_attack, sorted_enemies[0][0]]

        # 4. Move it!
        if self.robot_id in self._grunts.iterkeys():
            next_location = rg.toward(self.location, self._grunts[int(self.robot_id)])

            for location, robot in game.robots.iteritems():
                if robot.player_id == self.player_id and robot.location == next_location:
                    return [self._act_guard, self.location]

            return [self._act_move, next_location]
        # Could explicitly check for rangers here, but what if some robots are unaccounted for?
        # Shouldn't happen if i had any talent as a programmer...
        # Anyway, I'd rather they do something than just stand around with their metallic thumbs up their asses.
        else:
            # Being dumb right now - just moving to a random location.  Can make this smarter.
            valid_adjacent_locations = rg.locs_around(self.location, 
                filter_out=('invalid', 'obstacle', 'spawn'))
            friendly_adjacent_locations = []

            for adjacent_location in valid_adjacent_locations:
                for location, robot in game.robots.iteritems():
                    if location == adjacent_location and \
                        robot.player_id != self.player_id:

                        break
                    else:
                        friendly_adjacent_locations.append(adjacent_location)

                        break

            location_count = len(friendly_adjacent_locations)

            if (location_count > 0):
                random_index = random.randint(0, location_count) - 1
                # We could very well be trying to move into a location where there is already a friendly,
                # so might want to refine this.
                next_location = friendly_adjacent_locations[random_index]

                return [self._act_move, next_location]

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

        #Todo: Clean up deceased robots from roles.