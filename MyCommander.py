__author__ = 'Johann Jungbauer'
__version__ = "0.2"

import random

from api.commander import Commander
from api.gameinfo import MatchCombatEvent
from api.gameinfo import BotInfo
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

        self.respawnTime = self.game.match.timeToNextRespawn


    def tick(self):
        if self.enemiesSeen() == False and self.game.match.timeToNextRespawn > 10:
            if self.countDeadEnemies() == len(self.game.enemyTeam.members):
                self.rushMode()
            else:
                self.normalMode()
        else:
            self.normalMode()



    def normalMode(self):
        if self.attacker and self.attacker.health <= 0:
            # the attacker is dead we'll pick another when available
            self.attacker = None

        if self.defender and (self.defender.health <= 0 or self.defender.flag):
            # the defender is dead we'll pick another when available
            self.defender = None

        for bot in self.game.bots_available:
            if (self.defender == None or self.defender == bot) and not bot.flag:
                self.defender = bot

                self.defenderLogic()

            elif self.attacker == None or self.attacker == bot or bot.flag:
                    # Our attacking bot
                    self.attacker = bot
                    self.attackerLogic()
            else:
                # All our other (random) bots

                # pick a random position in the level to move to
                halfBox = 0.4 * min(self.level.width, self.level.height) * Vector2(1, 1)

                target = self.level.findRandomFreePositionInBox((self.middle + halfBox, self.middle - halfBox))

                # issue the order
                if target:
                    self.issue(commands.Attack, bot, target, description = 'random patrol')

    def rushMode(self):
        for bot in self.game.bots_available:
            if bot == self.defender:
                #print('%s is defender' % bot.name)
                self.defenderLogic()
            elif bot.flag:
                self.issue(commands.Charge, bot, self.game.team.flagScoreLocation, description = 'running home')
            else:
                self.issue(commands.Charge, bot, self.game.enemyTeam.flag.position, description = 'RUSH enemy flag')

    def getFlankingPosition(self, bot, target):
        flanks = [target + f * 16.0 for f in [self.left, self.right]]
        options = map(lambda f: self.level.findNearestFreePosition(f), flanks)
        return sorted(options, key = lambda p: (bot.position - p).length())[0]

    def attackerLogic(self):
        if self.attacker.flag:
            # Tell the flag carrier to run home!
            target = self.game.team.flagScoreLocation
            self.issue(commands.Charge, self.attacker, target, description = 'running home')
        else:
            target = self.game.enemyTeam.flag.position
            flank = self.getFlankingPosition(self.attacker, target)
            if (target - flank).length() > (self.attacker.position - target).length():
                self.issue(commands.Attack, self.attacker, target, description = 'attack from flank', lookAt=target)
            else:
                flank = self.level.findNearestFreePosition(flank)
                self.issue(commands.Move, self.attacker, flank, description = 'running to flank')

    def defenderLogic(self):
        # Stand on a random position in a box of 4m around the flag.
        targetPosition = self.game.team.flagSpawnLocation
        targetMin = targetPosition - Vector2(2.0, 2.0)
        targetMax = targetPosition + Vector2(2.0, 2.0)
        goal = self.level.findRandomFreePositionInBox([targetMin, targetMax])

        if (goal - self.defender.position).length() > 8.0:
            self.issue(commands.Charge, self.defender, goal, description = 'running to defend')
        else:
            self.issue(commands.Defend, self.defender, (self.middle - self.defender.position), description = 'turning to defend')

    def countDeadEnemies(self):
        count =0
        for event in reversed(self.game.match.combatEvents):
            if event.time > (self.game.match.timePassed + self.game.match.timeToNextRespawn - self.respawnTime):
                if event.type == MatchCombatEvent.TYPE_KILLED:
                    if self.isInList(self.game.enemyTeam.members, lambda BotInfo: BotInfo.name == event.subject.name):
                        count += 1
            else:
                break
            """if event.type == MatchCombatEvent.TYPE_KILLED:
                if self.isInList(self.game.enemyTeam.members, lambda BotInfo: BotInfo.name == event.subject.name):
                    if event.time > (self.game.match.timePassed + self.game.match.timeToNextRespawn - self.respawnTime):
                        count += 1"""

        return count

    def enemiesSeen(self):
        for bot in self.game.bots_alive:
            if len(bot.visibleEnemies) > 0:
                for enemy in bot.visibleEnemies:
                    if enemy.health > 0:
                        return True

        return False


    def countSeenEnemies(self):
        #TODO This count doesn't actually work
        count = 0
        for enemy in self.game.enemyTeam.members:
            if enemy.health > 0:
                count += 1

        return count

    def isInList(self, list, filter):
        for x in list:
            if filter(x):
                return True
        return False

    def isEnemy(self, list, name):
        for x in list:
            if x.name == name:
                return True
        return False

#TODO remove this before submission
class DummyCommander(Commander):

    def tick(self):
        pass
