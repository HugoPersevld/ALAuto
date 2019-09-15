import sys
import argparse
from modules.combat import CombatModule
from modules.commission import CommissionModule
from modules.mission import MissionModule
from modules.retirement import RetirementModule
from datetime import datetime, timedelta
from util.adb import Adb
from util.config import Config
from util.logger import Logger
from util.stats import Stats
from util.utils import Utils, Region


class ALAuto(object):
    modules = {
        'combat': None,
        'commissions': None,
        'missions': None,
        'retirement': None
    }

    def __init__(self, config):
        """Initializes the primary azurlane-auto instance with the passed in
        Config instance; creates the Stats instance and resets scheduled sleep
        timers.

        Args:
            config (Config): azurlane-auto Config instance
        """
        self.config = config
        self.stats = Stats(config)
        if self.config.combat['enabled']:
            self.modules['combat'] = CombatModule(self.config, self.stats)
        if self.config.commissions['enabled']:
            self.modules['commissions'] = CommissionModule(self.config, self.stats)
        if self.config.missions['enabled']:
            self.modules['missions'] = MissionModule(self.config, self.stats)
        if self.config.retirement['enabled']:
            self.modules['retirement'] = RetirementModule(self.config, self.stats)
        self.print_stats_check = True
        self.next_combat = datetime.now()

    def run_combat_cycle(self):
        """Method to run the combat cycle.
        """
        if self.modules['combat']:
            if self.modules['combat'].combat_logic_wrapper() == 2:
                self.next_combat = datetime.now() + timedelta(hours=1)
                #Logger.log_warning("Worked?")
            self.print_stats_check = True

    def run_commission_cycle(self):
        """Method to run the expedition cycle.
        """
        if self.modules['commissions']:
            if self.modules['commissions'].commission_logic_wrapper():
                self.print_stats_check = True

    def run_mission_cycle(self):
        """Method to run the mission cycle
        """
        if self.modules['missions']:
            if self.modules['missions'].mission_logic_wrapper():
                self.print_stats_check = True

    def run_retirement_cycle(self):
        """Method to run the retirement cycle
        """
        if self.modules['retirement']:
            if self.modules['retirement'].retirement_logic_wrapper():
                self.print_stats_check = True

    def print_cycle_stats(self):
        """Method to print the cycle stats"
        """
        if self.print_stats_check:
            self.stats.print_stats()
        self.print_stats_check = False

# check run-time args
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config',
                    metavar=('CONFIG_FILE'),
                    help='Use the specified configuration file instead ' +
                         'of the default config.ini')
parser.add_argument('-d', '--debug', nargs=2,
                    metavar=('IMAGE_FILE', 'SIMILARITY'),
                    help='Finds the specified image on the screen at ' +
                         'the specified similarity')
parser.add_argument('--copyright',)
args = parser.parse_args()

# check args, and if none provided, load default config
if args and args.config:
    config = Config(args.config)
else:
    config = Config('config.ini')

script = ALAuto(config)

Adb.service = config.network['service']
adb = Adb()
if adb.init():
    Logger.log_msg('Sucessfully connected to the service.')
else:
    Logger.log_error('Unable to connect to the service.')
    sys.exit()

while True:
    Utils.update_screen()
    
    # temporal solution to event alerts
    if Utils.find("map_hard_mode") or not Utils.find("menu_battle"):
        Utils.touch_randomly(Region(54, 57, 67, 67))
        continue
    if script.modules['commissions'] and Utils.find("commission_indicator"):
        script.run_commission_cycle()
        script.print_cycle_stats()
        continue
    if script.modules['missions'] and Utils.find("mission_indicator"):
        script.run_mission_cycle()
        continue
    if script.modules['combat'] and script.next_combat < datetime.now():
        script.run_combat_cycle()
        script.print_cycle_stats()
    if script.modules['retirement']:
        script.run_retirement_cycle()
        continue
    else:
        Logger.log_msg("Nothing to do, sleeping.")
        Utils.script_sleep(60)
        continue