__author__ = 'Johann Jungbauer'
__version__ = "0.1"

import random

from api.commander import Commander
from api import commands
from api.vector2 import Vector2


def contains(area, position):
    start, finish = area
    return position.x >= start.x and position.y >= start.y and position.x <= finish.x and position.y <= finish.y

class JJCommander(Commander):
    """Modified from original Balanced Commander example
        - flag carrier charges home instead of just moving home
        - The lead attacker now has a supporter paired with it"""

    def initialize(self):
        self.attacker = None
        self.defender = None
        self.verbose = True

        # Calculate flag positions and store the middle.
        ours = self.game.team.flag.position
        theirs = self.game.enemyTeam.flag.position
        self.middle = (theirs + ours) / 2.0

        # Now figure out the flaking directions, assumed perpendicular.
        d = (ours - theirs)
        self.left = Vector2(-d.y, d.x).normalized()
        self.right = Vector2(d.y, -d.x).normalized()
        self.front = Vector2(d.x, d.y).normalized()


    # Add the tick function, called each update
    # This is where you can do any logic and issue new orders.
    def tick(self):

        if self.attacker and self.attacker.health <= 0:
            # the attacker is dead we'll pick another when available
            self.attacker = None

        if self.defender and (self.defender.health <= 0 or self.defender.flag):
            # the defender is dead we'll pick another when available
            self.defender = None

        # In this example we loop through all living bots without orders (self.game.bots_available)
        # All other bots will wander randomly
        for bot in self.game.bots_available:
            if (self.defender == None or self.defender == bot) and not bot.flag:
                self.defender = bot

                # Stand on a random position in a box of 4m around the flag.
                targetPosition = self.game.team.flagScoreLocation
                targetMin = targetPosition - Vector2(2.0, 2.0)
                targetMax = targetPosition + Vector2(2.0, 2.0)
                goal = self.level.findRandomFreePositionInBox([targetMin, targetMax])

                if (goal - bot.position).length() > 8.0:
                    self.issue(commands.Charge, self.defender, goal, description = 'running to defend')
                else:
                    self.issue(commands.Defend, self.defender, (self.middle - bot.position), description = 'turning to defend')

            elif self.attacker == None or self.attacker == bot or bot.flag:
                # Our attacking bot
                self.attacker = bot

                if bot.flag:
                    # Tell the flag carrier to run home!
                    target = self.game.team.flagScoreLocation
                    self.issue(commands.Charge, bot, target, description = 'running home')
                else:
                    target = self.game.enemyTeam.flag.position
                    flank = self.getFlankingPosition(bot, target)
                    if (target - flank).length() > (bot.position - target).length():
                        self.issue(commands.Attack, bot, target, description = 'attack from flank', lookAt=target)
                    else:
                        flank = self.level.findNearestFreePosition(flank)
                        self.issue(commands.Move, bot, flank, description = 'running to flank')

            else:
                # All our other (random) bots

                # pick a random position in the level to move to
                halfBox = 0.4 * min(self.level.width, self.level.height) * Vector2(1, 1)

                target = self.level.findRandomFreePositionInBox((self.middle + halfBox, self.middle - halfBox))

                # issue the order
                if target:
                    self.issue(commands.Attack, bot, target, description = 'random patrol')

    def getFlankingPosition(self, bot, target):
        flanks = [target + f * 16.0 for f in [self.left, self.right]]
        options = map(lambda f: self.level.findNearestFreePosition(f), flanks)
        return sorted(options, key = lambda p: (bot.position - p).length())[0]
